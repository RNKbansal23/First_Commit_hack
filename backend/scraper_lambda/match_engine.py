import uuid
import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
watch_rules_table = dynamodb.Table('FirstMover-WatchRules')

def run_match_engine(job):
    print(f"MatchEngine: Analyzing new job: {job['title']} at {job['company']}")
    
    try:
        response = watch_rules_table.scan()
        rules = response.get('Items', [])
    except Exception as e:
        print(f"MatchEngine Error scanning DB: {e}")
        return
        
    matched_notifications = []
    
    for rule in rules:
        user_id = rule.get('user_id')
        if not user_id: continue
        
        keywords = rule.get('title_keywords', '').split(',') if rule.get('title_keywords') else []
        exp_max = rule.get('experience_max', 99)
        work_mode = rule.get('work_mode', 'any').lower()
        target_companies = rule.get('companies', [])
        
        # 1. Company match
        if target_companies and job.get('company') not in target_companies:
            continue
            
        # 2. Keyword match
        job_combined = (job.get('title', '') + " " + (job.get('description', '') or '')).lower()
        keyword_match = False
        if not keywords:
            keyword_match = True
        else:
            for kw in keywords:
                if kw.strip() and kw.strip().lower() in job_combined:
                    keyword_match = True
                    break
                    
        # 3. Work mode / Location match
        mode_match = True
        if work_mode and work_mode != 'any':
            job_loc = (job.get('location') or '').lower()
            job_mode = (job.get('work_mode') or '').lower()
            
            if work_mode not in job_mode and work_mode not in job_loc:
                mode_match = False
                
        if keyword_match and mode_match:
            print(f"MatchEngine: Match found for user {user_id}!")
            notif_id = f"notif_{uuid.uuid4().hex[:8]}"
            
            notification_payload = {
                'notification_id': notif_id,
                'user_id': user_id,
                'job': job
            }
            matched_notifications.append(notification_payload)
            
    # Fan out to SNS
    if matched_notifications:
        from notifications import publish_to_sns
        for payload in matched_notifications:
            try:
                publish_to_sns(payload)
            except Exception as e:
                print(f"MatchEngine SNS Error: {e}")

def lambda_handler(event, context):
    print("MatchEngine Lambda Triggered!")
    
    # EventBridge payload wrapper
    if 'detail' in event:
        job = event['detail']
        run_match_engine(job)
    else:
        print("Invalid event format")
        
    return {"statusCode": 200, "body": "MatchEngine executed"}
