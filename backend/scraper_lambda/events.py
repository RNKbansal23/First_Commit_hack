import os
import json
import boto3
from dotenv import load_dotenv

load_dotenv()

eb_client = boto3.client('events', 
    region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID', 'test'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY', 'test')
)

def publish_job_created(job):
    print(f"Publishing JobCreated event to EventBridge for: {job['title']}")
    try:
        response = eb_client.put_events(
            Entries=[
                {
                    'Source': 'jobpulse.connectors',
                    'DetailType': 'JobCreated',
                    'Detail': json.dumps(job),
                    'EventBusName': 'default' 
                }
            ]
        )
        print("EventBridge Response:", response)
    except Exception as e:
        print(f"EventBridge put_events failed (expected if local keys invalid): {e}")
        
    # Local Dev Hackathon Fallback: Trigger MatchEngine directly so the demo keeps working
    print("Triggering MatchEngine local handler...")
    from backend.scraper_lambda.match_engine import run_match_engine
    run_match_engine(job)
