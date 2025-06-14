"""
API routes for the application
"""

from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models.document import Document, Category, Tag
from app.models.user import User
from app.utils.decorators import admin_required
from app.utils.search import get_search_manager

bp = Blueprint('api', __name__)

# API authentication (simple token-based)
def token_required(f):
    """Decorator for token-based API authentication"""
    from functools import wraps
    
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-API-Token')
        
        if not token:
            return jsonify({'error': 'API token is missing'}), 401
        
        # Simple token validation (in production, use a more secure method)
        user = User.query.filter_by(api_token=token).first()
        if not user:
            return jsonify({'error': 'Invalid API token'}), 401
        
        return f(user, *args, **kwargs)
    
    return decorated

# Document API endpoints
@bp.route('/documents', methods=['GET'])
@token_required
def get_documents(user):
    """Get list of documents"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Basic query
    query = Document.query
    
    # Apply filters
    category_id = request.args.get('category_id', type=int)
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    # Get documents with pagination
    documents = query.order_by(Document.updated_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    
    # Format response
    result = {
        'documents': [doc.to_dict() for doc in documents.items],
        'pagination': {
            'page': documents.page,
            'per_page': documents.per_page,
            'total': documents.total,
            'pages': documents.pages
        }
    }
    
    return jsonify(result)

@bp.route('/documents/<int:id>', methods=['GET'])
@token_required
def get_document(user, id):
    """Get a single document"""
    document = Document.query.get_or_404(id)
    return jsonify(document.to_dict())

@bp.route('/search', methods=['GET'])
@token_required
def search(user):
    """Search documents"""
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Additional filters
    category_id = request.args.get('category_id', type=int)
    file_type = request.args.get('file_type')
    
    # Perform search
    search_manager = get_search_manager()
    results = search_manager.search_documents(
        query=query,
        category_id=category_id,
        file_type=file_type,
        page=page,
        per_page=per_page
    )
    
    return jsonify(results)

# Category API endpoints
@bp.route('/categories', methods=['GET'])
@token_required
def get_categories(user):
    """Get list of categories"""
    categories = Category.query.all()
    return jsonify([cat.to_dict() for cat in categories])

# Tag API endpoints
@bp.route('/tags', methods=['GET'])
@token_required
def get_tags(user):
    """Get list of tags"""
    tags = Tag.query.all()
    return jsonify([tag.to_dict() for tag in tags])

# User API endpoints (admin only)
@bp.route('/users', methods=['GET'])
@token_required
def get_users(user):
    """Get list of users (admin only)"""
    if not user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])

# System status endpoint
@bp.route('/status', methods=['GET'])
def status():
    """Get system status (public)"""
    return jsonify({
        'status': 'online',
        'version': current_app.config.get('VERSION', '1.0.0'),
        'api_version': 'v1'
    })
