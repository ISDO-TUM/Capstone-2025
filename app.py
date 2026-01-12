"""
Flask web server and API entrypoint for the Capstone academic paper recommendation system.

Responsibilities:
- Exposes REST API endpoints for project management, recommendations, ratings, and newsletter
- Handles file uploads, PDF extraction, and user interactions
- Orchestrates the Stategraph agent for multi-step academic search and filtering
- Manages database and ChromaDB connections
- Provides error handling and logging for all API routes

This is the main entrypoint for running the web application and serving the frontend.
"""

import json
import logging
import os
import sys
import io
import threading
from queue import Queue, Empty

from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    Response,
    stream_with_context,
)
from pypdf import PdfReader
from llm.StategraphAgent import trigger_stategraph_agent_show_thoughts
from chroma_db.chroma_vector_db import chroma_db
from database.database_connection import connect_to_db
from database.papers_database_handler import get_paper_by_hash, insert_papers
from database.projectpaper_database_handler import (
    get_papers_for_project,
    get_pubsub_papers_for_project,
    delete_project_rows,
    should_update,
    mark_paper_seen,
)
from database.projects_database_handler import (
    add_new_project_to_db,
    get_all_projects,
    get_project_data,
    get_project_by_id,
    get_queries_for_project,
    get_user_profile_embedding,
    update_project_description,
    delete_project,
)
from llm.Embeddings import embed_papers
from llm.feedback import update_user_profile_embedding_from_rating
from llm.tools.paper_handling_tools import replace_low_rated_paper
from paper_handling.paper_handler import (
    fetch_works_multiple_queries,
    process_available_papers,
    search_and_filter_papers,
    create_paper_dict,
)
from pubsub.pubsub_main import update_newsletter_papers
from pubsub.pubsub_params import DAYS_FOR_UPDATE
from utils.status import Status
from config import (
    TEST_MODE,
    CLERK_SECRET_KEY,
    CLERK_PUBLISHABLE_KEY,
    CLERK_FRONTEND_API_URL,
    HOSTNAME,
    validate_required_env_vars,
)

# Only import Clerk if not in test mode
if not TEST_MODE:
    from clerk_backend_api import Clerk
    from clerk_backend_api.security.types import AuthenticateRequestOptions
else:
    # Mock Clerk for testing
    Clerk = None
    AuthenticateRequestOptions = None

logger = logging.getLogger(__name__)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB

# Dictionary to track background agent processing
# Key: project_id, Value: dict with 'events' (list), 'complete' (bool), 'listeners' (list of Queues)
agent_sessions = {}
agent_locks = threading.Lock()


class AgentSession:
    """Manages an agent processing session with support for multiple listeners"""
    def __init__(self):
        self.events = []  # History of all events
        self.complete = False
        self.listeners = []  # List of queues for active listeners
        self.lock = threading.Lock()
    
    def add_event(self, event):
        """Add an event and broadcast to all listeners"""
        with self.lock:
            self.events.append(event)
            for listener in self.listeners:
                listener.put(event)
    
    def mark_complete(self):
        """Mark session as complete and notify all listeners"""
        with self.lock:
            self.complete = True
            for listener in self.listeners:
                listener.put(None)  # Signal end
    
    def subscribe(self):
        """Subscribe to events, returns a queue and replays past events"""
        q = Queue()
        with self.lock:
            # Replay all past events
            for event in self.events:
                q.put(event)
            if self.complete:
                q.put(None)  # Already complete
            else:
                self.listeners.append(q)
        return q
    
    def unsubscribe(self, q):
        """Remove a listener queue"""
        with self.lock:
            if q in self.listeners:
                self.listeners.remove(q)


# Initialize Clerk only if not in test mode
if TEST_MODE:
    clerk_sdk = None
else:
    clerk_sdk = Clerk(bearer_auth=CLERK_SECRET_KEY)


