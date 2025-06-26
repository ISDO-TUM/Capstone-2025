import json
import logging
import os
import sys
import io

from flask import Flask, request, jsonify, render_template, Response, stream_with_context

from database.papers_database_handler import get_paper_by_hash
from database.projectpaper_database_handler import get_papers_for_project
from database.projects_database_handler import add_new_project_to_db
from llm.Agent import trigger_agent_show_thoughts
import PyPDF2

from pubsub.pubsub_main import update_newsletter_papers
from database.projectpaper_database_handler import get_pubsub_papers_for_project
from database.projects_database_handler import get_project_by_id


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


@app.route('/api/recommendations', methods=['POST'])
def get_recommendations():
    data = request.get_json()
    if not data or 'projectDescription' not in data:
        return jsonify({"error": "Missing projectDescription"}), 400

    user_description = data['projectDescription']

    # Hardcoded until frontend is updated
    project_id = add_new_project_to_db("DummyProject", user_description)

    def generate():
        try:
            for response_part in trigger_agent_show_thoughts(user_description + "project ID: " + project_id):
                if not response_part['is_final']:
                    yield f"data: {json.dumps({'thought': response_part['thought']})}\n\n"
                else:
                    try:
                        llm_response_content = response_part['final_content']
                        recs_basic_data = get_papers_for_project(project_id)
                        print(f"Recs: {recs_basic_data}")
                        recommendations = []
                        for rec in recs_basic_data:
                            paper = get_paper_by_hash(rec['paper_hash'])
                            paper_dict = {'title': paper['title'], 'link': paper['landing_page_url'],
                                          'description': rec['summary']}
                            recommendations.append(paper_dict)
                        final_recommendations = []
                        for rec in recommendations:
                            final_recommendations.append({
                                "title": rec.get("title", "N/A"),
                                "link": rec.get("link", "N/A"),
                                "description": rec.get("description", "Relevant based on user interest.")
                            })
                        print(final_recommendations)
                        yield f"data: {json.dumps({'recommendations': final_recommendations})}\n\n"
                    except json.JSONDecodeError:
                        print(f"Failed to parse LLM response: {llm_response_content}")
                        error_payload = json.dumps({"error": "Failed to parse recommendations from LLM."})
                        yield f"data: {error_payload}\n\n"
                    except Exception as e:
                        print(f"An unexpected error occurred: {e}")
                        error_payload = json.dumps({"error": f"A server error occurred: {e}"})
                        yield f"data: {error_payload}\n\n"
        except Exception as e:
            print(f"An error occurred in /api/recommendations: {e}")
            error_payload = json.dumps({"error": f"An internal error occurred: {str(e)}"})
            yield f"data: {error_payload}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')


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
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))

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

@app.route('/api/pubsub/update_newsletter_papers', methods=['POST'])
def api_update_newsletter():
    payload = request.get_json() or {}
    project_id = payload.get('projectId')
    if not project_id:
        return jsonify({"error": "Missing projectId"}), 400
    
    try:
        update_newsletter_papers(project_id)
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        logger.exception("Error to update newsletters")
        return jsonify({'error': str(e)}), 500


@app.route('/api/pubsub/get_newsletter_papers', methods=['GET'])
def api_get_newsletter():
    project_id = request.args.get('projectId')
    if not project_id:
        return jsonify({"error": "Missing projectId"}), 400

    rows = get_pubsub_papers_for_project(project_id)  # [(hash, summary), …]
    papers = []
    for paper_hash, summary in rows:
        paper = get_paper_by_hash(paper_hash)
        papers.append({
            "title":       paper.get("title", "Untitled"),
            "link":        paper.get("landing_page_url", "#"),
            "description": summary
        })
    return jsonify(papers), 200

from database.projects_database_handler import get_project_by_id  # tendrás que implementarlo

@app.route('/api/project/<project_id>')
def api_get_project(project_id):
    proj = get_project_by_id(project_id)
    if not proj:
        return jsonify({"error": "Project not found"}), 404
    return jsonify({
        "projectId": proj["project_id"],
        "title": proj["title"],
        "description": proj["description"],
        # etc
    })

#@app.route('/api/project/<project_id>')
#def api_get_project(project_id):
    #proj = get_project_by_id(project_id)
    #if not proj:
        #return jsonify({"error": "Project not found"}), 404
    #return jsonify(proj), 200

if __name__ == '__main__':

    app.run(host='0.0.0.0', debug=True, port=7500)  # nosec B201, B104
