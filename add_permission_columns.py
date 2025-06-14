#!/usr/bin/env python3
"""
Add permission columns to user table
"""

import sqlite3

def add_permission_columns():
    """Add new permission columns to user table"""
    try:
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        # Add new permission columns
        permission_columns = [
            'can_access_admin',
            'can_manage_users', 
            'can_manage_categories',
            'can_delete_documents',
            'can_view_confidential',
            'can_view_audit_logs',
            'can_manage_system',
            'can_view_stats'
        ]
        
        for column in permission_columns:
            try:
                cursor.execute(f"ALTER TABLE user ADD COLUMN {column} BOOLEAN DEFAULT 0")
                print(f"Added column: {column}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"Column {column} already exists")
                else:
                    print(f"Error adding column {column}: {e}")
        
        # Update existing admin users to have all permissions
        cursor.execute("""
            UPDATE user 
            SET can_access_admin = 1,
                can_manage_users = 1,
                can_manage_categories = 1,
                can_delete_documents = 1,
                can_view_confidential = 1,
                can_view_audit_logs = 1,
                can_manage_system = 1,
                can_view_stats = 1
            WHERE is_admin = 1
        """)
        
        conn.commit()
        print("Successfully added permission columns and updated admin users")
        
        # Verify the changes
        cursor.execute("SELECT username, is_admin, can_access_admin, can_manage_users FROM user")
        users = cursor.fetchall()
        
        print("\nUser permissions status:")
        for user in users:
            print(f"  {user[0]}: is_admin={user[1]}, can_access_admin={user[2]}, can_manage_users={user[3]}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    add_permission_columns()
