import sqlite3
import os
from datetime import datetime

def recreate_document_table():
    """Recreate the document table with all required columns"""
    db_path = 'instance/arshafa.db'
    
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Backup existing data if any
        print("Backing up existing document data...")
        cursor.execute("SELECT * FROM document")
        existing_data = cursor.fetchall()
        
        # Get column names
        cursor.execute("PRAGMA table_info(document)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Current columns: {columns}")
        
        # Create a temporary table with all required columns
        print("Creating temporary table with all required columns...")
        cursor.execute("""
        CREATE TABLE document_new (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            filename TEXT,
            file_path TEXT,
            file_size INTEGER,
            file_type TEXT,
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            published_at TIMESTAMP,
            expiry_date TIMESTAMP,
            is_confidential BOOLEAN DEFAULT 0,
            access_level TEXT DEFAULT 'public',
            content_text TEXT,
            keywords TEXT,
            view_count INTEGER DEFAULT 0,
            download_count INTEGER DEFAULT 0,
            author_id INTEGER,
            category_id INTEGER,
            FOREIGN KEY (author_id) REFERENCES user (id),
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
        """)
        
        # Copy data from old table to new table
        if existing_data:
            print("Copying existing data to new table...")
            # Create a dynamic INSERT statement based on existing columns
            placeholders = ", ".join(["?" for _ in columns])
            columns_str = ", ".join(columns)
            
            for row in existing_data:
                cursor.execute(f"INSERT INTO document_new ({columns_str}) VALUES ({placeholders})", row)
        
        # Drop old table and rename new table
        print("Replacing old table with new table...")
        cursor.execute("DROP TABLE document")
        cursor.execute("ALTER TABLE document_new RENAME TO document")
        
        conn.commit()
        print("Document table recreated successfully with all required columns.")
        
        # Verify the new table structure
        cursor.execute("PRAGMA table_info(document)")
        new_columns = [col[1] for col in cursor.fetchall()]
        print(f"New columns: {new_columns}")
        
    except sqlite3.Error as e:
        conn.rollback()
        print(f"SQLite error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    recreate_document_table()