"""
Audit Log Model for tracking user activities
"""

from datetime import datetime, timezone
import pytz

# تعريف المنطقة الزمنية
saudi_tz = pytz.timezone('Asia/Riyadh')

from flask_sqlalchemy import SQLAlchemy
from app import db

class AuditAction:
    """Audit action constants"""
    # User actions
    LOGIN = 'login'
    LOGOUT = 'logout'
    LOGIN_FAILED = 'login_failed'
    
    # Document actions
    DOCUMENT_CREATE = 'document_create'
    DOCUMENT_VIEW = 'document_view'
    DOCUMENT_DOWNLOAD = 'document_download'
    DOCUMENT_UPDATE = 'document_update'
    DOCUMENT_DELETE = 'document_delete'
    DOCUMENT_APPROVE = 'document_approve'
    DOCUMENT_REJECT = 'document_reject'
    DOCUMENT_ARCHIVE = 'document_archive'
    DOCUMENT_RESTORE = 'document_restore'
    DOCUMENT_VERSION_DOWNLOAD = 'document_version_download'  # Added this action
    
    # Category actions
    CATEGORY_CREATE = 'category_create'
    CATEGORY_UPDATE = 'category_update'
    CATEGORY_DELETE = 'category_delete'
    
    # Tag actions
    TAG_CREATE = 'tag_create'
    TAG_UPDATE = 'tag_update'
    TAG_DELETE = 'tag_delete'
    
    # User management actions
    USER_CREATE = 'user_create'
    USER_UPDATE = 'user_update'
    USER_DELETE = 'user_delete'
    USER_ACTIVATE = 'user_activate'
    USER_DEACTIVATE = 'user_deactivate'
    USER_ROLE_CHANGE = 'user_role_change'
    
    # System actions
    SYSTEM_BACKUP = 'system_backup'
    SYSTEM_RESTORE = 'system_restore'
    SYSTEM_CONFIG_CHANGE = 'system_config_change'
    
    # Search actions
    SEARCH_PERFORM = 'search_perform'
    
    @classmethod
    def get_action_description(cls, action):
        """Get Arabic description for action"""
        descriptions = {
            cls.LOGIN: 'تسجيل دخول',
            cls.LOGOUT: 'تسجيل خروج',
            cls.LOGIN_FAILED: 'فشل تسجيل الدخول',
            
            cls.DOCUMENT_CREATE: 'إنشاء وثيقة',
            cls.DOCUMENT_VIEW: 'عرض وثيقة',
            cls.DOCUMENT_DOWNLOAD: 'تحميل وثيقة',
            cls.DOCUMENT_UPDATE: 'تحديث وثيقة',
            cls.DOCUMENT_DELETE: 'حذف وثيقة',
            cls.DOCUMENT_APPROVE: 'اعتماد وثيقة',
            cls.DOCUMENT_REJECT: 'رفض وثيقة',
            cls.DOCUMENT_ARCHIVE: 'أرشفة وثيقة',
            cls.DOCUMENT_RESTORE: 'استعادة وثيقة',
            cls.DOCUMENT_VERSION_DOWNLOAD: 'تحميل إصدار وثيقة',  # Added description
            
            cls.CATEGORY_CREATE: 'إنشاء فئة',
            cls.CATEGORY_UPDATE: 'تحديث فئة',
            cls.CATEGORY_DELETE: 'حذف فئة',
            
            cls.TAG_CREATE: 'إنشاء علامة',
            cls.TAG_UPDATE: 'تحديث علامة',
            cls.TAG_DELETE: 'حذف علامة',
            
            cls.USER_CREATE: 'إنشاء مستخدم',
            cls.USER_UPDATE: 'تحديث مستخدم',
            cls.USER_DELETE: 'حذف مستخدم',
            cls.USER_ACTIVATE: 'تفعيل مستخدم',
            cls.USER_DEACTIVATE: 'إلغاء تفعيل مستخدم',
            cls.USER_ROLE_CHANGE: 'تغيير دور المستخدم',
            
            cls.SYSTEM_BACKUP: 'نسخ احتياطي للنظام',
            cls.SYSTEM_RESTORE: 'استعادة النظام',
            cls.SYSTEM_CONFIG_CHANGE: 'تغيير إعدادات النظام',
            
            cls.SEARCH_PERFORM: 'تنفيذ بحث'
        }
        return descriptions.get(action, action)

class AuditLog(db.Model):
    """Audit log model for tracking all system activities"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Action information
    action = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))
    details = db.Column(db.Text)  # JSON string with additional details
    
    # Target information
    target_type = db.Column(db.String(50))  # document, user, category, etc.
    target_id = db.Column(db.Integer)
    target_name = db.Column(db.String(255))
    
    # User information
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    username = db.Column(db.String(64))  # Store username for deleted users

    # Relationships
    user = db.relationship('User', backref='audit_logs', lazy='select')
    
    # Request information
    ip_address = db.Column(db.String(45))  # IPv6 compatible
    user_agent = db.Column(db.String(500))
    
    # Result information
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    @property
    def action_description(self):
        """Get Arabic description for the action"""
        return AuditAction.get_action_description(self.action)
    
    @staticmethod
    def log_action(action, user=None, target_type=None, target_id=None, target_name=None,
                   description=None, details=None, ip_address=None, user_agent=None,
                   success=True, error_message=None):
        """Create an audit log entry"""
        log_entry = AuditLog(
            action=action,
            description=description,
            details=details,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            user_id=user.id if user else None,
            username=user.username if user else None,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message
        )
        
        db.session.add(log_entry)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # Log to application logger if database logging fails
            import logging
            logging.error(f"Failed to create audit log: {str(e)}")
    
    @staticmethod
    def log_document_action(action, document, user=None, description=None, details=None,
                           ip_address=None, user_agent=None, success=True, error_message=None):
        """Log document-related actions"""
        AuditLog.log_action(
            action=action,
            user=user,
            target_type='document',
            target_id=document.id,
            target_name=document.title,
            description=description,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message
        )
    
    @staticmethod
    def log_user_action(action, target_user, user=None, description=None, details=None,
                       ip_address=None, user_agent=None, success=True, error_message=None):
        """Log user-related actions"""
        AuditLog.log_action(
            action=action,
            user=user,
            target_type='user',
            target_id=target_user.id,
            target_name=target_user.username,
            description=description,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message
        )
    
    @staticmethod
    def log_login_attempt(user, success=True, ip_address=None, user_agent=None, error_message=None):
        """Log login attempts"""
        action = AuditAction.LOGIN if success else AuditAction.LOGIN_FAILED
        AuditLog.log_action(
            action=action,
            user=user if success else None,
            target_type='user',
            target_id=user.id if user else None,
            target_name=user.username if user else 'Unknown',
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message
        )
    
    def to_dict(self):
        """Convert audit log to dictionary"""
        return {
            'id': self.id,
            'action': self.action if isinstance(self.action, str) else (self.action.name if self.action else None),
            'action_description': self.action_description or '',
            'description': self.description or '',
            'target_type': self.target_type or '',
            'target_name': self.target_name or '',
            'username': self.username or '',
            'ip_address': self.ip_address or '',
            'user_agent': self.user_agent or '',
            'success': bool(self.success),
            'error_message': getattr(self, 'error_message', None),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<AuditLog {self.action} by {self.username}>'




