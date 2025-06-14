"""
Initialize default data for the application
"""

from app import db
from app.models.user import User, Role, Permission
from app.models.document import Category, Tag
from werkzeug.security import generate_password_hash

def init_default_data():
    """Initialize default roles, permissions, categories, and admin user"""
    
    # Create default permissions
    permissions = [
        ('view_documents', 'عرض الوثائق'),
        ('create_documents', 'إنشاء الوثائق'),
        ('edit_documents', 'تعديل الوثائق'),
        ('delete_documents', 'حذف الوثائق'),
        ('approve_documents', 'اعتماد الوثائق'),
        ('view_confidential_documents', 'عرض الوثائق السرية'),
        ('manage_categories', 'إدارة الفئات'),
        ('manage_tags', 'إدارة العلامات'),
        ('manage_users', 'إدارة المستخدمين'),
        ('manage_system', 'إدارة النظام'),
        ('view_audit_logs', 'عرض سجل الأنشطة'),
        ('backup_system', 'نسخ احتياطي للنظام'),
        ('restore_system', 'استعادة النظام')
    ]
    
    for perm_name, perm_desc in permissions:
        permission = Permission.query.filter_by(name=perm_name).first()
        if not permission:
            permission = Permission(name=perm_name, description=perm_desc)
            db.session.add(permission)
    
    db.session.commit()
    
    # Create default roles
    Role.insert_roles()
    
    # Create default categories
    categories = [
        {
            'name': 'Administrative Documents',
            'name_ar': 'الوثائق الإدارية',
            'description': 'Administrative and management documents',
            'description_ar': 'الوثائق الإدارية والتنظيمية',
            'color': '#007bff',
            'icon': 'building'
        },
        {
            'name': 'Financial Documents',
            'name_ar': 'الوثائق المالية',
            'description': 'Financial reports and documents',
            'description_ar': 'التقارير والوثائق المالية',
            'color': '#28a745',
            'icon': 'dollar-sign'
        },
        {
            'name': 'Legal Documents',
            'name_ar': 'الوثائق القانونية',
            'description': 'Legal contracts and agreements',
            'description_ar': 'العقود والاتفاقيات القانونية',
            'color': '#dc3545',
            'icon': 'gavel'
        },
        {
            'name': 'Technical Documents',
            'name_ar': 'الوثائق التقنية',
            'description': 'Technical specifications and manuals',
            'description_ar': 'المواصفات التقنية والأدلة',
            'color': '#6f42c1',
            'icon': 'cogs'
        },
        {
            'name': 'Human Resources',
            'name_ar': 'الموارد البشرية',
            'description': 'HR policies and employee documents',
            'description_ar': 'سياسات الموارد البشرية ووثائق الموظفين',
            'color': '#fd7e14',
            'icon': 'users'
        },
        {
            'name': 'Marketing Materials',
            'name_ar': 'المواد التسويقية',
            'description': 'Marketing and promotional materials',
            'description_ar': 'المواد التسويقية والترويجية',
            'color': '#e83e8c',
            'icon': 'bullhorn'
        }
    ]
    
    for cat_data in categories:
        category = Category.query.filter_by(name=cat_data['name']).first()
        if not category:
            category = Category(**cat_data)
            db.session.add(category)
    
    # Create subcategories
    subcategories = [
        {
            'name': 'Policies',
            'name_ar': 'السياسات',
            'parent_name': 'Administrative Documents',
            'color': '#0056b3',
            'icon': 'file-contract'
        },
        {
            'name': 'Procedures',
            'name_ar': 'الإجراءات',
            'parent_name': 'Administrative Documents',
            'color': '#004085',
            'icon': 'list-ol'
        },
        {
            'name': 'Budget Reports',
            'name_ar': 'تقارير الميزانية',
            'parent_name': 'Financial Documents',
            'color': '#1e7e34',
            'icon': 'chart-line'
        },
        {
            'name': 'Invoices',
            'name_ar': 'الفواتير',
            'parent_name': 'Financial Documents',
            'color': '#155724',
            'icon': 'receipt'
        },
        {
            'name': 'Contracts',
            'name_ar': 'العقود',
            'parent_name': 'Legal Documents',
            'color': '#721c24',
            'icon': 'handshake'
        },
        {
            'name': 'Compliance',
            'name_ar': 'الامتثال',
            'parent_name': 'Legal Documents',
            'color': '#a71d2a',
            'icon': 'shield-alt'
        }
    ]
    
    db.session.commit()  # Commit categories first
    
    for subcat_data in subcategories:
        parent_name = subcat_data.pop('parent_name')
        parent = Category.query.filter_by(name=parent_name).first()
        
        if parent:
            subcategory = Category.query.filter_by(
                name=subcat_data['name'], 
                parent_id=parent.id
            ).first()
            
            if not subcategory:
                subcategory = Category(**subcat_data, parent_id=parent.id)
                db.session.add(subcategory)
    
    # Create default tags
    tags = [
        {'name': 'urgent', 'name_ar': 'عاجل', 'color': '#dc3545'},
        {'name': 'important', 'name_ar': 'مهم', 'color': '#fd7e14'},
        {'name': 'confidential', 'name_ar': 'سري', 'color': '#6f42c1'},
        {'name': 'draft', 'name_ar': 'مسودة', 'color': '#6c757d'},
        {'name': 'approved', 'name_ar': 'معتمد', 'color': '#28a745'},
        {'name': 'archived', 'name_ar': 'مؤرشف', 'color': '#17a2b8'},
        {'name': 'public', 'name_ar': 'عام', 'color': '#007bff'},
        {'name': 'internal', 'name_ar': 'داخلي', 'color': '#ffc107'},
        {'name': 'template', 'name_ar': 'نموذج', 'color': '#e83e8c'},
        {'name': 'report', 'name_ar': 'تقرير', 'color': '#20c997'}
    ]
    
    for tag_data in tags:
        tag = Tag.query.filter_by(name=tag_data['name']).first()
        if not tag:
            tag = Tag(**tag_data)
            db.session.add(tag)
    
    # Create default admin user
    admin_role = Role.query.filter_by(name='admin').first()
    admin_user = User.query.filter_by(username='admin').first()
    
    if not admin_user and admin_role:
        admin_user = User(
            username='admin',
            email='admin@arshafa.local',
            first_name='مدير',
            last_name='النظام',
            department='تقنية المعلومات',
            role=admin_role,
            is_active=True,
            email_confirmed=True
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
    
    # Create default test user
    user_role = Role.query.filter_by(name='editor').first()
    test_user = User.query.filter_by(username='user').first()
    
    if not test_user and user_role:
        test_user = User(
            username='user',
            email='user@arshafa.local',
            first_name='مستخدم',
            last_name='تجريبي',
            department='الإدارة العامة',
            role=user_role,
            is_active=True,
            email_confirmed=True
        )
        test_user.set_password('user123')
        db.session.add(test_user)
    
    # Create viewer test user
    viewer_role = Role.query.filter_by(name='viewer').first()
    viewer_user = User.query.filter_by(username='viewer').first()
    
    if not viewer_user and viewer_role:
        viewer_user = User(
            username='viewer',
            email='viewer@arshafa.local',
            first_name='مشاهد',
            last_name='تجريبي',
            department='المراجعة',
            role=viewer_role,
            is_active=True,
            email_confirmed=True
        )
        viewer_user.set_password('viewer123')
        db.session.add(viewer_user)
    
    db.session.commit()
    
    print("Default data initialized successfully!")
    print("Default users created:")
    print("  Admin: admin / admin123")
    print("  Editor: user / user123")
    print("  Viewer: viewer / viewer123")
