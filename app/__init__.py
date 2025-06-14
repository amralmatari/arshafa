"""
Arshafa Document Management System
Application Factory
"""

import os
from flask import Flask, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_babel import Babel, lazy_gettext as _l
from flask_wtf.csrf import CSRFProtect
from flask_moment import Moment
from config import config

# Initialize Flask extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
moment = Moment()
babel = Babel()
csrf = CSRFProtect()  # تأكد من تعريف csrf

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Define locale selector function for Babel
    def get_locale():
        # 1. Check if user has set a language preference
        if request.args.get('lang'):
            session['language'] = request.args.get('lang')
        
        # 2. Use session language if available
        if 'language' in session:
            return session['language']
        
        # 3. Use browser's preferred language
        return request.accept_languages.best_match(app.config['LANGUAGES']) or 'ar'
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    babel.init_app(app, locale_selector=get_locale)
    csrf.init_app(app)  # تأكد من تهيئة csrf مع التطبيق
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = _l('يرجى تسجيل الدخول للوصول إلى هذه الصفحة.')
    login_manager.login_message_category = 'info'
    
    # Create upload directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['BACKUP_FOLDER'], exist_ok=True)
    os.makedirs(app.config['WHOOSH_BASE'], exist_ok=True)
    
    # Template context processors
    @app.context_processor
    def inject_conf_vars():
        from flask_wtf.csrf import generate_csrf
        return {
            'LANGUAGES': app.config['LANGUAGES'],
            'CURRENT_LANGUAGE': get_locale(),
            'csrf_token': generate_csrf
        }

    # إضافة دالة مساعدة لترجمة حالة الوثيقة
    @app.template_filter('document_status')
    def document_status_filter(status):
        """تحويل حالة الوثيقة إلى نص مقروء"""
        from app.models.document import DocumentStatus
        return DocumentStatus.get_display_name(status)

    # إضافة دالة مساعدة لترجمة نوع الملف
    @app.template_filter('file_type_display')
    def file_type_display_filter(file_type):
        """تحويل نوع الملف إلى نص مقروء بالعربية"""
        if not file_type:
            return 'غير محدد'

        file_type_map = {
            'pdf': 'PDF',
            'doc': 'Word',
            'docx': 'Word',
            'xls': 'Excel',
            'xlsx': 'Excel',
            'ppt': 'PowerPoint',
            'pptx': 'PowerPoint',
            'txt': 'نص',
            'rtf': 'نص منسق',
            'jpg': 'صورة',
            'jpeg': 'صورة',
            'png': 'صورة',
            'gif': 'صورة',
            'bmp': 'صورة',
            'tiff': 'صورة',
            'zip': 'مضغوط',
            'rar': 'مضغوط',
            '7z': 'مضغوط',
            'mp4': 'فيديو',
            'avi': 'فيديو',
            'mov': 'فيديو',
            'wmv': 'فيديو',
            'mp3': 'صوت',
            'wav': 'صوت',
            'wma': 'صوت'
        }

        return file_type_map.get(file_type.lower(), file_type.upper())

    # إضافة دالة مساعدة لترجمة أنواع العمليات
    @app.template_filter('translate_action')
    def translate_action_filter(action):
        """ترجمة أنواع العمليات إلى العربية"""
        translations = {
            'LOGIN': 'تسجيل دخول',
            'LOGOUT': 'تسجيل خروج',
            'LOGIN_FAILED': 'فشل تسجيل الدخول',
            'DOCUMENT_CREATE': 'إنشاء وثيقة',
            'DOCUMENT_UPDATE': 'تحديث وثيقة',
            'DOCUMENT_DELETE': 'حذف وثيقة',
            'DOCUMENT_VIEW': 'عرض وثيقة',
            'DOCUMENT_DOWNLOAD': 'تحميل وثيقة',
            'USER_CREATE': 'إنشاء مستخدم',
            'USER_UPDATE': 'تحديث مستخدم',
            'USER_DELETE': 'حذف مستخدم',
            'USER_ACTIVATE': 'تفعيل مستخدم',
            'USER_DEACTIVATE': 'إلغاء تفعيل مستخدم',
            'USER_ROLE_CHANGE': 'تغيير دور مستخدم',
            'CATEGORY_CREATE': 'إنشاء فئة',
            'CATEGORY_UPDATE': 'تحديث فئة',
            'CATEGORY_DELETE': 'حذف فئة',
            'ROLE_CREATE': 'إنشاء دور',
            'ROLE_UPDATE': 'تحديث دور',
            'ROLE_DELETE': 'حذف دور',
            'PERMISSION_UPDATE': 'تحديث صلاحية',
            'SYSTEM_BACKUP': 'نسخ احتياطي',
            'SYSTEM_RESTORE': 'استعادة نسخة احتياطية',
            'SETTINGS_UPDATE': 'تحديث الإعدادات'
        }
        return translations.get(action, action or 'غير محدد')

    # إضافة دالة مساعدة لتحويل ألوان الفئات
    @app.template_filter('category_color_hex')
    def category_color_hex_filter(color):
        """تحويل لون الفئة إلى hex color"""
        if not color:
            return '#007bff'  # Default blue

        # If it's already a hex color, return it
        if color.startswith('#'):
            return color

        # Convert Bootstrap color classes to hex
        bootstrap_colors = {
            'primary': '#007bff',
            'secondary': '#6c757d',
            'success': '#28a745',
            'danger': '#dc3545',
            'warning': '#ffc107',
            'info': '#17a2b8',
            'light': '#f8f9fa',
            'dark': '#343a40'
        }

        return bootstrap_colors.get(color, '#007bff')

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.routes.documents import bp as documents_bp
    app.register_blueprint(documents_bp, url_prefix='/documents')
    
    from app.routes.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    from app.routes.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    from app.routes.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    # Register error handlers
    from app.routes.errors import bp as errors_bp
    app.register_blueprint(errors_bp)
    
    # Template filters
    @app.template_filter('isoformat')
    def isoformat_filter(dt):
        """تحويل التاريخ إلى تنسيق ISO 8601"""
        if dt is None:
            return ''
        # إضافة timezone info للأوقات المحلية إذا لم تكن موجودة
        if dt.tzinfo is None:
            import pytz
            saudi_tz = pytz.timezone('Asia/Riyadh')
            dt = saudi_tz.localize(dt)
        return dt.isoformat()
    
    @app.template_filter('to_hindu')
    def to_hindu_filter(text):
        """تحويل الأرقام العربية إلى أرقام هندية"""
        if not text:
            return text

        hindu_numerals = {
            '0': '٠', '1': '١', '2': '٢', '3': '٣', '4': '٤',
            '5': '٥', '6': '٦', '7': '٢', '8': '٨', '9': '٩'
        }

        result = str(text)
        for arabic, hindu in hindu_numerals.items():
            result = result.replace(arabic, hindu)

        return result

    @app.template_filter('localize_dt')
    def localize_datetime_filter(dt):
        """إضافة معلومات المنطقة الزمنية للتاريخ"""
        if dt is None:
            return None
        # إضافة timezone info للأوقات المحلية إذا لم تكن موجودة
        if dt.tzinfo is None:
            import pytz
            saudi_tz = pytz.timezone('Asia/Riyadh')
            dt = saudi_tz.localize(dt)
        return dt
    
    # تهيئة Flask-Moment
    moment.init_app(app)
    
    # تعيين تنسيق التاريخ الافتراضي
    app.config['MOMENT_DEFAULT_FORMAT'] = 'YYYY/MM/DD HH:mm'
    
    return app

# Import models to ensure they are registered with SQLAlchemy
from app.models import user, document, audit



















