import os
import boto3
from datetime import datetime

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

def save_job(job):
    table = dynamodb.Table('FirstMover-Jobs')
    try:
        # Check if exists
        response = table.get_item(Key={'id': job['id']})
        if 'Item' not in response:
            if 'posted_at' not in job or not job['posted_at']:
                job['posted_at'] = datetime.utcnow().isoformat()
            table.put_item(Item=job)
            
            # Dispatch EventBridge Event
            try:
                from events import publish_job_created
                publish_job_created(job)
            except Exception as e:
                print(f"Failed to publish EventBridge event: {e}")
            return True
    except Exception as e:
        print(f"DynamoDB save error: {e}")
    return False

def update_health(company, platform, success):
    table = dynamodb.Table('FirstMover-Health')
    try:
        response = table.get_item(Key={'company': company})
        fails = 0
        if 'Item' in response:
            fails = response['Item'].get('consecutive_failures', 0)
            
        if not success:
            fails += 1
            
        status = 'healthy' if fails < 3 else 'degraded'
        
        table.put_item(Item={
            'company': company,
            'platform': platform,
            'last_poll_time': datetime.utcnow().isoformat(),
            'status': status,
            'consecutive_failures': fails
        })
    except Exception as e:
        print(f"DynamoDB health update error: {e}")

def get_health_status():
    table = dynamodb.Table('FirstMover-Health')
    try:
        response = table.scan()
        return response.get('Items', [])
    except Exception:
        return []

def get_all_jobs():
    table = dynamodb.Table('FirstMover-Jobs')
    try:
        response = table.scan()
        jobs = response.get('Items', [])
        # Sort by posted_at descending
        jobs.sort(key=lambda x: x.get('posted_at', ''), reverse=True)
        return jobs[:200]
    except Exception:
        return []

def get_all_drives():
    return []