@app.before_request
def authenticate_user():
    """
    Middleware to authenticate the user with Clerk and inject auth information into the request object.
    In TEST_MODE, automatically authenticates with a test user.
    """

    # Skip authentication for public endpoints
    if request.path == "/api/clerk-config":
        request.auth = None
        return

    # In test mode, bypass Clerk and set a test user
    if TEST_MODE:
        request.auth = {
            "user_id": "test_user_id",
            "username": "test_user",
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "profile_image_url": None,
        }
        return

    try:
        # Authenticate the request using Clerk
        hostname = HOSTNAME
        if hostname:
            hostname = (
                hostname.replace("http://", "").replace("https://", "").split(":")[0]
            )
            auth_options = AuthenticateRequestOptions(authorized_parties=[hostname])
        else:
            auth_options = AuthenticateRequestOptions()

        request_state = clerk_sdk.authenticate_request(request, auth_options)
        logger.info(f"Auth state - is_signed_in: {request_state.is_signed_in}")
        logger.info(f"Auth state - status: {request_state.status}")
        logger.info(f"Auth state - reason: {request_state.reason}")

        # Debug token details if available
        if hasattr(request_state, "token") and request_state.token:
            logger.info(f"Token found: {type(request_state.token)}")
            if hasattr(request_state.token, "azp"):
                logger.info(f"Token azp (authorized party): {request_state.token.azp}")

    except Exception as e:
        # Log the error and set default values for unauthenticated requests
        logger.error(f"Authentication error for {request.path}: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        request.auth = None
        return

    # Attach authentication information to the request object
    if request_state.is_signed_in:
        user_id = request_state.payload.get("sub")

        request.auth = {
            "user_id": user_id,
        }

        try:
            user_info = clerk_sdk.users.get(user_id=user_id)
            request.auth["username"] = user_info.username
            request.auth["first_name"] = user_info.first_name
            request.auth["last_name"] = user_info.last_name
            if user_info.email_addresses and len(user_info.email_addresses) > 0:
                request.auth["email"] = (
                    user_info.email_addresses[0].email_address
                    if user_info.email_addresses
                    else None
                )

            request.auth["profile_image_url"] = user_info.profile_image_url
        except Exception as e:
            logging.error(f"Error fetching user info from Clerk:\n{e}")

    else:
        logger.warning(
            f"Not signed in - status: {request_state.status}, reason: {request_state.reason}"
        )
        request.auth = None


@app.errorhandler(413)
def request_entity_too_large(error):
    """
    Handle HTTP 413 error for requests exceeding the 50MB file size limit.
    Args:
        error: The error object from Flask.
    Returns:
        Response: JSON error message and HTTP 413 status code.
    """
    logger.error(
        f"HTTP Error 413 - Request rejected. Request content length exceeds 50MB limit. Request Content Length: {request.content_length}"
    )
    return jsonify({"error": "File size exceeds maximum allowed size (50MB)"}), 413


@app.route("/")
def home():
    """
    Render the dashboard homepage or login view based on user authentication.
    Returns:
        Response: Rendered dashboard.html template or login view.
    """

    return render_template(
        "dashboard.html",
        auth=request.auth,
        showCreateProjectButton=True,
        CLERK_PUBLISHABLE_KEY=CLERK_PUBLISHABLE_KEY,
        CLERK_FRONTEND_API_URL=CLERK_FRONTEND_API_URL,
    )


@app.route("/api/clerk-config")
def clerk_config():
    """
    Get Clerk configuration for the frontend.
    Returns publishable key and frontend API URL.
    """
    return jsonify(
        {
            "publishableKey": os.getenv("CLERK_PUBLISHABLE_KEY"),
            "frontendApiUrl": os.getenv("CLERK_FRONTEND_API_URL"),
        }
    )


@app.route("/create-project")
def create_project_page():
    """
    Render the create project page.
    Returns:
        Response: Rendered create_project.html template.
    """
    if not request.auth:
        return {"error": "Not authenticated"}, 401

    return render_template(
        "create_project.html",
        auth=request.auth,
        CLERK_PUBLISHABLE_KEY=CLERK_PUBLISHABLE_KEY,
        CLERK_FRONTEND_API_URL=CLERK_FRONTEND_API_URL,
    )


@app.route("/project/<project_id>")
def project_overview_page(project_id):
    """
    Render the project overview page for a given project.
    Args:
        project_id (str): The project ID.
    Returns:
        Response: Rendered project_overview.html template.
    """
    if not request.auth:
        return render_template(
            "dashboard.html",
            auth=None,
            CLERK_PUBLISHABLE_KEY=CLERK_PUBLISHABLE_KEY,
            CLERK_FRONTEND_API_URL=CLERK_FRONTEND_API_URL,
        )

    user_id = request.auth["user_id"]
    project = get_project_by_id(user_id, project_id)
    if not project:
        return {"error": "Project not found"}, 404
    if project["user_id"] != user_id:
        return {"error": "Forbidden"}, 403

    return render_template(
        "project_overview.html",
        project_id=project_id,
        auth=request.auth,
        CLERK_PUBLISHABLE_KEY=CLERK_PUBLISHABLE_KEY,
        CLERK_FRONTEND_API_URL=CLERK_FRONTEND_API_URL,
    )


@app.route("/api/projects", methods=["POST"])
def api_create_project():
    """
    Create a new project for the signed-in user with the given title and description.
    Returns:
        Response: JSON with new projectId or error message.
    """
    if not request.auth:
        return {"error": "Not authenticated"}, 401

    user_id = request.auth["user_id"]
    data = request.get_json() or {}
    title = data.get("title")
    desc = data.get("description")
    if not title or not desc:
        return jsonify({"error": "Missing title or description"}), 400
    project_id = add_new_project_to_db(user_id, title, desc)
    return jsonify({"projectId": project_id}), 201


@app.route("/api/getProjects", methods=["GET"])
def get_projects():
    """
    Get all projects owned by the current user with project_id and metadata.
    Returns:
        Response: JSON with all projects and their metadata.
    """
    """Get all projects with project_id and metadata."""

    if not request.auth:
        return {"error": "Not authenticated"}, 401

    user_id = request.auth["user_id"]
    projects = get_all_projects(user_id)
    complete_projects = []
    for project in projects:
        if project is None:
            continue
        project["tags"] = []
        # Use the real creation_date from the DB, format as string for frontend
        if "creation_date" in project and project["creation_date"]:
            project["date"] = str(project["creation_date"])
        else:
            project["date"] = "Unknown"
        complete_projects.append(project)
    try:
        return jsonify({"success": True, "projects": complete_projects})
    except Exception as e:
        logger.error(f"Error getting projects: {e}")
        return jsonify({"error": f"Failed to get projects: {str(e)}"}), 500


@app.route("/api/recommendations", methods=["POST"])
def get_recommendations():
    """
    Get recommendations for a project. Streams agent thoughts and recommendations to the frontend.
    Agent processing runs in background thread to continue even if client disconnects.
    Supports reconnecting to an in-progress session.
    Returns:
        Response: Server-sent event stream with recommendations or agent thoughts.
    """

    if not request.auth:
        return {"error": "Not authenticated"}, 401

    print("Attempting to get recommendations")
    try:
        user_id = request.auth["user_id"]
        data = request.get_json()
        if not data or "projectId" not in data:
            print(f"Failed getting recs with data: {data}")
            return jsonify({"error": "Missing project_id"}), 400

        update_recommendations = data.get("update_recommendations", False)
        project = get_project_by_id(user_id, data["projectId"])
        if not project:
            return jsonify({"error": "Project not found"}), 404
        user_description, project_id = project["description"], project["project_id"]

        # Check if there's an existing agent session for this project
        with agent_locks:
            existing_session = agent_sessions.get(project_id)
        
        # If agent is already processing and we're not forcing update, connect to existing session
        if existing_session is not None and not update_recommendations:
            logger.info(f"Reconnecting to existing agent session for project {project_id}")
            listener_queue = existing_session.subscribe()
            
            def generate_reconnect():
                """Reconnect to existing agent stream with event replay"""
                try:
                    while True:
                        try:
                            event = listener_queue.get(timeout=1.0)
                            if event is None:  # End signal
                                break
                            yield f"data: {json.dumps(event)}\n\n"
                        except Empty:
                            yield f": keepalive\n\n"
                            continue
                except GeneratorExit:
                    logger.info(f"Client disconnected from reconnected stream for project {project_id}")
                finally:
                    existing_session.unsubscribe(listener_queue)
            
            return Response(stream_with_context(generate_reconnect()), mimetype="text/event-stream")

        # If NOT updating recommendations and no agent is processing, fetch from database
        if not update_recommendations:
            def generate_existing():
                """Immediately return existing recommendations from database"""
                try:
                    recs_basic_data = get_papers_for_project(project_id)
                    logger.info(f"Returning {len(recs_basic_data)} existing papers from database.")
                    recommendations = []
                    for rec in recs_basic_data:
                        paper = get_paper_by_hash(rec["paper_hash"])
                        if paper is not None:
                            paper_dict = create_paper_dict(
                                paper,
                                rec.get("summary", "Relevant based on user interest."),
                                rec.get("is_replacement", False),
                            )
                        else:
                            paper_dict = {
                                "title": "N/A",
                                "link": "#",
                                "description": "Relevant based on user interest.",
                                "hash": "N/A",
                                "is_replacement": False,
                            }
                        recommendations.append(paper_dict)
                    yield f"data: {json.dumps({'recommendations': recommendations})}\n\n"
                except Exception as e:
                    logger.error(f"Error fetching existing recommendations: {e}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            return Response(stream_with_context(generate_existing()), mimetype="text/event-stream")

        # Create new agent session for updating recommendations
        session = AgentSession()
        with agent_locks:
            agent_sessions[project_id] = session

        def process_agent_in_background():
            """Run agent processing in background thread"""
            try:
                removed = delete_project_rows(project_id)
                print(f"Deleted {removed} row(s).")
                
                for response_part in trigger_stategraph_agent_show_thoughts(
                    user_description + "project ID: " + project_id
                ):
                    logger.info(f"Getting agent response: {response_part}")
                    if response_part["is_final"]:
                        try:
                            llm_response_content = response_part["final_content"]
                            response_data = json.loads(llm_response_content)

                            # Check if this is an out-of-scope response
                            if response_data.get("type") == "out_of_scope":
                                logger.info("Agent detected out of scope query")
                                session.add_event({"out_of_scope": response_data})
                                session.mark_complete()
                                return

                            elif response_data.get("type") == "no_results":
                                logger.info("Agent couldn't find any results")
                                session.add_event({"no_results": response_data})
                                session.mark_complete()
                                return

                        except json.JSONDecodeError:
                            print(f"Failed to parse LLM response: {llm_response_content}")
                            session.add_event({"error": "Failed to parse recommendations from LLM."})
                            session.mark_complete()
                            return
                    else:
                        session.add_event({"thought": response_part["thought"]})
                
                # Fetch and send recommendations after agent completes
                recs_basic_data = get_papers_for_project(project_id)
                logger.info(f"Sending {len(recs_basic_data)} papers to the frontend.")
                recommendations = []
                for rec in recs_basic_data:
                    paper = get_paper_by_hash(rec["paper_hash"])
                    if paper is not None:
                        paper_dict = create_paper_dict(
                            paper,
                            rec.get("summary", "Relevant based on user interest."),
                            rec.get("is_replacement", False),
                        )
                    else:
                        paper_dict = {
                            "title": "N/A",
                            "link": "#",
                            "description": "Relevant based on user interest.",
                            "hash": "N/A",
                            "is_replacement": False,
                        }
                    recommendations.append(paper_dict)
                session.add_event({"recommendations": recommendations})
                session.mark_complete()
                
            except Exception as e:
                logger.error(f"Error in background agent processing: {e}")
                session.add_event({"error": f"An internal error occurred: {str(e)}"})
                session.mark_complete()
            finally:
                # Clean up session after a delay to allow reconnections
                def cleanup():
                    import time
                    time.sleep(60)  # Keep session for 60 seconds after completion
                    with agent_locks:
                        if project_id in agent_sessions:
                            del agent_sessions[project_id]
                            logger.info(f"Cleaned up agent session for project {project_id}")
                
                threading.Thread(target=cleanup, daemon=True).start()

        # Start background processing
        thread = threading.Thread(target=process_agent_in_background, daemon=True)
        thread.start()

        # Subscribe to the session
        listener_queue = session.subscribe()

        def generate():
            """Stream events from the session to the client"""
            try:
                while True:
                    try:
                        event = listener_queue.get(timeout=1.0)
                        if event is None:  # End signal
                            break
                        yield f"data: {json.dumps(event)}\n\n"
                    except Empty:
                        yield f": keepalive\n\n"
                        continue
            except GeneratorExit:
                logger.info(f"Client disconnected from project {project_id} stream, but agent continues processing")
            finally:
                session.unsubscribe(listener_queue)

        return Response(stream_with_context(generate()), mimetype="text/event-stream")

    except Exception as e:
        logger.error(f"Error in /api/recommendations: {e}")
        return jsonify({"error": f"Failed to get recommendations: {str(e)}"}), 500


@app.route("/api/extract-pdf-text", methods=["POST"])
def extract_pdf_text():
    """
    Extract text from an uploaded PDF file.
    Returns:
        Response: JSON with extracted text or error message.
    """
    if not request.auth:
        return jsonify({"error": "Unauthorized"}), 401

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "File must be a PDF"}), 400

    try:
        pdf_reader = PdfReader(io.BytesIO(file.read()))

        text_content = ""
        for page in pdf_reader.pages:
            text_content += page.extract_text() + "\n"

        text_content = " ".join(text_content.split())

        if not text_content.strip():
            return jsonify({"error": "Could not extract text from PDF"}), 400

        formatted_text = f"User provided this paper: \n{text_content}"
        return jsonify({"success": True, "extracted_text": formatted_text})

    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        return jsonify({"error": f"Failed to process PDF: {str(e)}"}), 500


