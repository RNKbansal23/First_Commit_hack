import sqlite3
import os
import json
import time
import threading

DB_PATH = os.path.join(os.path.dirname(__file__), 'backend', 'scraper_lambda', 'firstmover.db')

def stub_claude_extraction(title, description):
    # This is a stub simulating the Claude JSON response
    # Later, this will be replaced with boto3/anthropic API calls
    text = (title + " " + description).lower()
    
    # Heuristics for demo
    skills = []
    if "python" in text: skills.append("Python")
    if "java" in text or "spring" in text: skills.append("Java")
    if "react" in text or "javascript" in text: skills.append("React")
    if "aws" in text or "cloud" in text: skills.append("AWS")
    if "sql" in text: skills.append("SQL")
    if "c++" in text or "cpp" in text: skills.append("C++")
    
    work_mode = "remote" if "remote" in text else ("hybrid" if "hybrid" in text else "onsite")
    
    return {
        "experience_min": 0,
        "experience_max": 2 if "fresher" in text or "junior" in text else None,
        "seniority_level": "junior" if "junior" in text else "fresher",
        "skills": skills,
        "degree_requirement": "B.Tech/BE" if "b.tech" in text or "computer science" in text else None,
        "work_mode": work_mode,
        "visa_sponsorship_mentioned": False
    }

def run_extraction_pipeline():
    while True:
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            # Find jobs that haven't been extracted
            c.execute("SELECT id, title FROM jobs WHERE extracted = 0 AND extraction_failed = 0 LIMIT 10")
            jobs_to_process = c.fetchall()
            
            for row in jobs_to_process:
                job_id, title = row
                try:
                    # SIMULATING CLAUDE API CALL
                    extracted_data = stub_claude_extraction(title, "")
                    
                    c.execute('''
                        UPDATE jobs 
                        SET experience_min=?, experience_max=?, seniority_level=?, skills=?, degree_requirement=?, work_mode=?, visa_sponsorship_mentioned=?, extracted=1
                        WHERE id=?
                    ''', (
                        extracted_data["experience_min"],
                        extracted_data["experience_max"],
                        extracted_data["seniority_level"],
                        json.dumps(extracted_data["skills"]),
                        extracted_data["degree_requirement"],
                        extracted_data["work_mode"],
                        extracted_data["visa_sponsorship_mentioned"],
                        job_id
                    ))
                except Exception as e:
                    print(f"Extraction failed for {job_id}: {e}")
                    c.execute("UPDATE jobs SET extraction_failed=1 WHERE id=?", (job_id,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Extractor Loop Error: {e}")
            
        time.sleep(5) # Poll every 5 seconds

def start_extractor_thread():
    thread = threading.Thread(target=run_extraction_pipeline, daemon=True)
    thread.start()
    print("Background extraction pipeline started.")
