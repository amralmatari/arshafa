# Import all models to ensure they are registered with SQLAlchemy
from .user import User, Role, Permission
from .document import Document, Category, Tag, DocumentVersion
from .audit import AuditLog

