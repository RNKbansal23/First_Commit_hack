import json
import urllib.request
import re
import os
import concurrent.futures
from datetime import datetime

def parse_region(location_str):
    loc = location_str.lower()
    if 'india' in loc or 'bengaluru' in loc or 'bangalore' in loc or 'mumbai' in loc or 'delhi' in loc or 'hyderabad' in loc or 'gurugram' in loc or 'pune' in loc or 'chennai' in loc:
        return 'India'
    elif 'us' in loc or 'united states' in loc or 'san francisco' in loc or 'new york' in loc or 'seattle' in loc:
        return 'US'
    elif 'remote' in loc:
        return 'Remote'
    else:
        return 'Other'

def is_true_fresher(title, description):
    combined = (title + " " + description).lower()
    fake_patterns = [
        r'\b[2-9]\+?\s*years?\b', 
        r'\bmanager\b',
        r'\bsenior\b',
        r'\bprincipal\b',
        r'\bhead\b',
        r'\bvp\b',
        r'\bdirector\b',
        r'\blead\b'
    ]
    for pattern in fake_patterns:
        if re.search(pattern, combined):
            return False
    return True

def fetch_greenhouse(company_name, board_token):
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            jobs = []
            for job in data.get('jobs', []):
                jobs.append({
                    "id": f"gh_{job['id']}",
                    "company": company_name,
                    "title": job.get('title', ''),
                    "location": job.get('location', {}).get('name', 'Remote'),
                    "url": job.get('absolute_url', ''),
                    "description": job.get('title', '')
                })
            return jobs
    except Exception as e:
        print(f"Greenhouse Error for {company_name}: {e}")
        return []

def fetch_lever(company_name, board_token):
    url = f"https://api.lever.co/v0/postings/{board_token}?mode=json"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
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

def fetch_enterprise_mock(company_name):
    mock_jobs = [{
        "id": f"mock_{company_name.lower()}_1",
        "company": company_name,
        "title": f"Software Engineer, University Graduate (2027)",
        "location": "Bengaluru, India",
        "url": f"https://careers.{company_name.lower()}.com",
        "description": "Entry level role for freshers."
    }]
    return mock_jobs

def lambda_handler(event, context):
    print("Initializing FirstMover Parallel Scraper Engine...")
    
    tasks = [
        ("Figma", "figma", fetch_greenhouse),
        ("Stripe", "stripe", fetch_greenhouse),
        ("Vercel", "vercel", fetch_greenhouse),
        ("Razorpay", "razorpay", fetch_greenhouse),
        ("Discord", "discord", fetch_greenhouse),
        ("Coinbase", "coinbase", fetch_greenhouse),
        ("Robinhood", "robinhood", fetch_greenhouse),
        ("Spotify", "spotify", fetch_lever),
        ("Atlassian", "atlassian", fetch_lever),
        ("Notion", "notionhq", fetch_lever),
        ("Cred", "cred", fetch_lever),
        ("PhonePe", "phonepe", fetch_lever),
        ("Google", None, lambda c, t: fetch_enterprise_mock(c)),
        ("Microsoft", None, lambda c, t: fetch_enterprise_mock(c)),
        ("Amazon", None, lambda c, t: fetch_enterprise_mock(c)),
        ("Adobe", None, lambda c, t: fetch_enterprise_mock(c)),
        ("Salesforce", None, lambda c, t: fetch_enterprise_mock(c)),
        ("Uber", None, lambda c, t: fetch_enterprise_mock(c)),
        ("NVIDIA", None, lambda c, t: fetch_enterprise_mock(c)),
        ("JPMorgan Chase", None, lambda c, t: fetch_enterprise_mock(c)),
        ("Walmart", None, lambda c, t: fetch_enterprise_mock(c))
    ]

    all_jobs = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for company, token, func in tasks:
            futures.append(executor.submit(func, company, token))
            
        for future in concurrent.futures.as_completed(futures):
            try:
                jobs = future.result()
                all_jobs.extend(jobs)
            except Exception as e:
                print(f"Error fetching jobs: {e}")

    seen_jobs_file = 'backend/scraper_lambda/seen_jobs.json'
    if os.path.exists(seen_jobs_file):
        with open(seen_jobs_file, 'r') as f:
            seen_jobs = set(json.load(f))
    else:
        seen_jobs = set()

    target_keywords = ['engineer', 'developer', 'sde', 'analyst', 'fresher', 'intern', 'junior', 'graduate']
    filtered_jobs = []
    new_seen_jobs = set(seen_jobs)
    
    for job in all_jobs:
        title_lower = job['title'].lower()
        if any(keyword in title_lower for keyword in target_keywords):
            if is_true_fresher(job['title'], job['description']):
                job['region'] = parse_region(job['location'])
                
                if job['id'] not in seen_jobs:
                    job['is_new'] = True
                    new_seen_jobs.add(job['id'])
                else:
                    job['is_new'] = False
                    
                filtered_jobs.append(job)

    with open(seen_jobs_file, 'w') as f:
        json.dump(list(new_seen_jobs), f)

    print(f"Scrape complete. Found {len(all_jobs)} total jobs, {len(filtered_jobs)} passed fresher filter.")

    return {
        "jobs_array": filtered_jobs[:100] 
    }
