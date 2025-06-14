"""
Document and related models
"""

import os
from datetime import datetime, timedelta, timezone
import pytz
from flask_sqlalchemy import SQLAlchemy
from app import db

# تعريف المنطقة الزمنية
saudi_tz = pytz.timezone('Asia/Riyadh')

# Association table for document-tag many-to-many relationship
document_tag = db.Table('document_tag',
    db.Column('document_id', db.Integer, db.ForeignKey('document.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class Category(db.Model):
    """Document category model"""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_ar = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    description_ar = db.Column(db.Text, nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    icon = db.Column(db.String(50), nullable=True, default='folder')
    color = db.Column(db.String(20), nullable=True, default='primary')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    is_active = db.Column(db.Boolean, default=True)

    # العلاقات
    # تعديل العلاقة مع Document - لا تستخدم backref هنا لأننا سنعرفها في نموذج Document
    children = db.relationship('Category',
                              backref=db.backref('parent', remote_side=[id]),
                              lazy='dynamic',
                              cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Category {self.name}>'

    def get_display_name(self):
        """Get display name (Arabic if available, otherwise English)"""
        return self.name_ar if self.name_ar else self.name

    def get_display_description(self):
        """Get display description (Arabic if available, otherwise English)"""
        return self.description_ar if self.description_ar else self.description

    def get_full_path(self):
        """Get full hierarchical path of the category"""
        path = []
        current = self

        # Build path from current category to root
        while current:
            path.append(current.get_display_name())
            current = current.parent

        # Reverse to get root-to-leaf order
        path.reverse()

        # Join with arrow separator
        return ' ← '.join(path)

    def get_color_hex(self):
        """Get color as hex value, converting from Bootstrap class if needed"""
        if not self.color:
            return '#007bff'  # Default blue

        # If it's already a hex color, return it
        if self.color.startswith('#'):
            return self.color

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

        return bootstrap_colors.get(self.color, '#007bff')

    def get_color_class(self):
        """Get Bootstrap color class from hex color"""
        if not self.color:
            return 'primary'

        # If it's already a Bootstrap class, return it
        if not self.color.startswith('#'):
            return self.color

        # Convert hex colors to Bootstrap classes
        hex_to_bootstrap = {
            '#007bff': 'primary',
            '#6c757d': 'secondary',
            '#28a745': 'success',
            '#dc3545': 'danger',
            '#ffc107': 'warning',
            '#17a2b8': 'info',
            '#f8f9fa': 'light',
            '#343a40': 'dark'
        }

        return hex_to_bootstrap.get(self.color, 'primary')

    def to_dict(self):
        """Convert category to dictionary"""
        from sqlalchemy import func
        from app import db

        # استخدام استعلام SQL لحساب عدد الوثائق
        doc_count = db.session.query(func.count(Document.id)).filter(Document.category_id == self.id).scalar() or 0

        return {
            'id': self.id,
            'name': self.name,
            'name_ar': self.name_ar,
            'description': self.description,
            'description_ar': self.description_ar,
            'parent_id': self.parent_id,
            'icon': self.icon,
            'color': self.color,
            'color_hex': self.get_color_hex(),
            'color_class': self.get_color_class(),
            'is_active': self.is_active,
            'document_count': doc_count
        }

class Tag(db.Model):
    """Tag model for document labeling"""
    __tablename__ = 'tag'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    name_ar = db.Column(db.String(50))  # Arabic name
    description = db.Column(db.String(255))
    color = db.Column(db.String(7), default='#6c757d')  # Hex color code

    # Usage statistics
    usage_count = db.Column(db.Integer, default=0)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Define relationship to documents - using back_populates
    documents = db.relationship('Document', secondary=document_tag, back_populates='tags')

# تعريف ثوابت حالة الوثيقة
class DocumentStatus:
    DRAFT = 'draft'
    UNDER_REVIEW = 'under_review'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    ARCHIVED = 'archived'
    EXPIRED = 'expired'
    DELETED = 'deleted'

    @classmethod
    def choices(cls):
        """إرجاع خيارات الحالة مرتبة حسب دورة حياة الوثيقة"""
        return [
            (cls.DRAFT, 'مسودة'),
            (cls.UNDER_REVIEW, 'قيد المراجعة'),
            (cls.APPROVED, 'معتمد'),
            (cls.REJECTED, 'مرفوض'),
            (cls.ARCHIVED, 'مؤرشف'),
            (cls.EXPIRED, 'منتهي الصلاحية'),
            (cls.DELETED, 'محذوف')
        ]

    @classmethod
    def get_display_name(cls, status):
        """Get Arabic display name for status"""
        status_dict = dict(cls.choices())
        return status_dict.get(status, status)

    @classmethod
    def get_status_color(cls, status):
        """Get Bootstrap color class for status"""
        color_map = {
            cls.DRAFT: 'secondary',
            cls.UNDER_REVIEW: 'warning',
            cls.APPROVED: 'success',
            cls.REJECTED: 'danger',
            cls.ARCHIVED: 'info',
            cls.EXPIRED: 'dark',
            cls.DELETED: 'danger'
        }
        return color_map.get(status, 'secondary')

class Document(db.Model):
    """Document model"""
    __tablename__ = 'document'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    filename = db.Column(db.String(255))
    original_filename = db.Column(db.String(255))  # Original filename as uploaded
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)  # Size in bytes
    file_type = db.Column(db.String(50))  # MIME type or extension
    status = db.Column(db.String(20), default='draft')  # draft, under_review, approved, rejected

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    published_at = db.Column(db.DateTime)
    expiry_date = db.Column(db.DateTime)  # Add expiry date field

    # Security and access
    is_confidential = db.Column(db.Boolean, default=False)
    access_level = db.Column(db.String(20), default='public')  # public, internal, confidential, secret

    # Content indexing
    content_text = db.Column(db.Text)  # Extracted text for search
    keywords = db.Column(db.Text)  # Comma-separated keywords

    # Statistics
    view_count = db.Column(db.Integer, default=0)
    download_count = db.Column(db.Integer, default=0)

    # Relationships
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', backref='documents')

    # تصحيح العلاقة مع Category
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    category = db.relationship('Category', backref=db.backref('documents', lazy='dynamic'))

    # استخدام back_populates بدلاً من backref
    tags = db.relationship('Tag', secondary='document_tag', back_populates='documents')

    # استخدام back_populates بدلاً من backref
    versions = db.relationship('DocumentVersion', back_populates='document',
                              cascade='all, delete-orphan')

    # Define a property to get the author's full name
    @property
    def author_name(self):
        if self.author:
            return self.author.get_full_name()
        return "Unknown"

    @property
    def file_extension(self):
        """Get file extension with dot"""
        _, ext = os.path.splitext(self.original_filename)
        return ext

    def get_status_display(self):
        """Get Arabic display name for document status"""
        return DocumentStatus.get_display_name(self.status)

    def get_status_color(self):
        """Get Bootstrap color class for document status"""
        return DocumentStatus.get_status_color(self.status)

    def ensure_file_type(self):
        """Ensure document has a valid file_type, auto-detect if missing"""
        if not self.file_type or self.file_type.strip() == '':
            # Try to determine from original_filename
            if self.original_filename:
                filename_lower = self.original_filename.lower()

                # If filename is just an extension
                if filename_lower in ['docx', 'doc', 'xlsx', 'xls', 'pptx', 'ppt', 'pdf', 'jpg', 'png']:
                    self.file_type = filename_lower
                else:
                    # Extract extension
                    import os
                    _, ext = os.path.splitext(filename_lower)
                    if ext:
                        self.file_type = ext[1:]  # Remove dot

            # Try to determine from title if still empty
            if not self.file_type and self.title:
                title_lower = self.title.lower()
                if any(word in title_lower for word in ['وورد', 'word']):
                    self.file_type = 'docx'
                elif any(word in title_lower for word in ['اكسل', 'excel']):
                    self.file_type = 'xlsx'
                elif any(word in title_lower for word in ['powerpoint', 'بوربوينت']):
                    self.file_type = 'pptx'
                elif 'pdf' in title_lower:
                    self.file_type = 'pdf'
                else:
                    # Default to docx
                    self.file_type = 'docx'

            # Ensure we have something
            if not self.file_type:
                self.file_type = 'docx'  # Default fallback

class DocumentVersion(db.Model):
    """Document version model for tracking document history"""
    __tablename__ = 'document_version'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    version_number = db.Column(db.String(20), nullable=False)  # e.g., "1.0", "1.1", etc.
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)  # Size in bytes
    comment = db.Column(db.Text)  # Version comment

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_by = db.relationship('User')

    # استخدام back_populates بدلاً من backref
    document = db.relationship('Document', back_populates='versions')

    def __repr__(self):
        return f'<DocumentVersion {self.document_id}-{self.version_number}>'






































