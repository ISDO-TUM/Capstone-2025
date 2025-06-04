import json
import logging
import os
import sys

from flask import Flask, request, jsonify, render_template
from llm.Agent import trigger_agent
from utils.user_profile import process_user_paper

logger = logging.getLogger(__name__)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                             '..')))

app = Flask(__name__)


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

    enhanced_profile = data.get('enhancedProfile', '')
    user_description = f"{data['projectDescription']}\n\n{enhanced_profile}"

    try:
        llm_response_content = get_agent_response(user_description)
        try:
            recommendations = json.loads(llm_response_content).get('papers')
            final_recommendations = []
            for rec in recommendations:
                final_recommendations.append({
                    "title": rec.get("title", "N/A"),
                    "link": rec.get("link", "N/A"),
                    "description": rec.get("description", "Relevant based on user interest.")
                })
            return jsonify(final_recommendations)

        except json.JSONDecodeError:
            print(f"Failed to parse LLM response: {llm_response_content}")
            return jsonify({
                "error": "Failed to parse recommendations from LLM. Response was not valid JSON."}), 500
        except Exception as e:
            print(f"An unexpected error occurred after LLM call: {e}")
            return jsonify({"error": f"An server error occurred: {e}"}), 500

    except Exception as e:
        print(f"An error occurred in /api/recommendations: {e}")
        return jsonify({"error": f"An internal error occurred: {str(e)}"}), 500


@app.route('/api/upload-paper', methods=['POST'])
def upload_paper():
    """
    Handle PDF paper upload and enhance user profile.
    """
    if 'pdf' not in request.files:
        return jsonify({"error": "No PDF file provided"}), 400
        
    if 'paperContext' not in request.form:
        return jsonify({"error": "No paper context provided"}), 400
        
    if 'projectDescription' not in request.form:
        return jsonify({"error": "No project description provided"}), 400
        
    pdf_file = request.files['pdf']
    paper_context = request.form['paperContext']
    project_description = request.form['projectDescription']
    
    if not pdf_file.filename.endswith('.pdf'):
        return jsonify({"error": "File must be a PDF"}), 400
        
    try:
        pdf_content = pdf_file.read()
        logger.info(f"Processing PDF upload: {pdf_file.filename}")
        
        enhanced_profile = process_user_paper(pdf_content, paper_context, project_description)
        
        if not enhanced_profile:
            logger.error("Failed to process PDF and create enhanced profile")
            return jsonify({"error": "Failed to process PDF"}), 500
            
        logger.info("Successfully created enhanced profile with uploaded paper")
        logger.debug(f"Enhanced profile length: {len(enhanced_profile)} characters")

        return jsonify(enhanced_profile)
    except Exception as e:
        logger.error(f"Error processing PDF upload: {e}")
        return jsonify({"error": f"An error occurred while processing the PDF: {str(e)}"}), 500


def get_agent_response(user_description):
    messages = trigger_agent(user_description)['messages']

    for message in messages:
        logger.info(f"Messages: {message}")

    return messages[-1].content


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)  # nosec B201, B104
