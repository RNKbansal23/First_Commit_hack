import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'firstmover.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    # Jobs Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            external_id TEXT,
            source_platform TEXT,
            company TEXT,
            title TEXT,
            location TEXT,
            url TEXT,
            region TEXT,
            posted_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Drives Table (Group E)
    c.execute('''
        CREATE TABLE IF NOT EXISTS drives (
            id TEXT PRIMARY KEY,
            company TEXT,
            exam_name TEXT,
            registration_opens_at TEXT,
            registration_closes_at TEXT,
            eligibility_criteria TEXT,
            source_url TEXT,
            status TEXT,
            last_checked DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Connector Health Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS connector_health (
            company TEXT PRIMARY KEY,
            platform TEXT,
            last_poll_time DATETIME,
            status TEXT,
            consecutive_failures INTEGER DEFAULT 0
        )
    ''')
    
    conn.commit()
    conn.close()

def save_job(job):
    conn = get_db()
    c = conn.cursor()
    is_new = False
    
    # Check if exists
    c.execute('SELECT id FROM jobs WHERE external_id=? AND source_platform=?', (job['external_id'], job['source_platform']))
    if not c.fetchone():
        c.execute('''
            INSERT INTO jobs (id, external_id, source_platform, company, title, location, url, region)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (job['id'], job['external_id'], job['source_platform'], job['company'], job['title'], job['location'], job['url'], job['region']))
        is_new = True
    
    conn.commit()
    conn.close()
    return is_new

def update_health(company, platform, success):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT consecutive_failures FROM connector_health WHERE company=?', (company,))
    row = c.fetchone()
    
    fails = 0
    if not success:
        fails = (row['consecutive_failures'] + 1) if row else 1
    
    status = 'healthy'
    if fails >= 3:
        status = 'degraded'
        
    c.execute('''
        INSERT INTO connector_health (company, platform, last_poll_time, status, consecutive_failures)
        VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?)
        ON CONFLICT(company) DO UPDATE SET
            last_poll_time = CURRENT_TIMESTAMP,
            status = excluded.status,
            consecutive_failures = excluded.consecutive_failures
    ''', (company, platform, status, fails))
    
    conn.commit()
    conn.close()

def get_health_status():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM connector_health')
    rows = c.fetchall()
    conn.close()
    return [dict(ix) for ix in rows]

def get_all_jobs():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM jobs ORDER BY posted_at DESC LIMIT 200')
    rows = c.fetchall()
    conn.close()
    return [dict(ix) for ix in rows]

def get_all_drives():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM drives')
    rows = c.fetchall()
    conn.close()
    return [dict(ix) for ix in rows]

init_db()