# Triggers server-side logic (update_newsletter_papers) to fetch new papers, run agent, and update newsletter/seen flags in database.
# call this from front-end to “refresh” which papers should be marked for the newsletter.


@app.route("/api/pubsub/update_newsletter_papers", methods=["POST"])
def api_update_newsletter():
    """
    Trigger update of newsletter papers for a project using the agent and update newsletter/seen flags in the database.
    Returns:
        Response: JSON status message.
    """
    if not request.auth:
        return jsonify({"error": "Unauthorized"}), 401

    logger.info("Triggered api_update_newsletter")
    payload = request.get_json() or {}
    project_id = payload.get("projectId")
    if not project_id:
        return jsonify({"error": "Missing projectId"}), 400

    if not should_update(project_id, DAYS_FOR_UPDATE):
        return jsonify({"status": "Project not updated"}), 200

    # first read queries
    user_id = request.auth["user_id"]
    queries = get_queries_for_project(user_id, project_id)
    if not queries:
        # no queries: return ok but without doing anything
        return jsonify({"status": "no-queries"}), 200

    try:
        update_newsletter_papers(project_id)
        return jsonify({"status": "ok"}), 200
    except ValueError as e:
        msg = str(e)
        # Chroma sends ValueError with this text when there are no IDs
        if "Expected IDs to be a non-empty list" in msg:
            # return 200 so frontend continues and reads get_newsletter_papers
            return jsonify({"status": "no-results"}), 200
        # if there is another ValueError, we make it fall down
        return jsonify({"error": msg}), 500
    except Exception as e:
        # rest of exceptions
        logger.exception("Error to update newsletters")
        return jsonify({"error": str(e)}), 500


