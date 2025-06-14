"""
User and Role Models
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
import jwt
from time import time
from app import db

# Association table for many-to-many relationship between roles and permissions
role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'), primary_key=True)
)

class Permission(db.Model):
    __tablename__ = 'permission'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    description = db.Column(db.String(255))

class Role(db.Model):
    __tablename__ = 'role'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    description = db.Column(db.String(255))
    is_default = db.Column(db.Boolean, default=False)
    
    # Define relationship to permissions
    permissions = db.relationship('Permission', secondary=role_permissions)

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    department = db.Column(db.String(64))
    phone = db.Column(db.String(20))
    profile_image = db.Column(db.String(255))
    bio = db.Column(db.Text)
    
    # Status and permissions
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    api_token = db.Column(db.String(64), unique=True, index=True)

    # Individual admin permissions
    can_access_admin = db.Column(db.Boolean, default=False)
    can_manage_users = db.Column(db.Boolean, default=False)
    can_manage_categories = db.Column(db.Boolean, default=False)
    can_delete_documents = db.Column(db.Boolean, default=False)
    can_view_confidential = db.Column(db.Boolean, default=False)
    can_view_audit_logs = db.Column(db.Boolean, default=False)
    can_manage_system = db.Column(db.Boolean, default=False)
    can_view_stats = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    last_login = db.Column(db.DateTime)
    last_seen = db.Column(db.DateTime, default=datetime.now)
    
    # Foreign keys
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    
    # Define relationship to role
    role = db.relationship('Role')
    
    # Document relationships are defined in the Document model with foreign_keys
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        """Return the user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def has_permission(self, permission_name):
        # Check individual admin permissions first
        permission_map = {
            'admin_access': self.can_access_admin,
            'manage_users': self.can_manage_users,
            'manage_categories': self.can_manage_categories,
            'delete_documents': self.can_delete_documents,
            'view_confidential_documents': self.can_view_confidential,
            'view_audit_logs': self.can_view_audit_logs,
            'manage_system_settings': self.can_manage_system,
            'view_system_stats': self.can_view_stats
        }

        if permission_name in permission_map:
            if permission_map[permission_name]:
                return True

        # Fallback to general admin check
        if self.is_admin:
            return True

        # Check role-based permissions
        if self.role and self.role.permissions:
            return any(p.name == permission_name for p in self.role.permissions)

        return False
    
    def can(self, permission):
        """Check if user has a specific permission"""
        # If user is admin, they have all permissions
        if hasattr(self, 'is_admin') and self.is_admin:
            return True

        # Check role-based permissions
        if self.role:
            # Super admin has all permissions
            if self.role.name == 'super_admin':
                return True

            # Check if role has the specific permission
            if self.role.permissions:
                return any(p.name == permission for p in self.role.permissions)

        # Check specific permissions for backward compatibility
        if permission == 'edit_document':
            return True  # All authenticated users can edit documents
        elif permission == 'delete_document':
            return hasattr(self, 'is_admin') and self.is_admin
        elif permission == 'view_confidential_documents':
            return hasattr(self, 'role') and self.role and self.role.name in ['admin', 'manager', 'supervisor']
        elif permission == 'manage_users':
            return (hasattr(self, 'is_admin') and self.is_admin) or (self.role and self.role.name in ['super_admin', 'admin'])
        elif permission == 'manage_system':
            return (hasattr(self, 'is_admin') and self.is_admin) or (self.role and self.role.name == 'super_admin')

        return False
    
    def ping(self):
        """Update last seen time."""
        self.last_seen = datetime.now()
        db.session.add(self)

    def get_reset_password_token(self, expires_in=600):
        """Generate password reset token (expires in 10 minutes by default)"""
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )

    @staticmethod
    def verify_reset_password_token(token):
        """Verify password reset token and return user"""
        try:
            id = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )['reset_password']
        except:
            return None
        return User.query.get(id)









