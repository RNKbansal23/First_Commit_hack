import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname('backend/scraper_lambda/database.py'), 'firstmover.db')
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("UPDATE watch_rules SET work_mode = '' WHERE user_id = 'demo_user';")
c.execute("DELETE FROM jobs;")
c.execute("DELETE FROM notifications;")
conn.commit()
conn.close()
print("Filter removed and jobs cleared!")
