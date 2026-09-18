from flask import Flask, jsonify
from flask_cors import CORS
from backend.scraper_lambda.app import lambda_handler

app = Flask(__name__)
CORS(app)

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    print("Received request for /api/jobs...")
    try:
        result = lambda_handler({}, None)
        return jsonify(result), 200
    except Exception as e:
        print(f"Error fetching jobs: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting local API server on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
