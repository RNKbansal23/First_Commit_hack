from flask import Flask, jsonify
from flask_cors import CORS
from backend.scraper_lambda.app import lambda_handler
from backend.scraper_lambda.database import get_health_status, get_all_drives

app = Flask(__name__)
CORS(app)

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    try:
        result = lambda_handler({}, None)
        return jsonify(result), 200
    except Exception as e:
        print(f"Error fetching jobs: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/drives', methods=['GET'])
def fetch_drives():
    try:
        drives = get_all_drives()
        return jsonify({"drives": drives}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin/connector-status', methods=['GET'])
def get_connector_status():
    try:
        health = get_health_status()
        return jsonify({"status": "ok", "connectors": health}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
