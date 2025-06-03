import json
import os
import sys

from flask import Flask, request, jsonify, render_template
from llm.Agent import trigger_agent

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

    user_description = data['projectDescription']

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


def get_agent_response(user_description):
    return trigger_agent(user_description)['messages'][-1].content


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)  # nosec B201, B104
