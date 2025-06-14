#!/usr/bin/env python3
"""
Check user permissions in database
"""

import sqlite3

def check_user_permissions():
    """Check current user permissions"""
    try:
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        # Get all users with their permissions
        cursor.execute("""
            SELECT id, username, is_admin, 
                   can_access_admin, can_manage_users, can_manage_categories,
                   can_delete_documents, can_view_confidential, can_view_audit_logs,
                   can_manage_system, can_view_stats
            FROM user
        """)
        
        users = cursor.fetchall()
        
        print("Current user permissions:")
        print("-" * 80)
        
        for user in users:
            print(f"User ID: {user[0]}")
            print(f"Username: {user[1]}")
            print(f"Is Admin: {user[2]}")
            print(f"Can Access Admin: {user[3]}")
            print(f"Can Manage Users: {user[4]}")
            print(f"Can Manage Categories: {user[5]}")
            print(f"Can Delete Documents: {user[6]}")
            print(f"Can View Confidential: {user[7]}")
            print(f"Can View Audit Logs: {user[8]}")
            print(f"Can Manage System: {user[9]}")
            print(f"Can View Stats: {user[10]}")
            print("-" * 40)
        
        # Update admin users to have all permissions
        print("Updating admin users...")
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
        print("Updated admin users with all permissions")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    check_user_permissions()