# Returns current set of (paper_hash, summary) tuples that are both newsletter = TRUE and seen = FALSE for a given project.
# JS then looks up the full paper details via get_paper_by_hash and renders them.
@app.route("/api/pubsub/get_newsletter_papers", methods=["GET"])
def api_get_newsletter():
    """
    Get the current set of newsletter papers for a project.
    Returns:
        Response: JSON list of newsletter papers with metadata.
    """
    if not request.auth:
        return jsonify({"error": "Unauthorized"}), 401

    project_id = request.args.get("projectId") or request.args.get("project_id")
    if not project_id:
        return jsonify({"error": "Missing projectId"}), 400

    rows = get_pubsub_papers_for_project(project_id)  # [(hash, summary), …]
    papers = []
    for paper_hash, summary in rows:
        if mark_paper_seen(project_id, paper_hash):
            logger.info(f"Row ({project_id}, {paper_hash}) marked as seen.")
        else:
            logger.error(
                f"No matching row found or could not update row ({project_id}, {paper_hash})."
            )
        paper = get_paper_by_hash(paper_hash)
        if paper is not None:
            papers.append(
                {
                    "title": paper.get("title", "Untitled"),
                    "link": paper.get("landing_page_url", "#"),
                    "description": summary,
                }
            )
        else:
            papers.append(
                {"title": "Paper not found", "link": "#", "description": summary}
            )
    return jsonify(papers)


