import json
import urllib.request
import re
import concurrent.futures
from datetime import datetime
import os
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()
try:
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
except:
    pass

from database import save_job, update_health, get_all_jobs

# ---------------------------------------------------------
# Connectors
# ---------------------------------------------------------
class JobConnector:
    def __init__(self, company, platform):
        self.company = company
        self.platform = platform

    def fetch(self):
        raise NotImplementedError

class SmartRecruitersConnector(JobConnector):
    def __init__(self, company, companyIdentifier):
        super().__init__(company, 'smartrecruiters')
        self.companyIdentifier = companyIdentifier

    def fetch(self):
        jobs = []
        offset = 0
        limit = 100
        
        while True:
            url = f"https://api.smartrecruiters.com/v1/companies/{self.companyIdentifier}/postings?limit={limit}&offset={offset}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode())
                    content = data.get('content', [])
                    
                    for job in content:
                        loc = job.get('location', {})
                        city = loc.get('city', '')
                        region = loc.get('region', '')
                        country = loc.get('country', '')
                        remote = loc.get('remote', False)
                        
                        location_parts = [p for p in [city, region, country] if p]
                        location_str = ", ".join(location_parts) if location_parts else "Remote"
                        if remote and "Remote" not in location_str:
                            location_str += " (Remote)"
                        
                        jobs.append({
                            "id": f"sr_{job['id']}",
                            "external_id": str(job['id']),
                            "source_platform": self.platform,
                            "company": self.company,
                            "title": job.get('name', ''),
                            "location": location_str,
                            "url": f"https://jobs.smartrecruiters.com/{self.companyIdentifier}/{job['id']}",
                            "description": job.get('name', ''),
                            "posted_at": job.get('releasedDate')
                        })
                    
                    total = data.get('totalFound', 0)
                    offset += limit
                    if offset >= total:
                        break
            except urllib.error.HTTPError as e:
                if e.code in [401, 403]:
                    print(f"SmartRecruiters Auth Error for {self.company}: Needs API Key")
                raise e
                    
        return jobs

class GreenhouseConnector(JobConnector):
    def __init__(self, company, board_token):
        super().__init__(company, 'Greenhouse')
        self.board_token = board_token

    def fetch(self):
        url = f"https://boards-api.greenhouse.io/v1/boards/{self.board_token}/jobs?content=true"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            jobs = []
            for job in data.get('jobs', []):
                import html
                content = html.unescape(job.get('content', ''))
                # strip html tags safely
                desc_text = re.sub(r'<[^>]+>', ' ', content)
                jobs.append({
                    "id": f"gh_{job['id']}",
                    "external_id": str(job['id']),
                    "source_platform": self.platform,
                    "company": self.company,
                    "title": job.get('title', ''),
                    "location": job.get('location', {}).get('name', 'Remote'),
                    "url": job.get('absolute_url', ''),
                    "description": desc_text,
                    "posted_at": job.get('updated_at', '')
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
                    "description": job.get('descriptionPlain', job.get('text', '')),
                    "posted_at": str(job.get('createdAt', ''))
                })
            return jobs

class WorkdayConnector(JobConnector):
    def __init__(self, company, tenant, wd_number, site_slug):
        super().__init__(company, 'Workday')
        self.tenant = tenant
        self.wd_number = wd_number
        self.site_slug = site_slug

    def fetch(self):
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
    if 'india' in loc or 'bengaluru' in loc or 'bangalore' in loc or 'mumbai' in loc or 'delhi' in loc or 'hyderabad' in loc or 'gurugram' in loc or 'pune' in loc or 'chennai' in loc or 'in' in loc.split(','):
        return 'India'
    elif 'us' in loc or 'united states' in loc or 'san francisco' in loc or 'new york' in loc or 'seattle' in loc:
        return 'US'
    elif 'remote' in loc:
        return 'Remote'
    else:
        return 'Other'

def detect_gimmick(title, description):
    combined = (title + " " + description).lower()
    fake_patterns = {
        r'\b[2-9]\+?\s*years?\b': "Mentions 2+ years of experience",
        r'\bmanager\b': "Mentions 'Manager' in description",
        r'\bstaff\b': "Mentions 'Staff' level",
        r'\bsenior\b': "Mentions 'Senior' level",
        r'\bprincipal\b': "Mentions 'Principal'",
        r'\bhead\b': "Mentions 'Head of'",
        r'\bvp\b': "Mentions 'VP'",
        r'\bdirector\b': "Mentions 'Director'",
        r'\blead\b': "Mentions 'Lead'"
    }
    
    is_fresher_title = any(kw in title.lower() for kw in ['fresher', 'intern', 'junior', 'graduate', 'entry', 'new grad'])
    
    for pattern, reason in fake_patterns.items():
        if re.search(pattern, combined):
            if is_fresher_title:
                return {"is_gimmick": True, "reason": reason}
            else:
                # Not a fresher title, but requires experience. Just a normal job.
                return {"is_gimmick": False, "reason": None}
                
    return {"is_gimmick": False, "reason": None}

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
        LeverConnector("Meesho", "meesho"),
        SmartRecruitersConnector("Zomato", "Zomato1")
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
            # For SmartRecruiters, fetch description lazily if matched
            if job['source_platform'] == 'smartrecruiters' and job['description'] == job['title']:
                try:
                    req = urllib.request.Request(f"https://api.smartrecruiters.com/v1/companies/{job['company']}/postings/{job['external_id']}", headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=5) as response:
                        d = json.loads(response.read().decode())
                        job['description'] = d.get('jobAd', {}).get('sections', {}).get('jobDescription', {}).get('text', '')
                except:
                    pass

            gimmick_info = detect_gimmick(job['title'], job['description'])
            # Only save jobs that aren't senior masquerading as fresher
            if not gimmick_info['is_gimmick'] or 'fresher' in job['title'].lower() or 'intern' in job['title'].lower():
                job['region'] = parse_region(job['location'])
                job['is_gimmick'] = gimmick_info['is_gimmick']
                job['gimmick_reason'] = gimmick_info['reason']
                job['real_experience_required'] = gimmick_info.get('real_experience_required', 'Unknown')
                is_new = save_job(job)
                job['is_new'] = is_new

def lambda_handler(event, context):
    run_connectors()
    return {"jobs_array": get_all_jobs()}


if __name__ == '__main__':
    print('Testing scraper locally...')
    lambda_handler({}, {})
    print('Done!')

