"""
Custom decorators for route protection
"""

from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(f):
    """
    Decorator that checks if the current user is an admin
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def role_required(role_name):
    """
    Decorator that checks if the current user has a specific role
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.has_role(role_name):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator