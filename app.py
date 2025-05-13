from flask import Flask, request, jsonify, render_template
import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                             '..')))
from llm.Prompting import llm_call
from llm.Prompts import TriggerS, RatingH, RatingS
from paper_handling.paper_metadata_retriever import get_multiple_topic_works

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
        keywords = llm_call(TriggerS, user_description)
        if keywords == -1:
            return jsonify({"error": "Failed to generate keywords from LLM"}), 500

        if not isinstance(keywords, str):
            return jsonify({"error": "Keywords format from LLM is invalid"}), 500

        string_array = [s.strip() for s in keywords.split(";")]

        retrieved_papers_works = get_multiple_topic_works(string_array)


        all_works = [work for sublist in retrieved_papers_works for work in sublist]

        if not all_works:
            return jsonify([]), 200

        papers_details_for_prompt = []
        for work in all_works:
            title = work.get('title', 'N/A')
            abstract = work.get('abstract', 'No abstract available.')
            papers_details_for_prompt.append(f"Title: {title}\nAbstract: {abstract}\n")

        retrieved_papers_string_representation = "\n---\n".join(papers_details_for_prompt)

        human_message_for_rating = RatingH.format(
            user_description=user_description,
            retrieved_papers=retrieved_papers_string_representation
        )

        llm_response_content = llm_call(RatingS, human_message_for_rating)

        if llm_response_content == -1:
            return jsonify({"error": "Failed to get ratings from LLM"}), 500

        try:
            recommendations = json.loads(llm_response_content)
            final_recommendations = []
            for rec in recommendations:
                original_work = next((w for w in all_works if
                                      w.get('id', '').endswith(rec.get('id')) or w.get(
                                          'title') == rec.get('title')), None)
                link = "#"
                if original_work:
                    link = original_work.get('doi') or original_work.get('open_access', {}).get(
                        'oa_url', '#')

                final_recommendations.append({
                    "title": rec.get("title", "N/A"),
                    "link": link,
                    "description": rec.get("reasoning", "Relevant based on user interest.")
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


if __name__ == '__main__':
    app.run(debug=True, port=5000)
