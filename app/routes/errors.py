"""
Error handling routes
"""

from flask import Blueprint, render_template, request
from app import db

bp = Blueprint('errors', __name__)

@bp.app_errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('errors/404.html'), 404

@bp.app_errorhandler(403)
def forbidden_error(error):
    """Handle 403 errors"""
    return render_template('errors/403.html'), 403

@bp.app_errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    return render_template('errors/500.html'), 500

@bp.app_errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large errors"""
    return render_template('errors/413.html'), 413

@bp.app_errorhandler(429)
def too_many_requests(error):
    """Handle rate limit errors"""
    return render_template('errors/429.html'), 429
