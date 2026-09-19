import uuid
from backend.scraper_lambda.database import get_db

def run_match_engine(job):
    print(f"MatchEngine: Analyzing new job: {job['title']} at {job['company']}")
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM watch_rules')
    rules = c.fetchall()
    
    matched_notifications = []
    
    for rule in rules:
        user_id = rule['user_id']
        keywords = rule['title_keywords'].split(',') if rule['title_keywords'] else []
        exp_max = rule['experience_max']
        work_mode = rule['work_mode']
        
        # Keyword match
        job_combined = (job['title'] + " " + (job.get('description', '') or '')).lower()
        keyword_match = False
        if not keywords:
            keyword_match = True
        else:
            for kw in keywords:
                if kw.strip().lower() in job_combined:
                    keyword_match = True
                    break
                    
        # Work mode match
        mode_match = True
        if work_mode:
            job_mode = (job.get('work_mode') or '').lower()
            if work_mode.lower() not in job_mode and work_mode.lower() not in job['location'].lower():
                mode_match = False
                
        if keyword_match and mode_match:
            print(f"MatchEngine: Match found for user {user_id}!")
            notif_id = f"notif_{uuid.uuid4().hex[:8]}"
            c.execute('''
                INSERT INTO notifications (id, user_id, job_id, watch_id, read)
                VALUES (?, ?, ?, ?, ?)
            ''', (notif_id, user_id, job['id'], rule['id'], 0))
            
            notification_payload = {
                'notification_id': notif_id,
                'user_id': user_id,
                'job': job
            }
            matched_notifications.append(notification_payload)
            
    conn.commit()
    conn.close()
    
    # Fan out to SNS
    if matched_notifications:
        from backend.scraper_lambda.notifications import publish_to_sns
        for payload in matched_notifications:
            publish_to_sns(payload)

def lambda_handler(event, context):
    print("MatchEngine Lambda Triggered!")
    
    # EventBridge payload wrapper
    if 'detail' in event:
        job = event['detail']
        run_match_engine(job)
    else:
        print("Invalid event format")
        
    return {"statusCode": 200, "body": "MatchEngine executed"}
