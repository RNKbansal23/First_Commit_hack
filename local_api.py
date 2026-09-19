from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from backend.scraper_lambda.app import lambda_handler
from backend.scraper_lambda.database import get_health_status, get_all_drives, get_db
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
        
        conn = get_db()
        c = conn.cursor()
        
        query = 'SELECT * FROM jobs WHERE 1=1'
        params = []
        
        if experience_max:
            # STRICT filter to prove it works: must have extracted experience and it must be <= requested
            query += ' AND experience_max <= ? AND experience_max IS NOT NULL'
            params.append(int(experience_max))
            
        if work_mode:
            placeholders = ','.join('?' for _ in work_mode)
            query += f' AND work_mode IN ({placeholders})'
            params.extend(work_mode)
            
        if title_match:
            query += ' AND title LIKE ?'
            params.append(f'%{title_match}%')
            
        if region and region != 'All':
            query += ' AND region = ?'
            params.append(region)
            
        if posted_since_hours:
            query += ' AND posted_at >= datetime("now", ?)'
            params.append(f'-{posted_since_hours} hours')
            
        query += ' ORDER BY posted_at DESC LIMIT 200'
        c.execute(query, params)
        rows = c.fetchall()
        jobs = [dict(ix) for ix in rows]
        
        if skills:
            filtered_jobs = []
            for j in jobs:
                job_skills_json = j['skills']
                if not job_skills_json: continue
                import json
                try:
                    job_skills = json.loads(job_skills_json)
                    if any(s.lower() in [js.lower() for js in job_skills] for s in skills):
                        filtered_jobs.append(j)
                except:
                    pass
            jobs = filtered_jobs
            
        conn.close()
        return jsonify({"jobs_array": jobs}), 200
    except Exception as e:
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

