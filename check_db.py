#!/usr/bin/env python3
"""
Check database schema
"""

import sqlite3

def check_database():
    """Check the user table schema"""
    try:
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        # Get table schema
        cursor.execute("PRAGMA table_info(user)")
        columns = cursor.fetchall()
        
        print("User table columns:")
        for column in columns:
            print(f"  {column[1]} - {column[2]}")
        
        # Check if new permission columns exist
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
        
        existing_columns = [col[1] for col in columns]
        
        print("\nPermission columns status:")
        for perm_col in permission_columns:
            status = "EXISTS" if perm_col in existing_columns else "MISSING"
            print(f"  {perm_col}: {status}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking database: {e}")

if __name__ == '__main__':
    check_database()
