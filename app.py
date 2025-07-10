import json
import logging
import os
import sys
import io

from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from database.papers_database_handler import get_paper_by_hash
from database.projectpaper_database_handler import get_papers_for_project, should_update, mark_paper_seen, \
    delete_project_rows
from database.projects_database_handler import get_project_by_id, get_queries_for_project
from database.projects_database_handler import add_new_project_to_db, get_all_projects
from llm.Agent import trigger_agent_show_thoughts
from pypdf import PdfReader

from pubsub.pubsub_main import update_newsletter_papers
from database.projectpaper_database_handler import get_pubsub_papers_for_project
from pubsub.pubsub_params import DAYS_FOR_UPDATE

logger = logging.getLogger(__name__)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                             '..')))
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB


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
                    # todo before calling the agent delete ALL papers for the project in paperprojects_table
                    removed = delete_project_rows(project_id)
                    print(f"Deleted {removed} row(s).")
                    for response_part in trigger_agent_show_thoughts(user_description + "project ID: " + project_id):
                        yield f"data: {json.dumps({'thought': response_part['thought']})}\n\n"

                recs_basic_data = get_papers_for_project(project_id)
                recommendations = []
                for rec in recs_basic_data:
                    paper = get_paper_by_hash(rec['paper_hash'])
                    if paper is not None:
                        paper_dict = {
                            'title': paper.get("title", "N/A"),
                            'link': paper.get("landing_page_url", "#"),
                            'description': rec.get("summary", "Relevant based on user interest.")
                        }
                    else:
                        paper_dict = {
                            'title': "N/A",
                            'link': "#",
                            'description': rec.get("summary", "Relevant based on user interest.")
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


@app.route('/api/extract-pdf-text', methods=['POST'])
def extract_pdf_text():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not file.filename or not file.filename.lower().endswith('.pdf'):
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
    logger.info("Triggered api_update_newsletter")
    payload = request.get_json() or {}
    project_id = payload.get('projectId')
    if not project_id:
        return jsonify({"error": "Missing projectId"}), 400

    if not should_update(project_id, DAYS_FOR_UPDATE):
        return jsonify({"status": "Project not updated"}), 200

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
    rows = get_pubsub_papers_for_project(project_id)
    # [(hash, summary), …]
    papers = []
    for paper_hash, summary in rows:
        if mark_paper_seen(project_id, paper_hash):
            logger.info(f"Row ({project_id}, {paper_hash}) marked as seen.")
        else:
            logger.error(f"No matching row found or could not update row ({project_id}, {paper_hash}).")
        paper = get_paper_by_hash(paper_hash)
        if paper is not None:
            papers.append({
                "title": paper.get("title", "Untitled"),
                "link": paper.get("landing_page_url", "#"),
                "description": summary
            })
        else:
            papers.append({
                "title": "Untitled",
                "link": "#",
                "description": summary
            })
    return jsonify(papers), 200

# Gives front-end the project’s metadata (title, description, queries, email).
# need this on page load to fill in the header (project title/description)
# and to know which project_id to pass into the other two endpoints.


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


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=80)  # nosec B201, B104
