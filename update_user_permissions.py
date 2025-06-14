#!/usr/bin/env python3
"""
Script to update user table with new admin permission fields
"""

from app import create_app, db
from app.models.user import User

def update_user_permissions():
    """Add new permission fields to existing users"""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if columns exist by trying to access them
            users = User.query.all()
            
            for user in users:
                # Set default values for new permission fields if they don't exist
                if not hasattr(user, 'can_access_admin'):
                    print(f"Adding permission fields to user: {user.username}")
                    
                    # If user is already admin, grant all permissions
                    if user.is_admin:
                        user.can_access_admin = True
                        user.can_manage_users = True
                        user.can_manage_categories = True
                        user.can_delete_documents = True
                        user.can_view_confidential = True
                        user.can_view_audit_logs = True
                        user.can_manage_system = True
                        user.can_view_stats = True
                    else:
                        user.can_access_admin = False
                        user.can_manage_users = False
                        user.can_manage_categories = False
                        user.can_delete_documents = False
                        user.can_view_confidential = False
                        user.can_view_audit_logs = False
                        user.can_manage_system = False
                        user.can_view_stats = False
                else:
                    print(f"User {user.username} already has permission fields")
            
            db.session.commit()
            print("Successfully updated user permissions")
            
            # Test accessing the new fields
            test_user = User.query.first()
            if test_user:
                print(f"Test user {test_user.username} permissions:")
                print(f"  can_access_admin: {test_user.can_access_admin}")
                print(f"  can_manage_users: {test_user.can_manage_users}")
                print(f"  can_manage_categories: {test_user.can_manage_categories}")
                print(f"  can_delete_documents: {test_user.can_delete_documents}")
                print(f"  can_view_confidential: {test_user.can_view_confidential}")
                print(f"  can_view_audit_logs: {test_user.can_view_audit_logs}")
                print(f"  can_manage_system: {test_user.can_manage_system}")
                print(f"  can_view_stats: {test_user.can_view_stats}")
                
        except Exception as e:
            print(f"Error updating permissions: {e}")
            db.session.rollback()

if __name__ == '__main__':
    update_user_permissions()
