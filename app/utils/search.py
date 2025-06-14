"""
Search utilities for document indexing and retrieval
"""

import os
import re
from datetime import datetime
from whoosh.index import create_in, open_dir, exists_in  # تغيير create_index إلى create_in
from whoosh.fields import Schema, TEXT, ID, DATETIME, KEYWORD
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh.query import And, Or, Term, DateRange
from whoosh.analysis import StandardAnalyzer, CharsetFilter, StemmingAnalyzer
from whoosh.support.charset import accent_map
from flask import current_app
from app.models.document import Document, DocumentStatus
from app.models.user import User

# Arabic-aware analyzer
arabic_analyzer = StandardAnalyzer() | CharsetFilter(accent_map)

# Document schema for search index
document_schema = Schema(
    id=ID(stored=True, unique=True),
    title=TEXT(stored=True, analyzer=arabic_analyzer),
    title_ar=TEXT(stored=True, analyzer=arabic_analyzer),
    description=TEXT(stored=True, analyzer=arabic_analyzer),
    description_ar=TEXT(stored=True, analyzer=arabic_analyzer),
    content=TEXT(analyzer=arabic_analyzer),
    filename=TEXT(stored=True),
    file_type=KEYWORD(stored=True),
    category=TEXT(stored=True, analyzer=StandardAnalyzer()),
    tags=KEYWORD(stored=True, commas=True),
    author=TEXT(stored=True),
    status=KEYWORD(stored=True),
    created_at=DATETIME(stored=True),
    updated_at=DATETIME(stored=True)
)

