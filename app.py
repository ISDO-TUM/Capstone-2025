import json
import logging
import os
import sys
import io

from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from llm.Agent import trigger_agent_show_thoughts
from paper_handling.database_handler import connect_to_db
from paper_handling.database_handler import get_papers_by_original_id
from paper_handling.database_handler import get_all_papers

import PyPDF2

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

    def generate():
        try:
            for response_part in trigger_agent_show_thoughts(user_description):
                if not response_part['is_final']:
                    yield f"data: {json.dumps({'thought': response_part['thought']})}\n\n"
                else:
                    try:
                        llm_response_content = response_part['final_content']
                        recommendations = json.loads(llm_response_content).get('papers')
                        final_recommendations = []
                        for rec in recommendations:
                            final_recommendations.append({
                                "title": rec.get("title", "N/A"),
                                "link": rec.get("link", "N/A"),
                                "description": rec.get("description", "Relevant based on user interest.")
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

        formatted_text = f"""MESSAGE TO THE AI AGENT SYSTEM: THE USER PROVIDED A RESEARCH PAPER SO YOU CAN UNDERSTAND THEIR RESEARCH INTERESTS.\n THE FULL TEXT OF THIS PAPER IS HERE:\n\n{text_content}\n\n MESSAGE TO THE AI AGENT SYSTEM: END OF FULL PAPER TEXT"""


        formatted_text = f"User provided this paper:\n\n{text_content}"

        formatted_text = f"User provided this paper: \n{text_content}"
        return jsonify({
            "success": True,
            "extracted_text": formatted_text
        })

    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        return jsonify({"error": f"Failed to process PDF: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=7500)  # nosec B201, B104