# Gives front-end the project’s metadata (title, description, queries, email).
# need this on page load to fill in the header (project title/description)
# and to know which project_id to pass into the other two endpoints.


@app.route("/api/rate_paper", methods=["POST"])
def rate_paper():
    """
    Rate a paper, update the user embedding, and replace it if it's low rated.
    Returns:
        Response: JSON status message and replacement info if applicable.
    """
    if not request.auth:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = request.auth["user_id"]
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    paper_hash = data.get("paper_hash")
    project_id = data.get("project_id")
    rating = data.get("rating")

    print(
        f"Rating - paper_hash: {paper_hash}, project_id: {project_id}, rating: {rating}"
    )

    if (
        not paper_hash
        or not project_id
        or not isinstance(rating, int)
        or rating < 1
        or rating > 5
    ):
        return jsonify(
            {"status": "error", "message": "Invalid paper_hash, project_id, or rating"}
        ), 400

    conn = connect_to_db()
    if not conn:
        return jsonify(
            {"status": "error", "message": "Database connection failed"}
        ), 500

    try:
        cur = conn.cursor()
        cur.execute(
            """
                    UPDATE paperprojects_table
                    SET rating = %s
                    WHERE paper_hash = %s AND project_id = %s;
                """,
            (rating, paper_hash, project_id),
        )
        conn.commit()

        if cur.rowcount == 0:
            return jsonify({"status": "error", "message": "Paper not found"}), 404

        # Update user profile embedding based on the rating
        update_user_profile_embedding_from_rating(
            user_id, project_id, paper_hash, rating
        )

        # If rating is low (1-2 stars), automatically replace the paper
        replacement_result = None
        if rating <= 2:
            try:
                print(
                    f"Low rating ({rating}) detected, attempting to replace paper {paper_hash}"
                )

                # Call the replacement tool directly
                result = replace_low_rated_paper.invoke(
                    {"project_id": project_id, "low_rated_paper_hash": paper_hash}
                )

                # Parse the JSON result
                replacement_result = json.loads(result)
                print(f"Replacement result: {replacement_result}")

            except Exception as replacement_error:
                logger.warning(
                    f"Failed to replace low-rated paper: {replacement_error}"
                )
                replacement_result = None

        # Return response with replacement info
        response_data = {"status": "success", "message": "Rating saved"}
        if replacement_result and replacement_result.get("status") == "success":
            response_data["replacement"] = replacement_result

        return jsonify(response_data)
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating rating: {e}")
        return jsonify({"status": "error", "message": f"Database error: {e}"}), 500
    finally:
        cur.close()
        conn.close()


