#!/usr/bin/env python3
"""
Initialize system with default roles, permissions, and super admin user
"""

import os
import sys
from flask import Flask
from app import create_app, db
from app.models.user import User, Role, Permission

def init_permissions():
    """Create default permissions"""
    permissions = [
        ('view_documents', 'عرض الوثائق'),
        ('create_documents', 'إنشاء الوثائق'),
        ('edit_documents', 'تعديل الوثائق'),
        ('delete_documents', 'حذف الوثائق'),
        ('view_confidential_documents', 'عرض الوثائق السرية'),
        ('manage_categories', 'إدارة التصنيفات'),
        ('manage_users', 'إدارة المستخدمين'),
        ('manage_roles', 'إدارة الأدوار'),
        ('manage_system', 'إدارة النظام'),
        ('view_audit_logs', 'عرض سجلات المراجعة'),
        ('backup_system', 'نسخ احتياطي للنظام'),
        ('restore_system', 'استعادة النظام'),
    ]
    
    created_permissions = []
    for name, description in permissions:
        permission = Permission.query.filter_by(name=name).first()
        if not permission:
            permission = Permission(name=name, description=description)
            db.session.add(permission)
            created_permissions.append(permission)
            print(f"Created permission: {name}")
        else:
            print(f"Permission already exists: {name}")
    
    db.session.commit()
    return created_permissions

def init_roles():
    """Create default roles with permissions"""
    # Get all permissions
    all_permissions = Permission.query.all()
    permissions_dict = {p.name: p for p in all_permissions}
    
    # Define roles and their permissions
    roles_config = {
        'super_admin': {
            'description': 'مدير النظام - صلاحيات كاملة',
            'permissions': list(permissions_dict.keys()),  # All permissions
            'is_default': False
        },
        'admin': {
            'description': 'مدير - صلاحيات إدارية',
            'permissions': [
                'view_documents', 'create_documents', 'edit_documents', 'delete_documents',
                'view_confidential_documents', 'manage_categories', 'manage_users',
                'view_audit_logs'
            ],
            'is_default': False
        },
        'manager': {
            'description': 'مشرف - صلاحيات متوسطة',
            'permissions': [
                'view_documents', 'create_documents', 'edit_documents',
                'view_confidential_documents', 'manage_categories'
            ],
            'is_default': False
        },
        'user': {
            'description': 'مستخدم عادي - صلاحيات أساسية',
            'permissions': [
                'view_documents', 'create_documents', 'edit_documents'
            ],
            'is_default': True
        }
    }
    
    created_roles = []
    for role_name, config in roles_config.items():
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role(
                name=role_name,
                description=config['description'],
                is_default=config['is_default']
            )
            db.session.add(role)
            created_roles.append(role)
            print(f"Created role: {role_name}")
        else:
            print(f"Role already exists: {role_name}")
            
        # Assign permissions to role
        role_permissions = [permissions_dict[p] for p in config['permissions'] if p in permissions_dict]
        role.permissions = role_permissions
        
        print(f"  Assigned {len(role_permissions)} permissions to {role_name}")
    
    db.session.commit()
    return created_roles

def create_super_admin():
    """Create super admin user"""
    # Check if super admin already exists
    super_admin = User.query.filter_by(username='admin').first()
    if super_admin:
        print("Super admin user already exists")
        return super_admin
    
    # Get super admin role
    super_admin_role = Role.query.filter_by(name='super_admin').first()
    if not super_admin_role:
        print("Error: Super admin role not found!")
        return None
    
    # Create super admin user
    super_admin = User(
        username='admin',
        email='admin@arshafa.local',
        first_name='مدير',
        last_name='النظام',
        department='إدارة النظام',
        is_active=True,
        is_admin=True,
        role=super_admin_role
    )
    
    super_admin.set_password('admin@123')
    
    db.session.add(super_admin)
    db.session.commit()
    
    print("Created super admin user:")
    print(f"  Username: admin")
    print(f"  Password: admin@123")
    print(f"  Email: admin@arshafa.local")
    print(f"  Role: super_admin")
    
    return super_admin

def main():
    """Main initialization function"""
    print("Initializing Arshafa Document Management System...")
    
    # Create Flask app
    app = create_app(os.getenv('FLASK_CONFIG') or 'development')
    
    with app.app_context():
        # Create database tables
        print("Creating database tables...")
        db.create_all()
        
        # Initialize permissions
        print("\nInitializing permissions...")
        init_permissions()
        
        # Initialize roles
        print("\nInitializing roles...")
        init_roles()
        
        # Create super admin user
        print("\nCreating super admin user...")
        create_super_admin()
        
        print("\nSystem initialization completed successfully!")
        print("\nYou can now login with:")
        print("Username: admin")
        print("Password: admin@123")

if __name__ == '__main__':
    main()
