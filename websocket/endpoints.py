from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/')
def serve_home_page():
    return ""

@app.route('api/recommendations', methods=['GET'])
def get_recommendations(query):
    return "" #llm.get_recommendations(query) or whatever