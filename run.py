#!/usr/bin/env python3
"""
Arshafa Document Management System
Main application entry point
"""

import os
from flask import Flask
from flask.cli import FlaskGroup
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app import create_app, db
from app.models import User, Document, Category, Tag, AuditLog

# Create application instance
app = create_app(os.getenv('FLASK_CONFIG') or 'default')
cli = FlaskGroup(app)

@app.shell_context_processor
def make_shell_context():
    """Make database models available in Flask shell"""
    return {
        'db': db,
        'User': User,
        'Document': Document,
        'Category': Category,
        'Tag': Tag,
        'AuditLog': AuditLog
    }

@app.cli.command()
def init_db():
    """Initialize the database with default data"""
    from app.utils.init_data import init_default_data
    
    print("Creating database tables...")
    db.create_all()
    
    print("Initializing default data...")
    init_default_data()
    
    print("Database initialization completed!")

@app.cli.command()
def create_admin():
    """Create an admin user"""
    from app.models.user import User, Role
    from werkzeug.security import generate_password_hash
    
    username = input("Enter admin username: ")
    email = input("Enter admin email: ")
    password = input("Enter admin password: ")
    
    # Check if user already exists
    if User.query.filter_by(username=username).first():
        print(f"User {username} already exists!")
        return
    
    # Create admin user
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        admin_role = Role(name='admin', description='System Administrator')
        db.session.add(admin_role)
    
    admin_user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        role=admin_role,
        is_active=True
    )
    
    db.session.add(admin_user)
    db.session.commit()
    
    print(f"Admin user {username} created successfully!")

@app.cli.command()
def backup_db():
    """Create a database backup"""
    from app.utils.backup import create_backup
    
    backup_file = create_backup()
    print(f"Database backup created: {backup_file}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