@app.route("/api/project/<project_id>")
def api_get_project(project_id):
    """
    Get project metadata for a given project_id.
    Args:
        project_id (str): The project ID.
    Returns:
        Response: JSON with project metadata or error message.
    """
    if not request.auth:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = request.auth["user_id"]
    proj = get_project_by_id(user_id, project_id)
    if not proj:
        return jsonify({"error": "Project not found"}), 404
    return jsonify(
        {
            "projectId": proj["project_id"],
            "title": proj["title"],
            "description": proj["description"],
            "queries": proj["queries"],
            "email": proj["email"],
            # etc
        }
    ), 200


# Endpoint to update project prompt/description


@app.route("/api/project/<project_id>/update_prompt", methods=["POST"])
def api_update_project_prompt(project_id):
    """
    Update the project prompt/description for a given project_id.
    Args:
        project_id (str): The project ID.
    Returns:
        Response: JSON with updated description or error message.
    """
    if not request.auth:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = request.auth["user_id"]
    data = request.get_json() or {}
    new_prompt = data.get("prompt")
    if not new_prompt:
        return jsonify({"error": "Missing prompt"}), 400
    status = update_project_description(user_id, project_id, new_prompt)
    if status == Status.SUCCESS:
        # Fetch updated project to return new description
        project = get_project_by_id(user_id, project_id)
        return jsonify(
            {"success": True, "description": project.get("description", new_prompt)}
        )
    else:
        return jsonify({"error": "Failed to update project prompt"}), 500


