import io
import json
import logging
import os
import sys

from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from pypdf import PdfReader

from chroma_db.chroma_vector_db import chroma_db
from database.database_connection import connect_to_db
from database.papers_database_handler import get_paper_by_hash, insert_papers
from database.projectpaper_database_handler import get_papers_for_project, get_pubsub_papers_for_project
from database.projects_database_handler import add_new_project_to_db, get_all_projects, get_project_data, get_project_by_id, get_queries_for_project, get_user_profile_embedding
from llm.Agent import trigger_agent_show_thoughts
from llm.Embeddings import embed_papers
from llm.feedback import update_user_profile_embedding_from_rating
from llm.tools.paper_handling_tools import replace_low_rated_paper
from paper_handling.paper_handler import fetch_works_multiple_queries, process_available_papers, search_and_filter_papers
from pubsub.pubsub_main import update_newsletter_papers
from utils.status import Status

logger = logging.getLogger(__name__)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                             '..')))
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

MOCK_NEWSLETTER = [
    {
        "title": "Weekly AI Research Digest - Healthcare Focus",
        "link": "https://arxiv.org/abs/2301.22222",
        "description": "Latest breakthroughs in AI applications for healthcare diagnostics."
    },
    {
        "title": "Emerging Trends in Medical AI Ethics",
        "link": "https://arxiv.org/abs/2301.33333",
        "description": "Discussion on ethical considerations in medical AI deployment."
    },
    {
        "title": "Real-world Clinical AI Implementation Case Studies",
        "link": "https://arxiv.org/abs/2301.44444",
        "description": "Practical insights from successful clinical AI integrations."
    }
]


@app.errorhandler(413)
def request_entity_too_large(error):
    logger.error(f"HTTP Error 413 - Request rejected. Request content length exceeds 50MB limit. Request Content Length: {request.content_length}")
    return jsonify({
        "error": "File size exceeds maximum allowed size (50MB)"
    }), 413


@app.route('/')
def home():
    return render_template('dashboard.html')


@app.route('/create-project')
def create_project_page():
    return render_template('create_project.html')


@app.route('/project/<project_id>')
def project_overview_page(project_id):
    return render_template('project_overview.html', project_id=project_id)


@app.route('/api/projects', methods=['POST'])
def api_create_project():
    data = request.get_json() or {}
    title = data.get('title')
    desc = data.get('description')
    if not title or not desc:
        return jsonify({"error": "Missing title or description"}), 400
    project_id = add_new_project_to_db(title, desc)
    return jsonify({"projectId": project_id}), 201


@app.route('/api/getProjects', methods=['GET'])
def get_projects():
    """Get all projects with project_id and metadata."""

    projects = get_all_projects()
    complete_projects = []
    for project in projects:
        if project is None:
            continue
        project['tags'] = []
        # Use the real creation_date from the DB, format as string for frontend
        if 'creation_date' in project and project['creation_date']:
            project['date'] = str(project['creation_date'])
        else:
            project['date'] = "Unknown"
        complete_projects.append(project)
    try:
        return jsonify({
            "success": True,
            "projects": complete_projects
        })
    except Exception as e:
        logger.error(f"Error getting projects: {e}")
        return jsonify({"error": f"Failed to get projects: {str(e)}"}), 500


@app.route('/api/recommendations', methods=['POST'])
def get_recommendations():
    print("Attempting to get recommendations")
    """Get recommendations for a project. Updated to use project_id and update_recommendations flag."""
    try:
        data = request.get_json()
        if not data or 'projectId' not in data:
            print(f"Failed getting recs with data: {data}")
            return jsonify({"error": "Missing project_id"}), 400

        # project_id validated above but currently unused in mock implementation
        update_recommendations = data.get('update_recommendations', False)
        project = get_project_by_id(data['projectId'])
        user_description, project_id = project['description'], project['project_id']

        def generate():
            try:
                if update_recommendations:
                    for response_part in trigger_agent_show_thoughts(user_description + "project ID: " + project_id):
                        yield f"data: {json.dumps({'thought': response_part['thought']})}\n\n"

                # todo update get_papers_for_project so that it doesnt return pubsub papers or define how the behaviour should be
                recs_basic_data = get_papers_for_project(project_id)
                recommendations = []
                for rec in recs_basic_data:
                    paper = get_paper_by_hash(rec['paper_hash'])
                    if paper is not None:
                        paper_dict = {
                            'title': paper.get("title", "N/A"),
                            'link': paper.get("landing_page_url", "#"),
                            'description': rec.get("summary", "Relevant based on user interest."),
                            'hash': rec['paper_hash'],
                            'is_replacement': rec.get('is_replacement', False)
                        }
                    else:
                        paper_dict = {
                            'title': "N/A",
                            'link': "#",
                            'description': "Relevant based on user interest.",
                            'hash': "Nan",
                            'is_replacement': False
                        }
                    recommendations.append(paper_dict)
                yield f"data: {json.dumps({'recommendations': recommendations})}\n\n"
            except Exception as e:
                logger.error(f"Error in recommendations generation: {e}")
                error_payload = json.dumps({"error": f"An internal error occurred: {str(e)}"})
                yield f"data: {error_payload}\n\n"

        return Response(stream_with_context(generate()), mimetype='text/event-stream')

    except Exception as e:
        logger.error(f"Error in /api/recommendations: {e}")
        return jsonify({"error": f"Failed to get recommendations: {str(e)}"}), 500


