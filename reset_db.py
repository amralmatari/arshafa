import os
import sys
from app import create_app, db
from app.models.document import Document, Category, Tag, DocumentVersion
from app.models.user import User
from app.models.audit import AuditLog

def reset_database():
    """Reset the database completely"""
    app = create_app()
    
    with app.app_context():
        # Drop all tables
        db.drop_all()
        print("All tables dropped.")
        
        # Create all tables
        db.create_all()
        print("All tables created.")
        
        # Create initial data if needed
        create_initial_data()
        print("Initial data created.")

def create_initial_data():
    """Create initial data for the application"""
    # Create admin user
    admin = User(
        username='admin',
        email='admin@example.com',
        first_name='Admin',
        last_name='User',
        is_admin=True,
        is_active=True
    )
    admin.set_password('admin123')
    db.session.add(admin)
    
    # Create default categories
    categories = [
        Category(name='General', name_ar='عام', icon='folder', color='primary'),
        Category(name='Reports', name_ar='تقارير', icon='file-text', color='info'),
        Category(name='Contracts', name_ar='عقود', icon='file-contract', color='warning'),
        Category(name='Policies', name_ar='سياسات', icon='shield-alt', color='danger')
    ]
    db.session.add_all(categories)
    
    # Create default tags
    tags = [
        Tag(name='Important', name_ar='مهم', color='#dc3545'),
        Tag(name='Urgent', name_ar='عاجل', color='#fd7e14'),
        Tag(name='Archived', name_ar='مؤرشف', color='#6c757d')
    ]
    db.session.add_all(tags)
    
    # Commit changes
    db.session.commit()

if __name__ == "__main__":
    # Ask for confirmation
    confirm = input("This will reset the entire database. Are you sure? (y/n): ")
    if confirm.lower() == 'y':
        reset_database()
        print("Database reset complete.")
    else:
        print("Operation cancelled.")