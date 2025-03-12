from flask import Flask, request, jsonify
from flask_cors import CORS
from backend.rag_model import rag_model

app = Flask(__name__)
CORS(app)  # Allows cross-origin requests (for frontend integration)

@app.route('/ask', methods=['POST'])
def ask_rag():
    data = request.get_json()
    user_query = data.get("query")

    if not user_query:
        return jsonify({"error": "No query provided"}), 400

    response = rag_model.get_answer(user_query)  # Call your RAG model
    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)