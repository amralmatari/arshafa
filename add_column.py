import sqlite3
import os

def add_missing_column():
    """Add the missing filename column to the document table"""
    db_path = 'instance/arshafa.db'
    
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(document)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'filename' not in columns:
            print("Adding 'filename' column to 'document' table...")
            cursor.execute("ALTER TABLE document ADD COLUMN filename TEXT;")
            conn.commit()
            print("Column added successfully.")
        else:
            print("Column 'filename' already exists in 'document' table.")
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(document)")
        columns = [col[1] for col in cursor.fetchall()]
        print("Current columns in 'document' table:", columns)
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_missing_column()