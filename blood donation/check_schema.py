import sqlite3
import os

def check_db():
    db_path = os.path.join('instance', 'lifelink.db')
    if not os.path.exists(db_path):
        print("Database not found!")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # List tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cursor.fetchall()]
    print(f"Tables found: {tables}")
    
    # Check Hospital table specifically
    if 'hospitals' in tables:
        cursor.execute("PRAGMA table_info(hospitals);")
        columns = [r[1] for r in cursor.fetchall()]
        print(f"Hospital columns: {columns}")
    else:
        print("MISSING TABLE: hospitals")
        
    conn.close()

if __name__ == '__main__':
    check_db()