@app.route("/api/project/<project_id>", methods=["DELETE"])
def api_delete_project(project_id):
    """
    Delete a project and all its associated data.
    Args:
        project_id (str): The project ID to delete.
    Returns:
        Response: JSON with success status or error message.
    """
    if not request.auth:
        return jsonify({"error": "Unauthorized"}), 401
    user_id = request.auth["user_id"]

    status = delete_project(user_id, project_id)
    if status == Status.SUCCESS:
        return jsonify({"success": True, "message": "Project deleted successfully"})
    else:
        return jsonify({"error": "Failed to delete project"}), 500


@app.route("/api/load_more_papers", methods=["POST"])
def load_more_papers():
    """
    Load more paper recommendations for the user, streaming results as they are found.
    Returns:
        Response: Server-sent event stream with more recommendations or error message.
    """
    if not request.auth:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = request.auth["user_id"]
        data = request.get_json()
        project_id = data.get("project_id") if data else None
        if not project_id:
            return jsonify({"error": "Missing project_id"}), 400

        project = get_project_data(user_id, project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404

        def generate():
            try:
                # Retrieve the latest user profile embedding
                user_embedding = get_user_profile_embedding(user_id, project_id)
                if not user_embedding:
                    yield f"data: {json.dumps({'error': 'No user profile embedding found'})}\n\n"
                    return

                # Retrieve already shown papers and project description
                shown_hashes = {
                    p.get("paper_hash") for p in get_papers_for_project(project_id)
                }
                description = project.get("description", "No description")

                def yield_recommendations(similarity):
                    papers = search_and_filter_papers(
                        chroma_db,
                        user_embedding,
                        shown_hashes,
                        min_similarity=similarity,
                    )
                    if papers:
                        recs = process_available_papers(papers, project_id, description)
                        if len(recs) == 10:
                            yield f"data: {json.dumps({'recommendations': recs})}\n\n"
                            return True
                    return False

                # First try finding more papers in Chroma
                if (yield from yield_recommendations(-0.4)):
                    return

                # Next try fetching more papers with OpenAlex
                queries = get_queries_for_project(user_id, project_id)
                if not queries:
                    yield f"data: {json.dumps({'error': 'No search queries found for this project'})}\n\n"
                    return

                for count in [10, 15, 20, 25]:
                    yield f"data: {json.dumps({'thought': f'Fetching {count} papers per query from OpenAlex...'})}\n\n"
                    fetched, status = fetch_works_multiple_queries(
                        queries, per_page=count
                    )
                    if status != Status.SUCCESS or not fetched:
                        continue

                    _, deduped = insert_papers(fetched)
                    embeddings = [
                        {
                            "embedding": embed_papers(p["title"], p["abstract"]),
                            "hash": p["hash"],
                        }
                        for p in deduped
                        if embed_papers(p["title"], p["abstract"])
                    ]

                    if embeddings:
                        chroma_db.store_embeddings(embeddings)
                        if (yield from yield_recommendations(-0.4)):
                            return

                # Last resort
                if (yield from yield_recommendations(-0.4)):
                    return

                yield f"data: {json.dumps({'error': 'No more papers available to show.'})}\n\n"

            except Exception as e:
                logger.error(f"Error in generator: {e}")
                yield f"data: {json.dumps({'error': f'Internal error: {str(e)}'})}\n\n"

        return Response(stream_with_context(generate()), mimetype="text/event-stream")

    except Exception as e:
        logger.error(f"Error in /load_more_papers: {e}")
        return jsonify({"error": f"Failed to load more papers: {str(e)}"}), 500


if __name__ == "__main__":
    # Validate required environment variables
    validate_required_env_vars()

    app.run(host="0.0.0.0", debug=True, port=80)  # nosec B201, B104
