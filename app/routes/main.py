"""
Main routes for the application
"""

from flask import Blueprint, render_template, request, current_app, abort, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func, desc
from app import db
from app.models.document import Document, Category, DocumentStatus
from app.models.user import User
from app.models.audit import AuditLog, AuditAction
from app.utils.date_utils import localize_datetime

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Home page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard with statistics and recent activities"""

    # استخدام استعلامات محددة بدلاً من استعلامات تلقائية
    user_stats = {
        'total_documents': db.session.execute(
            db.select(db.func.count()).select_from(Document).where(Document.author_id == current_user.id)
        ).scalar() or 0,
        'draft_documents': db.session.execute(
            db.select(db.func.count()).select_from(Document).where(
                Document.author_id == current_user.id,
                Document.status == 'draft'
            )
        ).scalar() or 0,
        'approved_documents': db.session.execute(
            db.select(db.func.count()).select_from(Document).where(
                Document.author_id == current_user.id,
                Document.status == 'approved'
            )
        ).scalar() or 0,
        'under_review_documents': db.session.execute(
            db.select(db.func.count()).select_from(Document).where(
                Document.author_id == current_user.id,
                Document.status == 'under_review'
            )
        ).scalar() or 0,
        'archived_documents': db.session.execute(
            db.select(db.func.count()).select_from(Document).where(
                Document.author_id == current_user.id,
                Document.status == 'archived'
            )
        ).scalar() or 0
    }

    # Get system statistics (for admins)
    system_stats = {}
    if current_user.can('manage_system'):
        system_stats = {
            'total_documents': db.session.execute(
                db.select(db.func.count()).select_from(Document)
            ).scalar() or 0,
            'total_users': db.session.execute(
                db.select(db.func.count()).select_from(User).where(User.is_active == True)
            ).scalar() or 0,
            'total_categories': db.session.execute(
                db.select(db.func.count()).select_from(Category)
            ).scalar() or 0,
            'documents_this_month': db.session.execute(
                db.select(db.func.count()).select_from(Document).where(
                    db.extract('year', Document.created_at) == db.extract('year', db.func.current_timestamp()),
                    db.extract('month', Document.created_at) == db.extract('month', db.func.current_timestamp())
                )
            ).scalar() or 0
        }

    # Get recent documents - استخدام استعلام محدد
    stmt = db.select(Document).where(Document.author_id == current_user.id).order_by(Document.updated_at.desc()).limit(5)
    recent_documents = db.session.execute(stmt).scalars().all()

    # Get recent activities
    stmt = db.select(AuditLog).where(AuditLog.user_id == current_user.id).order_by(AuditLog.created_at.desc()).limit(10)
    recent_activities = db.session.execute(stmt).scalars().all()

    # Get documents expiring soon
    from datetime import datetime, timedelta
    stmt = db.select(Document).where(
        Document.expiry_date.isnot(None),
        Document.expiry_date > datetime.now(),
        Document.expiry_date <= datetime.now() + timedelta(days=30),
        Document.status.in_(['approved', 'archived'])
    ).order_by(Document.expiry_date).limit(5)
    expiring_soon = db.session.execute(stmt).scalars().all()

    # Get popular categories
    stmt = db.select(
        Category.id,
        Category.name,
        Category.name_ar,
        db.func.count(Document.id).label('doc_count')
    ).join(Document).group_by(Category.id, Category.name, Category.name_ar).order_by(db.desc('doc_count')).limit(5)
    popular_categories = db.session.execute(stmt).all()

    return render_template('dashboard.html',
                         user_stats=user_stats,
                         system_stats=system_stats,
                         recent_documents=recent_documents,
                         recent_activities=recent_activities,
                         expiring_soon=expiring_soon,
                         popular_categories=popular_categories)

@bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@bp.route('/help')
@login_required
def help():
    """Help page"""
    return render_template('help.html')

@bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

@bp.route('/search')
@login_required
def search():
    """Global search page"""
    query = request.args.get('q', '')
    category_id = request.args.get('category')
    file_type = request.args.get('type')
    status = request.args.get('status')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    results = []
    total_results = 0

    # Check if search button was pressed (form submitted)
    search_submitted = request.args.get('search_submitted', False) or bool(request.args)

    # Always perform search when form is submitted or when there are parameters
    if search_submitted:
        from app.utils.search import search_documents
        results, total_results = search_documents(
            query=query,
            category_id=category_id,
            file_type=file_type,
            date_from=date_from,
            date_to=date_to,
            status=status,
            user=current_user
        )

        # Log search action
        if query or category_id or file_type or status or date_from or date_to:
            search_description = f"Search query: '{query}'" if query else "Filter search"
            if category_id:
                search_description += f", Category: {category_id}"
            if file_type:
                search_description += f", Type: {file_type}"
            if status:
                search_description += f", Status: {status}"
            if date_from or date_to:
                search_description += f", Date: {date_from} to {date_to}"
        else:
            search_description = "Show all documents"

        AuditLog.log_action(
            action=AuditAction.SEARCH_PERFORM,
            user=current_user,
            description=search_description,
            details=f"Results: {total_results}",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )

    # Get all categories for filter
    categories = Category.query.order_by(Category.name).all()

    # Get status choices
    status_choices = DocumentStatus.choices()

    return render_template('search.html',
                         query=query,
                         results=results,
                         total_results=total_results,
                         categories=categories,
                         status_choices=status_choices,
                         selected_category=category_id,
                         selected_type=file_type,
                         selected_status=status,
                         date_from=date_from,
                         date_to=date_to)

@bp.route('/statistics')
@login_required
def statistics():
    """Statistics page"""
    if not current_user.can('view_audit_logs'):
        abort(403)

    from datetime import datetime, timedelta
    from sqlalchemy import extract

    # Document statistics by month
    doc_stats_monthly_raw = db.session.query(
        extract('year', Document.created_at).label('year'),
        extract('month', Document.created_at).label('month'),
        func.count(Document.id).label('count')
    ).group_by('year', 'month').order_by('year', 'month').all()

    # Convert to serializable format
    doc_stats_monthly = [
        {
            'year': int(row.year) if row.year else 0,
            'month': int(row.month) if row.month else 0,
            'count': int(row.count) if row.count else 0
        }
        for row in doc_stats_monthly_raw
    ]

    # Document statistics by category
    doc_stats_category_raw = db.session.query(
        Category.name,
        Category.name_ar,
        func.count(Document.id).label('count')
    ).join(Document).group_by(Category.id, Category.name, Category.name_ar)\
     .order_by(desc('count')).all()

    # Convert to serializable format
    doc_stats_category = [
        {
            'name': row.name or '',
            'name_ar': row.name_ar or '',
            'count': int(row.count) if row.count else 0
        }
        for row in doc_stats_category_raw
    ]

    # Document statistics by status
    doc_stats_status_raw = db.session.query(
        Document.status,
        func.count(Document.id).label('count')
    ).group_by(Document.status).all()

    # Convert to serializable format
    doc_stats_status = [
        {
            'status': row.status or '',
            'count': int(row.count) if row.count else 0
        }
        for row in doc_stats_status_raw
    ]

    # User activity statistics
    user_activity_raw = db.session.query(
        User.username,
        User.first_name,
        User.last_name,
        func.count(AuditLog.id).label('activity_count')
    ).join(AuditLog).filter(
        AuditLog.created_at >= datetime.now() - timedelta(days=30)
    ).group_by(User.id, User.username, User.first_name, User.last_name)\
     .order_by(desc('activity_count')).limit(10).all()

    # Convert to serializable format
    user_activity = [
        {
            'username': row.username or '',
            'first_name': row.first_name or '',
            'last_name': row.last_name or '',
            'activity_count': int(row.activity_count) if row.activity_count else 0,
            'full_name': f"{row.first_name or ''} {row.last_name or ''}".strip() or row.username
        }
        for row in user_activity_raw
    ]

    # Storage statistics
    storage_stats_raw = db.session.query(
        func.sum(Document.file_size).label('total_size'),
        func.count(Document.id).label('total_files'),
        func.avg(Document.file_size).label('avg_size')
    ).first()

    # Convert to serializable format
    storage_stats = {
        'total_size': int(storage_stats_raw.total_size) if storage_stats_raw.total_size else 0,
        'total_files': int(storage_stats_raw.total_files) if storage_stats_raw.total_files else 0,
        'avg_size': float(storage_stats_raw.avg_size) if storage_stats_raw.avg_size else 0.0
    }

    # Additional statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    total_categories = Category.query.count()
    total_documents = Document.query.count()

    # Recent activity count
    recent_activity_count = AuditLog.query.filter(
        AuditLog.created_at >= datetime.now() - timedelta(days=7)
    ).count()

    return render_template('statistics.html',
                         doc_stats_monthly=doc_stats_monthly,
                         doc_stats_category=doc_stats_category,
                         doc_stats_status=doc_stats_status,
                         user_activity=user_activity,
                         storage_stats=storage_stats,
                         total_users=total_users,
                         active_users=active_users,
                         total_categories=total_categories,
                         total_documents=total_documents,
                         recent_activity_count=recent_activity_count)

@bp.before_app_request
def before_request():
    """Execute before each request"""
    if current_user.is_authenticated:
        current_user.ping()

# Error handlers
@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@bp.app_errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html'), 403

@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500








