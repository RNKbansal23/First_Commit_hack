from backend.scraper_lambda.database import save_job
import time
import random

job = {
    'id': f'mock_{random.randint(1000, 9999)}',
    'external_id': f'ext_{random.randint(1000, 9999)}',
    'source_platform': 'mock',
    'company': 'Awesome Tech Inc',
    'title': 'Frontend Backend Developer Intern',
    'location': 'Remote, US',
    'url': 'https://example.com/job',
    'region': 'Remote'
}

print(f"Triggering ingestion of mock job: {job['title']}")
is_new = save_job(job)
print(f"Job inserted. Was it new? {is_new}")
