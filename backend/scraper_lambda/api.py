import json
from database import get_all_jobs

def lambda_handler(event, context):
    try:
        jobs = get_all_jobs()
        
        # Apply Query String Filters
        query_params = event.get('queryStringParameters') or {}
        
        # Region Filter
        region = query_params.get('region')
        if region and region != 'Any Country/Region':
            jobs = [j for j in jobs if region.lower() in (j.get('region') or '').lower() or region.lower() in (j.get('location') or '').lower()]
            
        # Experience Max Filter
        exp_max = query_params.get('experience_max')
        if exp_max and exp_max != 'Any Experience':
            # Extract number from string like '3 Years' or 'Fresher (0)'
            try:
                import re
                if 'Fresher' in exp_max:
                    max_val = 0
                else:
                    nums = re.findall(r'\d+', exp_max)
                    max_val = int(nums[0]) if nums else 99
                
                # Simplified matching - just passing them through for hackathon demo
                # In real life, we'd parse job text for experience
            except:
                pass
                
        # Posted Since Filter (Any Time / Today / Last 3 Days)
        posted_since = query_params.get('posted_since')
        if posted_since and posted_since != 'Any Time':
            # Skipping complex date math for hackathon demo, assuming all jobs are fresh
            pass
            
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "OPTIONS,GET"
            },
            "body": json.dumps({"jobs_array": jobs})
        }
    except Exception as e:
        print(f"API Error: {e}")
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"error": str(e)})
        }
