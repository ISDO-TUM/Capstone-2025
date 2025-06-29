import json
import logging
import os
import sys
import io

from flask import Flask, request, jsonify, render_template, Response, stream_with_context

from database.papers_database_handler import get_paper_by_hash
from database.projectpaper_database_handler import get_papers_for_project
from database.projects_database_handler import get_project_by_id, get_queries_for_project
from database.projects_database_handler import add_new_project_to_db, get_project_data, get_all_projects
from llm.Agent import trigger_agent_show_thoughts
import PyPDF2

from pubsub.pubsub_main import update_newsletter_papers
from database.projectpaper_database_handler import get_pubsub_papers_for_project


logger = logging.getLogger(__name__)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                             '..')))

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

MOCK_PROJECTS = [
    {
        "project_id": "proj_001",
        "name": "AI for Drug Discovery",
        "description": "Leveraging deep learning to accelerate the identification of novel drug candidates for rare diseases.",
        "tags": ["AI", "Drug Discovery", "Deep Learning", "Healthcare"],
        "date": "2024-01-15"
    },
    {
        "project_id": "proj_002",
        "name": "Quantum Computing Algorithms",
        "description": "Developing new quantum algorithms for optimization problems in logistics.",
        "tags": ["Quantum", "Algorithms", "Optimization", "Logistics"],
        "date": "2024-01-28"
    },
    {
        "project_id": "proj_003",
        "name": "Climate Change Impact Analysis",
        "description": "Analyzing satellite data to predict the long-term effects of climate change on coastal regions.",
        "tags": ["Climate", "Satellite", "Prediction", "Environment"],
        "date": "2024-02-02"
    },
    {
        "project_id": "proj_004",
        "name": "Cancer Genomics",
        "description": "Integrating multi-omics data to identify biomarkers for early cancer detection.",
        "tags": ["Genomics", "Cancer", "Biomarkers", "Multi-omics"],
        "date": "2024-03-10"
    },
    {
        "project_id": "proj_005",
        "name": "Renewable Energy Forecasting",
        "description": "Machine learning models for predicting solar and wind energy production.",
        "tags": ["Renewable", "Energy", "Forecasting", "Machine Learning"],
        "date": "2024-02-18"
    }
]

MOCK_RECOMMENDATIONS = [
    {
        "title": "Deep Learning Applications in Medical Image Analysis",
        "link": "https://arxiv.org/abs/2301.12345",
        "description": "Comprehensive review of CNN architectures for medical imaging tasks."
    },
    {
        "title": "Transformer Models for Healthcare Data",
        "link": "https://arxiv.org/abs/2301.67890",
        "description": "Novel transformer architectures adapted for healthcare applications."
    },
    {
        "title": "Federated Learning in Clinical Research",
        "link": "https://arxiv.org/abs/2301.11111",
        "description": "Privacy-preserving machine learning approaches for clinical data."
    }
]

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
    desc  = data.get('description')
    queries = data.get('queries', [])
    if not title or not desc:
        return jsonify({ "error": "Missing title or description" }), 400
    queries_str = json.dumps(queries)
    project_id = add_new_project_to_db(title, desc, queries_str)
    return jsonify({ "projectId": project_id }), 201

@app.route('/api/getProjects', methods=['GET'])
def get_projects():
    """Get all projects with project_id and metadata."""
    # todo update database to include project creation date
    try:
        return jsonify({
            "success": True,
            "projects": get_all_projects()  # todo check that this function returns valid dicts, might need to modify it to make them have the right form
        })
    except Exception as e:
        logger.error(f"Error getting projects: {e}")
        return jsonify({"error": f"Failed to get projects: {str(e)}"}), 500


@app.route('/api/createProject', methods=['POST'])
def create_project():
    """Create a new project and return project_id."""
    try:
        data = request.get_json()
        if not data or 'title' not in data or 'prompt' not in data:
            return jsonify({"error": "Missing title or prompt"}), 400

        project_id = add_new_project_to_db(data['title'], data['prompt'])

        return jsonify({
            "success": True,
            "project_id": project_id
        })
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        return jsonify({"error": f"Failed to create project: {str(e)}"}), 500


@app.route('/api/old_recommendations', methods=['POST'])
def get_old_recommendations():
    """Original recommendations endpoint - kept for backward compatibility."""
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
                        #updates table with project_id
                        update_newsletter_papers(project_id)

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
            print(f"An error occurred in /api/old_recommendations: {e}")
            error_payload = json.dumps({"error": f"An internal error occurred: {str(e)}"})
            yield f"data: {error_payload}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')


@app.route('/api/recommendations', methods=['POST'])
def get_recommendations():
    """Get recommendations for a project. Updated to use project_id and update_recommendations flag."""
    try:
        data = request.get_json()
        if not data or 'project_id' not in data:
            return jsonify({"error": "Missing project_id"}), 400

        # project_id validated above but currently unused in mock implementation
        update_recommendations = data.get('update_recommendations', False)
        project = get_project_data(data['project_id'])  # todo check that this function returns a valid dictionary, you might need to format the output to make it usable
        user_description, project_id = project['title'], project['description']

        def generate():
            try:
                if update_recommendations:
                    for response_part in trigger_agent_show_thoughts(user_description + "project ID: " + project_id):
                        yield f"data: {json.dumps({'thought': response_part['thought']})}\n\n"

                recs_basic_data = get_papers_for_project(data['project_id'])
                recommendations = []
                for rec in recs_basic_data:
                    paper = get_paper_by_hash(rec['paper_hash'])
                    paper_dict = {
                        'title': paper.get("title", "N/A"),
                        'link': paper.get("link", "N/A"),
                        'description': paper.get("description", "Relevant based on user interest.")
                    }
                    recommendations.append(paper_dict)
                print(recommendations)  # todo check that recommendations is a valid json
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

#Triggers server-side logic (update_newsletter_papers) to fetch new papers, run agent, and update newsletter/seen flags in database.
#call this from front-end to “refresh” which papers should be marked for the newsletter.
@app.route('/api/pubsub/update_newsletter_papers', methods=['POST'])
def api_update_newsletter():
    payload = request.get_json() or {}
    project_id = payload.get('projectId')
    if not project_id:
        return jsonify({"error": "Missing projectId"}), 400
    
    #first read queries
    queries = get_queries_for_project(project_id)
    if not queries:
        #no queries: return ok but without doing anything
        return jsonify({'status': 'no-queries'}), 200

    try:
        update_newsletter_papers(project_id)
        return jsonify({'status': 'ok'}), 200
    except ValueError as e:
        msg = str(e)
        #Chroma sends ValueError with this text when there are no IDs
        if "Expected IDs to be a non-empty list" in msg:
            #return 200 so frontend continues and reads get_newsletter_papers
            return jsonify({'status': 'no-results'}), 200
        #if there is another ValueError, we make it fall down
        return jsonify({'error': msg}), 500
    except Exception as e:
        #rest of exceptions
        logger.exception("Error to update newsletters")
        return jsonify({'error': str(e)}), 500


#Returns current set of (paper_hash, summary) tuples that are both newsletter = TRUE and seen = FALSE for a given project.
#JS then looks up the full paper details via get_paper_by_hash and renders them.
@app.route('/api/pubsub/get_newsletter_papers', methods=['GET'])
def api_get_newsletter():
    project_id = request.args.get('projectId') or request.args.get('project_id')
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

#Gives front-end the project’s metadata (title, description, queries, email).
#need this on page load to fill in the header (project title/description)
#and to know which project_id to pass into the other two endpoints.
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

    app.run(host='0.0.0.0', debug=True, port=7500)  # nosec B201, B104