@app.route('/api/getNewsletter', methods=['POST'])
def get_newsletter():
    """Get newsletter/pubsub papers for a project."""
    try:
        data = request.get_json()
        if not data or 'project_id' not in data:
            return jsonify({"error": "Missing project_id"}), 400

        # project_id validated above but currently unused in mock implementation
        update_newsletter = data.get('update_newsletter', False)

        def generate():
            try:
                if update_newsletter:
                    yield f"data: {json.dumps({'thought': 'Fetching latest publications...'})}\n\n"
                    yield f"data: {json.dumps({'thought': 'Filtering relevant content...'})}\n\n"
                    yield f"data: {json.dumps({'thought': 'Preparing newsletter digest...'})}\n\n"

                yield f"data: {json.dumps({'recommendations': MOCK_NEWSLETTER})}\n\n"

            except Exception as e:
                logger.error(f"Error in newsletter generation: {e}")
                error_payload = json.dumps({"error": f"An internal error occurred: {str(e)}"})
                yield f"data: {error_payload}\n\n"

        return Response(stream_with_context(generate()), mimetype='text/event-stream')

    except Exception as e:
        logger.error(f"Error in /api/getNewsletter: {e}")
        return jsonify({"error": f"Failed to get newsletter: {str(e)}"}), 500


@app.route('/api/extract-pdf-text', methods=['POST'])
def extract_pdf_text():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.lower().endswith('.pdf'):
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
        return jsonify({
            "success": True,
            "extracted_text": formatted_text
        })

    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        return jsonify({"error": f"Failed to process PDF: {str(e)}"}), 500

# Triggers server-side logic (update_newsletter_papers) to fetch new papers, run agent, and update newsletter/seen flags in database.
# call this from front-end to “refresh” which papers should be marked for the newsletter.


@app.route('/api/pubsub/update_newsletter_papers', methods=['POST'])
def api_update_newsletter():
    payload = request.get_json() or {}
    project_id = payload.get('projectId')
    if not project_id:
        return jsonify({"error": "Missing projectId"}), 400

    # first read queries
    queries = get_queries_for_project(project_id)
    if not queries:
        # no queries: return ok but without doing anything
        return jsonify({'status': 'no-queries'}), 200

    try:
        update_newsletter_papers(project_id)
        return jsonify({'status': 'ok'}), 200
    except ValueError as e:
        msg = str(e)
        # Chroma sends ValueError with this text when there are no IDs
        if "Expected IDs to be a non-empty list" in msg:
            # return 200 so frontend continues and reads get_newsletter_papers
            return jsonify({'status': 'no-results'}), 200
        # if there is another ValueError, we make it fall down
        return jsonify({'error': msg}), 500
    except Exception as e:
        # rest of exceptions
        logger.exception("Error to update newsletters")
        return jsonify({'error': str(e)}), 500


# Returns current set of (paper_hash, summary) tuples that are both newsletter = TRUE and seen = FALSE for a given project.
# JS then looks up the full paper details via get_paper_by_hash and renders them.
@app.route('/api/pubsub/get_newsletter_papers', methods=['GET'])
def api_get_newsletter():
    project_id = request.args.get('projectId') or request.args.get('project_id')
    if not project_id:
        return jsonify({"error": "Missing projectId"}), 400

    rows = get_pubsub_papers_for_project(project_id)  # [(hash, summary), …]
    papers = []
    for paper_hash, summary in rows:
        paper = get_paper_by_hash(paper_hash)
        if paper is not None:
            papers.append({
                "title": paper.get("title", "Untitled"),
                "link": paper.get("landing_page_url", "#"),
                "description": summary
            })
        else:
            papers.append({
                "title": "Paper not found",
                "link": "#",
                "description": summary
            })
    return jsonify(papers)

