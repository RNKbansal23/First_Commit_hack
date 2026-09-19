import json
import urllib.request
import re
import concurrent.futures
from datetime import datetime
from backend.scraper_lambda.database import save_job, update_health, get_all_jobs

# ---------------------------------------------------------
# Connectors
# ---------------------------------------------------------
class JobConnector:
    def __init__(self, company, platform):
        self.company = company
        self.platform = platform

    def fetch(self):
        raise NotImplementedError

class GreenhouseConnector(JobConnector):
    def __init__(self, company, board_token):
        super().__init__(company, 'Greenhouse')
        self.board_token = board_token

    def fetch(self):
        url = f"https://boards-api.greenhouse.io/v1/boards/{self.board_token}/jobs"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            jobs = []
            for job in data.get('jobs', []):
                jobs.append({
                    "id": f"gh_{job['id']}",
                    "external_id": str(job['id']),
                    "source_platform": self.platform,
                    "company": self.company,
                    "title": job.get('title', ''),
                    "location": job.get('location', {}).get('name', 'Remote'),
                    "url": job.get('absolute_url', ''),
                    "description": job.get('title', '')
                })
            return jobs

class LeverConnector(JobConnector):
    def __init__(self, company, board_token):
        super().__init__(company, 'Lever')
        self.board_token = board_token

    def fetch(self):
        url = f"https://api.lever.co/v0/postings/{self.board_token}?mode=json"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            jobs = []
            for job in data:
                jobs.append({
                    "id": f"lv_{job['id']}",
                    "external_id": str(job['id']),
                    "source_platform": self.platform,
                    "company": self.company,
                    "title": job.get('text', ''),
                    "location": job.get('categories', {}).get('location', 'Remote'),
                    "url": job.get('hostedUrl', ''),
                    "description": job.get('text', '')
                })
            return jobs

class WorkdayConnector(JobConnector):
    def __init__(self, company, tenant, wd_number, site_slug):
        super().__init__(company, 'Workday')
        self.tenant = tenant
        self.wd_number = wd_number
        self.site_slug = site_slug

    def fetch(self):
        # Fallback to empty for now since workday is flaky
        return []

class CustomConnector(JobConnector):
    def __init__(self, company, platform_name="Custom"):
        super().__init__(company, platform_name)
    def fetch(self):
        return []

# ---------------------------------------------------------
# Logic
# ---------------------------------------------------------
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
    fake_patterns = [r'\b[2-9]\+?\s*years?\b', r'\bmanager\b', r'\bstaff\b', r'\bsenior\b', r'\bprincipal\b', r'\bhead\b', r'\bvp\b', r'\bdirector\b', r'\blead\b']
    for pattern in fake_patterns:
        if re.search(pattern, combined): return False
    return True

def run_connectors():
    print("Running modular connectors...")
    connectors = [
        GreenhouseConnector("Figma", "figma"),
        GreenhouseConnector("Stripe", "stripe"),
        GreenhouseConnector("Airbnb", "airbnb"),
        GreenhouseConnector("Pinterest", "pinterest"),
        GreenhouseConnector("Reddit", "reddit"),
        GreenhouseConnector("Lyft", "lyft"),
        GreenhouseConnector("Twitch", "twitch"),
        GreenhouseConnector("Dropbox", "dropbox"),
        GreenhouseConnector("GitLab", "gitlab"),
        GreenhouseConnector("Discord", "discord"),
        LeverConnector("Spotify", "spotify"),
        LeverConnector("Meesho", "meesho")
    ]
    
    target_keywords = ['engineer', 'developer', 'sde', 'analyst', 'fresher', 'intern', 'junior', 'graduate']
    
    def process(connector):
        try:
            jobs = connector.fetch()
            update_health(connector.company, connector.platform, True)
            return jobs
        except Exception as e:
            update_health(connector.company, connector.platform, False)
            print(f"Failed {connector.company}: {e}")
            return []

    all_jobs = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process, c) for c in connectors]
        for f in concurrent.futures.as_completed(futures):
            all_jobs.extend(f.result())

    for job in all_jobs:
        if any(keyword in job['title'].lower() for keyword in target_keywords):
            if is_true_fresher(job['title'], job['description']):
                job['region'] = parse_region(job['location'])
                is_new = save_job(job)
                job['is_new'] = is_new

def lambda_handler(event, context):
    run_connectors()
    return {"jobs_array": get_all_jobs()}
