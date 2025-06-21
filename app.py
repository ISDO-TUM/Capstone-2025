import json
import logging
import os
import sys

from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from llm.Agent import trigger_agent_show_thoughts
from paper_handling.database_handler import connect_to_db
from paper_handling.database_handler import get_papers_by_original_id
from paper_handling.database_handler import get_all_papers


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

    user_description = data['projectDescription']

    def generate():
        try:
            for response_part in trigger_agent_show_thoughts(user_description):
                if not response_part['is_final']:
                    yield f"data: {json.dumps({'thought': response_part['thought']})}\n\n"
                else:
                    try:
                        llm_response_content = response_part['final_content']
                        recommendations = json.loads(llm_response_content).get('papers')
                        all_papers = get_all_papers()
                        final_recommendations = []
                        for rec in recommendations:
                            paper_hash = "N/A"
                            rec_title = rec.get("title")

                            # Match by title (can enhance with link if needed)
                            for p in all_papers:
                                if p["title"] == rec_title:
                                    paper_hash = p["paper_hash"]
                                    break

                            final_recommendations.append({
                                "title": rec.get("title", "N/A"),
                                "link": rec.get("link", "N/A"),
                                "description": rec.get("description", "Relevant based on user interest."),
                                "hash": paper_hash
                            })

                        yield f"data: {json.dumps({'recommendations': final_recommendations})}\n\n"
                    except json.JSONDecodeError:
                        print(f"Failed to parse LLM response: {llm_response_content}")
                        error_payload = json.dumps({"error": "Failed to parse recommendations from LLM."})
                        yield f"data: {error_payload}\n\n"
                    except Exception as e:
                        print(f"An unexpected error occurred: {e}")
                        error_payload = json.dumps({"error": f"An server error occurred: {e}"})
                        yield f"data: {error_payload}\n\n"
        except Exception as e:
            print(f"An error occurred in /api/recommendations: {e}")
            error_payload = json.dumps({"error": f"An internal error occurred: {str(e)}"})
            yield f"data: {error_payload}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')


@app.route('/api/rate_paper', methods=['POST'])
def rate_paper():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    paper_hash = data.get("paper_hash")
    rating = data.get("rating")

    if not paper_hash or not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({"status": "error", "message": "Invalid paper_hash or rating"}), 400

    conn = connect_to_db()
    if not conn:
        return jsonify({"status": "error", "message": "Database connection failed"}), 500

    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE papers_table SET rating = %s WHERE paper_hash = %s;",
            (rating, paper_hash)
        )
        conn.commit()

        if cur.rowcount == 0:
            return jsonify({"status": "error", "message": "Paper not found"}), 404

        return jsonify({"status": "success", "message": "Rating saved"})
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating rating: {e}")
        return jsonify({"status": "error", "message": f"Database error: {e}"}), 500
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=7500)  # nosec B201, B104
