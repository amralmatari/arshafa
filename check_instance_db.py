#!/usr/bin/env python3
"""
Check instance database
"""

import sqlite3
import os

def check_instance_db():
    """Check instance database"""
    db_paths = ['app.db', 'instance/arshafa.db']
    
    for db_path in db_paths:
        print(f"\nChecking database: {db_path}")
        print("=" * 50)
        
        if not os.path.exists(db_path):
            print(f"Database file '{db_path}' does not exist!")
            continue
            
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if user table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
            user_table = cursor.fetchone()
            
            if not user_table:
                print("User table does not exist!")
                continue
            
            # Get user permissions
            cursor.execute("""
                SELECT id, username, is_admin, 
                       can_access_admin, can_manage_users, can_manage_categories,
                       can_delete_documents, can_view_confidential, can_view_audit_logs,
                       can_manage_system, can_view_stats
                FROM user
                LIMIT 5
            """)
            
            users = cursor.fetchall()
            
            print("Users found:")
            for user in users:
                print(f"  ID: {user[0]}, Username: {user[1]}, Is Admin: {user[2]}")
                print(f"    Permissions: {user[3:]}")
            
            # Update admin users
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
            print("Updated admin users with permissions")
            
            conn.close()
            
        except Exception as e:
            print(f"Error with {db_path}: {e}")

if __name__ == '__main__':
    check_instance_db()
