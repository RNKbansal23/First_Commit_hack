import sys
sys.path.append('backend/scraper_lambda')
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from backend.scraper_lambda.app import lambda_handler
from backend.scraper_lambda.database import get_health_status, get_all_drives, get_all_jobs
from extractor import start_extractor_thread

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

start_extractor_thread()

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    try:
        lambda_handler({}, None)
        
        experience_max = request.args.get('experience_max')
        skills = request.args.getlist('skills[]')
        work_mode = request.args.getlist('work_mode[]')
        title_match = request.args.get('title_match')
        region = request.args.get('region')
        posted_since_hours = request.args.get('posted_since')
        
        jobs = get_all_jobs()
        filtered = []
        for j in jobs:
            if experience_max:
                exp = j.get('experience_max')
                if exp is None or int(exp) > int(experience_max): continue
            if work_mode:
                if j.get('work_mode') not in work_mode: continue
            if title_match:
                if title_match.lower() not in j.get('title', '').lower(): continue
            if region and region != 'All':
                if j.get('region') != region: continue
            if posted_since_hours:
                import datetime
                posted = j.get('posted_at')
                if posted:
                    try:
                        dt = datetime.datetime.fromisoformat(posted.replace('Z', '+00:00'))
                        if dt < datetime.datetime.now(dt.tzinfo) - datetime.timedelta(hours=int(posted_since_hours)):
                            continue
                    except: pass
            
            if skills:
                js_json = j.get('skills')
                if not js_json: continue
                import json
                try:
                    js = json.loads(js_json)
                    if not any(s.lower() in [x.lower() for x in js] for s in skills):
                        continue
                except: continue
                
            filtered.append(j)
            
        return jsonify({"jobs_array": filtered[:200]}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/jobs/smart-search', methods=['POST'])
def smart_search():
    try:
        data = request.json
        query = data.get('query', '')
        
        q_lower = query.lower()
        parsed_filters = {}
        
        is_matched = False
        
        if 'python' in q_lower:
            parsed_filters['skills[]'] = ['Python']
            is_matched = True
        if 'remote' in q_lower:
            parsed_filters['work_mode[]'] = ['remote']
            is_matched = True
        if 'under 2' in q_lower or 'fresher' in q_lower or 'intern' in q_lower:
            parsed_filters['experience_max'] = 2
            is_matched = True
            
        if not is_matched or 'intern' in q_lower or 'backend' in q_lower or 'frontend' in q_lower:
            parsed_filters['title_match'] = query.strip()
            
        return jsonify({"parsed_filters": parsed_filters}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/drives', methods=['GET'])
def fetch_drives():
    try:
        return jsonify({"drives": get_all_drives()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin/connector-status', methods=['GET'])
def get_connector_status():
    try:
        return jsonify({"status": "ok", "connectors": get_health_status()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/internal/emit-notification', methods=['POST'])
def emit_notification():
    try:
        payload = request.json
        # Emitting to all connected clients for hackathon purposes
        # In prod, you'd use room=payload['user_id']
        socketio.emit('new_notification', payload)
        return jsonify({"status": "emitted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000, use_reloader=False, allow_unsafe_werkzeug=True)