# Gives front-end the project’s metadata (title, description, queries, email).
# need this on page load to fill in the header (project title/description)
# and to know which project_id to pass into the other two endpoints.


@app.route('/api/rate_paper', methods=['POST'])
def rate_paper():
    """Rate a paper, update the user embedding, and replace it if it's low rated"""
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    paper_hash = data.get("paper_hash")
    project_id = data.get("project_id")
    rating = data.get("rating")

    print(f"Rating - paper_hash: {paper_hash}, project_id: {project_id}, rating: {rating}")

    if not paper_hash or not project_id or not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({"status": "error", "message": "Invalid paper_hash, project_id, or rating"}), 400

    conn = connect_to_db()
    if not conn:
        return jsonify({"status": "error", "message": "Database connection failed"}), 500

    try:
        cur = conn.cursor()
        cur.execute("""
                    UPDATE paperprojects_table
                    SET rating = %s
                    WHERE paper_hash = %s AND project_id = %s;
                """, (rating, paper_hash, project_id))
        conn.commit()

        if cur.rowcount == 0:
            return jsonify({"status": "error", "message": "Paper not found"}), 404

        # Update user profile embedding based on the rating
        update_user_profile_embedding_from_rating(project_id, paper_hash, rating)

        # If rating is low (1-2 stars), automatically replace the paper
        replacement_result = None
        if rating <= 2:
            try:
                print(f"Low rating ({rating}) detected, attempting to replace paper {paper_hash}")

                # Call the replacement tool directly
                result = replace_low_rated_paper.invoke({
                    "project_id": project_id,
                    "low_rated_paper_hash": paper_hash
                })

                # Parse the JSON result
                replacement_result = json.loads(result)
                print(f"Replacement result: {replacement_result}")

            except Exception as replacement_error:
                logger.warning(f"Failed to replace low-rated paper: {replacement_error}")
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


@app.route('/api/project/<project_id>')
def api_get_project(project_id):
    proj = get_project_by_id(project_id)
    if not proj:
        return jsonify({"error": "Project not found"}), 404
    return jsonify({
        "projectId": proj["project_id"],
        "title": proj["title"],
        "description": proj["description"],
        "queries": proj["queries"],
        "email": proj["email"],
        # etc
    }), 200


@app.route('/api/load_more_papers', methods=['POST'])
def load_more_papers():
    """Load more paper recommendations for user."""
    try:
        data = request.get_json()
        project_id = data.get('project_id') if data else None
        if not project_id:
            return jsonify({"error": "Missing project_id"}), 400

        project = get_project_data(project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404

        def generate():
            try:
                # Retrieve the latest user profile embedding
                user_embedding = get_user_profile_embedding(project_id)
                if not user_embedding:
                    yield f"data: {json.dumps({'error': 'No user profile embedding found'})}\n\n"
                    return

                # Retrieve already shown papers and project description
                shown_hashes = {p.get('paper_hash') for p in get_papers_for_project(project_id)}
                description = project.get('description', 'No description')

                def yield_recommendations(similarity):
                    papers = search_and_filter_papers(chroma_db, user_embedding, shown_hashes, min_similarity=similarity)
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
                queries = get_queries_for_project(project_id)
                if not queries:
                    yield f"data: {json.dumps({'error': 'No search queries found for this project'})}\n\n"
                    return

                for count in [10, 15, 20, 25]:
                    yield f"data: {json.dumps({'thought': f'Fetching {count} papers per query from OpenAlex...'})}\n\n"
                    fetched, status = fetch_works_multiple_queries(queries, per_page=count)
                    if status != Status.SUCCESS or not fetched:
                        continue

                    _, deduped = insert_papers(fetched)
                    embeddings = [
                        {'embedding': embed_papers(p['title'], p['abstract']), 'hash': p['hash']}
                        for p in deduped if embed_papers(p['title'], p['abstract'])
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

        return Response(stream_with_context(generate()), mimetype='text/event-stream')

    except Exception as e:
        logger.error(f"Error in /load_more_papers: {e}")
        return jsonify({"error": f"Failed to load more papers: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=80)  # nosec B201, B104
