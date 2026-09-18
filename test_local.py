from backend.scraper_lambda.app import lambda_handler

if __name__ == "__main__":
    print("Running scraper locally...")
    # Simulate an EventBridge trigger with an empty event
    result = lambda_handler({}, None)
    
    print("\n--- RESULTS ---")
    jobs = result.get('jobs_array', [])
    print(f"Found {len(jobs)} jobs.")
    
    for job in jobs[:3]: # Print first 3 to verify
        print(f"Company: {job['company']}")
        print(f"Title:   {job['title']}")
        print(f"URL:     {job['url']}")
        print("-" * 20)