class SearchManager:
    """Manages document search indexing and querying"""
    
    def __init__(self):
        self.index_dir = current_app.config['WHOOSH_BASE']
        self.index = None
        self._ensure_index()
    
    def _ensure_index(self):
        """Ensure search index exists"""
        if not os.path.exists(self.index_dir):
            os.makedirs(self.index_dir)
        
        if not exists_in(self.index_dir):
            self.index = create_in(self.index_dir, document_schema)  # تغيير create_index إلى create_in
        else:
            self.index = open_dir(self.index_dir)
    
    def add_document(self, document):
        """Add or update document in search index"""
        writer = self.index.writer()
        
        try:
            # Extract text content from file if possible
            content_text = self._extract_text_content(document)
            
            # Prepare tags
            tags = ','.join([tag.name for tag in document.tags])
            
            writer.update_document(
                id=str(document.id),
                title=document.title or '',
                title_ar=document.title or '',  # Use title for both fields
                description=document.description or '',
                description_ar=document.description or '',  # Use description for both fields
                content=content_text,
                filename=document.original_filename or document.filename or '',
                file_type=document.file_type or '',
                category=document.category.get_display_name() if document.category else '',
                tags=tags,
                author=document.author.get_full_name() if document.author else '',
                status=document.status,
                created_at=document.created_at,
                updated_at=document.updated_at
            )
            
            writer.commit()
            return True
            
        except Exception as e:
            writer.cancel()
            current_app.logger.error(f"Error adding document to search index: {str(e)}")
            return False
    
    def remove_document(self, document_id):
        """Remove document from search index"""
        writer = self.index.writer()

        try:
            writer.delete_by_term('id', str(document_id))
            writer.commit()
            return True

        except Exception as e:
            writer.cancel()
            current_app.logger.error(f"Error removing document from search index: {str(e)}")
            return False

    def update_document(self, document):
        """Update document in search index"""
        writer = self.index.writer()

        try:
            # Remove existing document
            writer.delete_by_term('id', str(document.id))

            # Add updated document
            self._add_document_to_writer(writer, document)

            writer.commit()
            current_app.logger.info(f"Document {document.id} updated in search index")
            return True

        except Exception as e:
            writer.cancel()
            current_app.logger.error(f"Error updating document in search index: {str(e)}")
            return False
    
    def search_documents(self, query_string, category_id=None, file_type=None, 
                        date_from=None, date_to=None, status=None, user=None, 
                        page=1, per_page=20):
        """Search documents with filters"""
        
        with self.index.searcher() as searcher:
            # Build query
            query_parts = []
            
            # Text search in multiple fields
            if query_string:
                fields = ['title', 'title_ar', 'description', 'description_ar', 'content', 'filename']
                parser = MultifieldParser(fields, self.index.schema)
                text_query = parser.parse(query_string)
                query_parts.append(text_query)
            
            # Category filter
            if category_id:
                from app.models.document import Category
                try:
                    # Convert category_id to int since it comes as string from URL
                    category_id_int = int(category_id)
                    category = Category.query.get(category_id_int)
                    if category:
                        # Use QueryParser for TEXT field
                        from whoosh.qparser import QueryParser
                        category_parser = QueryParser('category', self.index.schema)
                        # Escape special characters and use quotes for exact match
                        escaped_name = category.get_display_name().replace('"', '\\"')
                        category_query = category_parser.parse(f'"{escaped_name}"')
                        query_parts.append(category_query)
                except (ValueError, TypeError):
                    # If category_id is not a valid integer, skip this filter
                    pass
            
            # File type filter
            if file_type:
                file_type_query = Term('file_type', file_type)
                query_parts.append(file_type_query)
            
            # Status filter
            if status:
                status_query = Term('status', status)
                query_parts.append(status_query)
            
            # Date range filter
            if date_from or date_to:
                from datetime import datetime
                # Convert string dates to datetime objects
                start_date = None
                end_date = None

                if date_from:
                    try:
                        start_date = datetime.strptime(date_from, '%Y-%m-%d')
                    except ValueError:
                        pass

                if date_to:
                    try:
                        end_date = datetime.strptime(date_to, '%Y-%m-%d')
                        # Set to end of day
                        end_date = end_date.replace(hour=23, minute=59, second=59)
                    except ValueError:
                        pass

                if start_date or end_date:
                    date_query = DateRange('created_at', start_date, end_date)
                    query_parts.append(date_query)
            
            # Combine all query parts
            if query_parts:
                if len(query_parts) == 1:
                    final_query = query_parts[0]
                else:
                    final_query = And(query_parts)
            else:
                # If no filters, return all documents
                from whoosh.query import Every
                final_query = Every()
            
            # Execute search
            results = searcher.search_page(final_query, page, per_page)
            
            # Filter results based on user permissions
            filtered_results = []
            for hit in results:
                doc_id = int(hit['id'])
                document = Document.query.get(doc_id)
                
                if document and self._can_user_access_document(document, user):
                    result_data = {
                        'id': doc_id,
                        'title': hit['title'] or hit['title_ar'],
                        'description': hit['description'] or hit['description_ar'],
                        'filename': hit['filename'],
                        'file_type': hit['file_type'],
                        'category': hit['category'],
                        'author': hit['author'],
                        'status': hit['status'],
                        'status_display': document.get_status_display(),
                        'status_color': document.get_status_color(),
                        'created_at': hit['created_at'],
                        'score': hit.score
                    }
                    filtered_results.append(result_data)
            
            return filtered_results, results.total
    
    def get_suggestions(self, partial_query, limit=10):
        """Get search suggestions based on partial query"""
        suggestions = []
        
        with self.index.searcher() as searcher:
            # Get suggestions from titles
            title_parser = QueryParser('title', self.index.schema)
            title_suggestions = searcher.suggest('title', partial_query, limit=limit//2)
            
            # Get suggestions from Arabic titles
            title_ar_parser = QueryParser('title_ar', self.index.schema)
            title_ar_suggestions = searcher.suggest('title_ar', partial_query, limit=limit//2)
            
            suggestions.extend(title_suggestions)
            suggestions.extend(title_ar_suggestions)
        
        return list(set(suggestions))[:limit]
    
    def rebuild_index(self):
        """Rebuild the entire search index"""
        writer = self.index.writer()
        
        try:
            # Clear existing index
            from whoosh.query import Every
            writer.delete_by_query(Every())
            
            # Add all documents (include all statuses)
            documents = Document.query.all()
            
            for document in documents:
                self._add_document_to_writer(writer, document)
            
            writer.commit()
            current_app.logger.info(f"Search index rebuilt with {len(documents)} documents")
            return True
            
        except Exception as e:
            writer.cancel()
            current_app.logger.error(f"Error rebuilding search index: {str(e)}")
            return False
    
    def _add_document_to_writer(self, writer, document):
        """Add document to writer (used in bulk operations)"""
        content_text = self._extract_text_content(document)
        tags = ','.join([tag.name for tag in document.tags])
        
        writer.add_document(
            id=str(document.id),
            title=document.title or '',
            title_ar=document.title or '',  # Use title for both fields
            description=document.description or '',
            description_ar=document.description or '',  # Use description for both fields
            content=content_text,
            filename=document.original_filename or document.filename or '',
            file_type=document.file_type or '',
            category=document.category.get_display_name() if document.category else '',
            tags=tags,
            author=document.author.get_full_name() if document.author else '',
            status=document.status,
            created_at=document.created_at,
            updated_at=document.updated_at
        )
    
    def _extract_text_content(self, document):
        """Extract text content from document file"""
        if not document.file_path or not os.path.exists(document.file_path):
            return document.content_text or ''
        
        try:
            # Get file extension from filename or file_path
            if document.filename:
                file_extension = os.path.splitext(document.filename)[1].lower()
            elif document.file_path:
                file_extension = os.path.splitext(document.file_path)[1].lower()
            else:
                return document.content_text or ''
            
            if file_extension == '.pdf':
                return self._extract_pdf_text(document.file_path)
            elif file_extension in ['.doc', '.docx']:
                return self._extract_word_text(document.file_path)
            elif file_extension == '.txt':
                return self._extract_txt_text(document.file_path)
            else:
                return document.content_text or ''
                
        except Exception as e:
            current_app.logger.error(f"Error extracting text from {document.file_path}: {str(e)}")
            return document.content_text or ''
    
    def _extract_pdf_text(self, file_path):
        """Extract text from PDF file"""
        try:
            import PyPDF2
            text = ''
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + '\n'
            return text
        except ImportError:
            current_app.logger.warning("PyPDF2 not installed, cannot extract PDF text")
            return ''
        except Exception as e:
            current_app.logger.error(f"Error extracting PDF text: {str(e)}")
            return ''
    
    def _extract_word_text(self, file_path):
        """Extract text from Word document"""
        try:
            from docx import Document as DocxDocument
            doc = DocxDocument(file_path)
            text = ''
            for paragraph in doc.paragraphs:
                text += paragraph.text + '\n'
            return text
        except ImportError:
            current_app.logger.warning("python-docx not installed, cannot extract Word text")
            return ''
        except Exception as e:
            current_app.logger.error(f"Error extracting Word text: {str(e)}")
            return ''
    
    def _extract_txt_text(self, file_path):
        """Extract text from text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            current_app.logger.error(f"Error extracting text file: {str(e)}")
            return ''
    
    def _can_user_access_document(self, document, user):
        """Check if user can access document based on permissions"""
        if not user:
            # If no user provided, allow access to public documents only
            return document.access_level == 'public' if hasattr(document, 'access_level') else True
        
        # Admin can access all documents
        if user.is_admin:
            return True
        
        # Document author can always access their documents
        if document.author_id == user.id:
            return True
        
        # Check document access level
        if document.access_level == 'public':
            return True
        elif document.access_level == 'internal' and user.is_authenticated:
            return True
        elif document.access_level in ['confidential', 'secret']:
            # Only specific roles can access confidential/secret documents
            return user.can('view_confidential_documents')
        
        return False

_search_manager = None

def get_search_manager():
    """Get or create the search manager instance"""
    global _search_manager
    if _search_manager is None:
        _search_manager = SearchManager()
    return _search_manager

def search_documents(query="", category_id=None, file_type=None, date_from=None,
                    date_to=None, status=None, user=None, page=1, per_page=20):
    """Convenience function for searching documents"""
    return get_search_manager().search_documents(
        query, category_id, file_type, date_from, date_to, status, user, page, per_page
    )


