import json
import urllib.request
from datetime import datetime

# ---------------------------------------------------------
# 1. Greenhouse Scraper (Swiggy, Razorpay, Juspay)
# ---------------------------------------------------------
def fetch_greenhouse(company_name, board_token):
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            jobs = []
            for job in data.get('jobs', []):
                jobs.append({
                    "id": f"gh_{job['id']}",
                    "company": company_name,
                    "title": job.get('title', ''),
                    "location": job.get('location', {}).get('name', 'Remote'),
                    "url": job.get('absolute_url', ''),
                    "description": job.get('title', '') # Used by Bedrock for AI scoring
                })
            return jobs
    except Exception as e:
        print(f"Greenhouse Error for {company_name}: {e}")
        return []

# ---------------------------------------------------------
# 2. Lever Scraper (PhonePe)
# ---------------------------------------------------------
def fetch_lever(company_name, board_token):
    url = f"https://api.lever.co/v0/postings/{board_token}?mode=json"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            jobs = []
            for job in data:
                jobs.append({
                    "id": f"lv_{job['id']}",
                    "company": company_name,
                    "title": job.get('text', ''),
                    "location": job.get('categories', {}).get('location', 'Remote'),
                    "url": job.get('hostedUrl', ''),
                    "description": job.get('text', '') 
                })
            return jobs
    except Exception as e:
        print(f"Lever Error for {company_name}: {e}")
        return []

# ---------------------------------------------------------
# 3. Workday Scraper (Flipkart, Walmart)
# ---------------------------------------------------------
def fetch_workday(company_name, tenant_url):
    # Workday requires a POST request to their internal API
    url = f"{tenant_url}/wday/cxs/{company_name.lower()}/customReq/jobs"
    payload = json.dumps({
        "appliedFacets": {},
        "limit": 20,
        "offset": 0,
        "searchText": ""
    }).encode('utf-8')
    
    try:
        req = urllib.request.Request(url, data=payload, headers={
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        })
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            jobs = []
            for job in data.get('jobPostings', []):
                jobs.append({
                    "id": f"wd_{job.get('bulletinId', '0')}",
                    "company": company_name,
                    "title": job.get('title', ''),
                    "location": job.get('locationsText', 'Remote'),
                    "url": tenant_url + job.get('externalPath', ''),
                    "description": job.get('title', '')
                })
            return jobs
    except Exception as e:
        print(f"Workday Error for {company_name}: {e}")
        return []

# ---------------------------------------------------------
# Main Lambda Handler (The Engine)
# ---------------------------------------------------------
def lambda_handler(event, context):
    print("Initializing FirstMover Scraper Engine...")
    
    all_jobs = []

    # 1. Fetch from Greenhouse (Verified Tokens)
    all_jobs.extend(fetch_greenhouse("Figma", "figma"))
    all_jobs.extend(fetch_greenhouse("Stripe", "stripe"))
    all_jobs.extend(fetch_greenhouse("Vercel", "vercel"))

    # 2. Fetch from Lever (Verified Tokens)
    all_jobs.extend(fetch_lever("Spotify", "spotify"))
    all_jobs.extend(fetch_lever("Coupa", "coupa"))

    target_keywords = ['engineer', 'developer', 'sde', 'analyst', 'fresher', 'intern', 'junior']
    filtered_jobs = []
    
    for job in all_jobs:
        title_lower = job['title'].lower()
        if any(keyword in title_lower for keyword in target_keywords):
            filtered_jobs.append(job)

    print(f"Scrape complete. Found {len(all_jobs)} total jobs, {len(filtered_jobs)} passed initial keyword filter.")

    return {
        "jobs_array": filtered_jobs[:40] 
    }