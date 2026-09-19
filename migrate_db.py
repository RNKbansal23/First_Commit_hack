import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'backend', 'scraper_lambda', 'firstmover.db')

def migrate():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Try adding columns. If they exist, it will throw an error, which we ignore.
    new_columns = [
        ("experience_min", "INTEGER"),
        ("experience_max", "INTEGER"),
        ("seniority_level", "TEXT"),
        ("skills", "TEXT"),
        ("degree_requirement", "TEXT"),
        ("work_mode", "TEXT"),
        ("visa_sponsorship_mentioned", "BOOLEAN"),
        ("extraction_failed", "BOOLEAN DEFAULT 0"),
        ("extracted", "BOOLEAN DEFAULT 0")
    ]
    
    for col_name, col_type in new_columns:
        try:
            c.execute(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_type}")
            print(f"Added column {col_name}")
        except sqlite3.OperationalError as e:
            # Column already exists
            pass
            
    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == '__main__':
    migrate()
