"""
Document management routes
"""

import os
import mimetypes
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file, jsonify, Response
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models.document import Document, DocumentVersion, Category, DocumentStatus
from app.models.audit import AuditLog, AuditAction
from app.models.user import User
from app.forms.document import DocumentForm
from app import db
from app.utils.search import get_search_manager
from app.utils.date_utils import localize_datetime

bp = Blueprint('documents', __name__)

@bp.route('/')
@login_required
def index():
    """Document index page - redirects to list_documents"""
    return redirect(url_for('documents.list_documents'))

@bp.route('/list')
@login_required
def list_documents():
    """List all documents the user has access to"""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['DOCUMENTS_PER_PAGE']

    # Debug logging
    current_app.logger.debug(f"Raw request args: {dict(request.args)}")

    # Initialize filter variables
    main_category_id = None
    sub_category_1_id = None
    sub_category_2_id = None
    sub_category_3_id = None
    category_id = None  # Keep for backward compatibility
    doc_type = None
    author_id = None
    search_query = None
    sort_by = None
    start_date = None
    end_date = None

    # Only process filters if there are query parameters
    if request.args:
        # Get hierarchical category filter parameters
        main_category_id = request.args.get('main_category', type=int)
        sub_category_1_id = request.args.get('sub_category_1', type=int)
        sub_category_2_id = request.args.get('sub_category_2', type=int)
        sub_category_3_id = request.args.get('sub_category_3', type=int)

        # Get legacy category parameter for backward compatibility
        category_id = request.args.get('category', type=int)

        doc_type = request.args.get('doc_type')
        if doc_type is not None:
            doc_type = doc_type.strip()
            if not doc_type:  # If empty string, set to None
                doc_type = None

        author_id = request.args.get('author', type=int)

        search_query = request.args.get('search')
        if search_query is not None:
            search_query = search_query.strip()
            if not search_query:  # If empty string, set to None
                search_query = None

        # Get sort parameter
        sort_by = request.args.get('sort', 'newest')

        # Get date filter parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        time_filter = request.args.get('time_filter')
    else:
        current_app.logger.debug("No query parameters - all filters are None")
        sort_by = 'newest'  # Default sort
        start_date = None
        end_date = None
        time_filter = None

    current_app.logger.debug(f"Filter values - category: {category_id}, doc_type: {doc_type}, author: {author_id}, search: {search_query}, sort: {sort_by}")

    # Basic query for documents with joins for filtering
    query = db.session.query(Document).join(User, Document.author_id == User.id)

    # Apply category filters to query
    # Determine the final category to filter by
    final_category_id = None

    # Priority: most specific category selected
    if sub_category_3_id:
        final_category_id = sub_category_3_id
    elif sub_category_2_id:
        final_category_id = sub_category_2_id
    elif sub_category_1_id:
        final_category_id = sub_category_1_id
    elif main_category_id:
        # If only main category is selected, get all documents in its subcategories
        main_category = Category.query.get(main_category_id)
        if main_category:
            # Get all descendant category IDs
            def get_all_descendant_ids(category):
                descendant_ids = []
                for child in category.children:
                    descendant_ids.append(child.id)
                    descendant_ids.extend(get_all_descendant_ids(child))
                return descendant_ids

            descendant_ids = get_all_descendant_ids(main_category)
            if descendant_ids:
                query = query.filter(Document.category_id.in_(descendant_ids))
    elif category_id:  # Backward compatibility
        final_category_id = category_id

    # Apply specific category filter if we have one
    if final_category_id:
        query = query.filter(Document.category_id == final_category_id)

    if doc_type:
        # Handle multiple extensions (comma-separated)
        if ',' in doc_type:
            extensions = [ext.strip() for ext in doc_type.split(',')]
            query = query.filter(Document.file_type.in_(extensions))
        else:
            query = query.filter(Document.file_type == doc_type)

    if author_id:
        query = query.filter(Document.author_id == author_id)

    if search_query:
        search_filter = f"%{search_query}%"
        query = query.filter(
            db.or_(
                Document.title.ilike(search_filter),
                Document.description.ilike(search_filter)
            )
        )

    # Apply time filters (quick filters and custom date ranges)
    if time_filter:
        from datetime import datetime, timedelta
        today = datetime.now().date()

        if time_filter == 'daily':
            # Filter for today only
            query = query.filter(db.func.date(Document.created_at) == today)
        elif time_filter == 'monthly':
            # Filter for current month
            start_of_month = today.replace(day=1)
            if today.month == 12:
                end_of_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_of_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            query = query.filter(
                db.and_(
                    db.func.date(Document.created_at) >= start_of_month,
                    db.func.date(Document.created_at) <= end_of_month
                )
            )
        elif time_filter == 'yearly':
            # Filter for current year
            start_of_year = today.replace(month=1, day=1)
            end_of_year = today.replace(month=12, day=31)
            query = query.filter(
                db.and_(
                    db.func.date(Document.created_at) >= start_of_year,
                    db.func.date(Document.created_at) <= end_of_year
                )
            )
    elif start_date or end_date:
        # Apply custom date filters (enhanced to work with single dates too)
        from datetime import datetime
        try:
            if start_date and end_date:
                # Both dates provided - filter range
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(
                    db.and_(
                        db.func.date(Document.created_at) >= start_date_obj,
                        db.func.date(Document.created_at) <= end_date_obj
                    )
                )
            elif start_date:
                # Only start date - filter from this date onwards
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(db.func.date(Document.created_at) >= start_date_obj)
            elif end_date:
                # Only end date - filter up to this date
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(db.func.date(Document.created_at) <= end_date_obj)
        except ValueError:
            # Invalid date format, ignore filter
            pass

    # Apply sorting
    if sort_by == 'newest':
        query = query.order_by(Document.updated_at.desc())
    elif sort_by == 'file_type':
        query = query.order_by(Document.file_type.asc(), Document.title.asc())
    elif sort_by == 'status':
        query = query.order_by(Document.status.asc(), Document.title.asc())
    elif sort_by == 'author':
        query = query.order_by(User.first_name.asc(), User.last_name.asc(), Document.title.asc())
    elif sort_by == 'title':
        query = query.order_by(Document.title.asc())
    else:
        # Default to newest
        query = query.order_by(Document.updated_at.desc())

    # Get documents with pagination
    documents = query.paginate(page=page, per_page=per_page, error_out=False)

    # Get categories for hierarchical filters
    main_categories = Category.query.filter_by(parent_id=None).all()

    # Get all categories for backward compatibility
    categories = db.session.query(Category).all()

    # Get all document types for the filter dropdown
    doc_types_raw = db.session.query(Document.file_type).distinct().filter(
        Document.file_type.isnot(None)
    ).all()
    doc_types_raw = [dt[0] for dt in doc_types_raw if dt[0]]  # Extract values and filter None

    # Create document types list for dropdown
    doc_types = []

    # Only show image types if there's an active image filter
    show_images = False
    if doc_type:
        image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff']
        if ',' in doc_type:
            # Multiple extensions in filter
            filter_extensions = [ext.strip() for ext in doc_type.split(',')]
            show_images = any(ext in image_extensions for ext in filter_extensions)
        else:
            # Single extension in filter
            show_images = doc_type in image_extensions

    current_app.logger.debug(f"Show images in dropdown: {show_images}")

    # Group and add document types
    doc_types_grouped = {}
    for file_type in doc_types_raw:
        if file_type in ['doc', 'docx']:
            if 'word' not in doc_types_grouped:
                doc_types_grouped['word'] = []
            doc_types_grouped['word'].append(file_type)
        elif file_type in ['xls', 'xlsx']:
            if 'excel' not in doc_types_grouped:
                doc_types_grouped['excel'] = []
            doc_types_grouped['excel'].append(file_type)
        elif file_type in ['ppt', 'pptx']:
            if 'powerpoint' not in doc_types_grouped:
                doc_types_grouped['powerpoint'] = []
            doc_types_grouped['powerpoint'].append(file_type)
        elif file_type in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff']:
            if 'image' not in doc_types_grouped:
                doc_types_grouped['image'] = []
            doc_types_grouped['image'].append(file_type)
        else:
            # For other types, keep them as individual entries
            doc_types_grouped[file_type] = [file_type]

    # Add types to dropdown in preferred order
    preferred_order = ['pdf', 'word', 'excel', 'powerpoint', 'image', 'txt']

    for group_name in preferred_order:
        if group_name in doc_types_grouped:
            # Skip image group if no image filter is applied
            if group_name == 'image' and not show_images:
                continue

            extensions = doc_types_grouped[group_name]
            if group_name == 'word':
                doc_types.append({
                    'value': ','.join(extensions),
                    'display': f"📝 Word ({', '.join(extensions).upper()})",
                    'extensions': extensions
                })
            elif group_name == 'excel':
                doc_types.append({
                    'value': ','.join(extensions),
                    'display': f"📊 Excel ({', '.join(extensions).upper()})",
                    'extensions': extensions
                })
            elif group_name == 'powerpoint':
                doc_types.append({
                    'value': ','.join(extensions),
                    'display': f"📈 PowerPoint ({', '.join(extensions).upper()})",
                    'extensions': extensions
                })
            elif group_name == 'image':
                doc_types.append({
                    'value': ','.join(extensions),
                    'display': f"🖼️ صورة ({', '.join(extensions).upper()})",
                    'extensions': extensions
                })
            elif group_name == 'pdf':
                doc_types.append({
                    'value': 'pdf',
                    'display': "📄 PDF",
                    'extensions': ['pdf']
                })
            elif group_name == 'txt':
                doc_types.append({
                    'value': 'txt',
                    'display': "📄 نص (TXT)",
                    'extensions': ['txt']
                })

    # Add remaining types not in preferred order
    for group_name, extensions in doc_types_grouped.items():
        if group_name not in preferred_order:
            doc_types.append({
                'value': group_name,
                'display': f"📎 {group_name.upper()}",
                'extensions': [group_name]
            })

    # Get all authors for the filter dropdown
    authors = db.session.query(User.id, User.username, User.first_name, User.last_name).join(
        Document, User.id == Document.author_id
    ).distinct().all()

    return render_template('documents/list.html',
                          documents=documents,
                          categories=categories,
                          main_categories=main_categories,
                          doc_types=doc_types,
                          authors=authors,
                          current_category=category_id,  # Backward compatibility
                          current_main_category=main_category_id,
                          current_sub_category_1=sub_category_1_id,
                          current_sub_category_2=sub_category_2_id,
                          current_sub_category_3=sub_category_3_id,
                          current_doc_type=doc_type,
                          current_author=author_id,
                          current_search=search_query,
                          current_sort=sort_by,
                          current_start_date=start_date,
                          current_end_date=end_date,
                          current_time_filter=time_filter)

@bp.route('/api/subcategories/<int:parent_id>')
@login_required
def get_subcategories(parent_id):
    """Get subcategories for a given parent category (AJAX endpoint)"""
    try:
        subcategories = Category.query.filter_by(parent_id=parent_id).all()
        subcategories_data = []

        for subcategory in subcategories:
            subcategories_data.append({
                'id': subcategory.id,
                'name': subcategory.get_display_name()
            })

        return jsonify({
            'success': True,
            'subcategories': subcategories_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/view/<int:id>')
@login_required
def view_document(id):
    """View a single document"""
    document = Document.query.get_or_404(id)

    # تأكد من أن التواريخ لها منطقة زمنية
    if document.created_at and document.created_at.tzinfo is None:
        document.created_at = document.created_at.replace(tzinfo=timezone.utc)

    if document.updated_at and document.updated_at.tzinfo is None:
        document.updated_at = document.updated_at.replace(tzinfo=timezone.utc)

    # Log document view
    AuditLog.log_document_action(
        action=AuditAction.DOCUMENT_VIEW,
        document=document,
        user=current_user,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )

    # Increment view count
    document.view_count += 1
    db.session.commit()

    # Get related documents
    related_documents = Document.query.filter(
        Document.category_id == document.category_id,
        Document.id != document.id
    ).limit(5).all()

    # تحميل الإصدارات مسبقًا
    versions = DocumentVersion.query.filter_by(document_id=document.id).order_by(DocumentVersion.version_number.desc()).all()

    # Get PDF info if it's a PDF file
    pdf_info = None
    if document.file_type == 'pdf' and os.path.exists(document.file_path):
        pdf_info = get_pdf_info(document.file_path)

    return render_template('documents/view.html',
                          document=document,
                          related_documents=related_documents,
                          versions=versions,
                          pdf_info=pdf_info)

@bp.route('/download/<int:id>')
@login_required
def download_document(id):
    """Download a document file"""
    document = Document.query.get_or_404(id)

    # Log document download
    AuditLog.log_document_action(
        action=AuditAction.DOCUMENT_DOWNLOAD,
        document=document,
        user=current_user,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )

    # Increment download count
    document.download_count += 1
    db.session.commit()

    # Get file extension from original filename
    file_ext = os.path.splitext(document.original_filename)[1]

    # تأكد من أن امتداد الملف موجود
    if not file_ext or file_ext == '':
        if document.file_type:
            file_ext = f".{document.file_type}"
        else:
            # تخمين الامتداد من نوع الملف
            mime_type = mimetypes.guess_type(document.file_path)[0]
            if mime_type == 'application/pdf':
                file_ext = '.pdf'
            elif mime_type and 'image' in mime_type:
                file_ext = f".{mime_type.split('/')[-1]}"
            else:
                file_ext = ''

    # Create download filename using document title
    download_filename = f"{document.title}{file_ext}"

    # تسجيل معلومات التنزيل للتصحيح
    current_app.logger.info(f"Downloading file: {document.file_path}")
    current_app.logger.info(f"Original filename: {document.original_filename}")
    current_app.logger.info(f"File extension: {file_ext}")
    current_app.logger.info(f"Download filename: {download_filename}")

    return send_file(document.file_path,
                    download_name=download_filename,
                    as_attachment=True)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_document():
    """Create a new document"""
    # Create form
    form = DocumentForm()

    # Get categories for the hierarchical form
    main_categories = Category.query.filter_by(parent_id=None).all()

    # Set choices for main categories
    form.main_category_id.choices = [(0, '-- اختر الفئة الرئيسية --')] + [(c.id, c.get_display_name()) for c in main_categories]

    # Initialize subcategory choices as empty
    form.sub_category_1_id.choices = [(0, '-- اختر الفئة الفرعية الأولى --')]
    form.sub_category_2_id.choices = [(0, '-- اختر الفئة الفرعية الثانية --')]
    form.sub_category_3_id.choices = [(0, '-- اختر الفئة الفرعية الثالثة --')]
    form.category_id.choices = [(0, '-- اختر الفئة --')]

    # حذف الجزء المتعلق بالعلامات
    # if hasattr(form, 'tags'):
    #     tags = Tag.query.all()
    #     if tags is not None:
    #         form.set_tag_choices(tags)
    #     else:
    #         form.tags.choices = []

    if request.method == 'POST':
        current_app.logger.info("Form submitted")
        current_app.logger.debug(f"Form data: main_category_id={request.form.get('main_category_id')}, sub_category_1_id={request.form.get('sub_category_1_id')}, sub_category_2_id={request.form.get('sub_category_2_id')}, sub_category_3_id={request.form.get('sub_category_3_id')}")
        current_app.logger.debug(f"Form choices before validation: main={form.main_category_id.choices}, sub1={form.sub_category_1_id.choices}, sub2={form.sub_category_2_id.choices}, sub3={form.sub_category_3_id.choices}")

        # إعادة تعيين خيارات الفئات قبل التحقق من صحة النموذج
        main_categories = Category.query.filter_by(parent_id=None).all()
        form.main_category_id.choices = [(0, '-- اختر الفئة الرئيسية --')] + [(c.id, c.get_display_name()) for c in main_categories]

        # إعادة تعيين خيارات الفئات الفرعية بناءً على البيانات المرسلة
        main_category_id = request.form.get('main_category_id', type=int)
        if main_category_id and main_category_id > 0:
            sub_categories_1 = Category.query.filter_by(parent_id=main_category_id).all()
            form.sub_category_1_id.choices = [(0, '-- اختر الفئة الفرعية الأولى --')] + [(c.id, c.get_display_name()) for c in sub_categories_1]

            sub_category_1_id = request.form.get('sub_category_1_id', type=int)
            if sub_category_1_id and sub_category_1_id > 0:
                sub_categories_2 = Category.query.filter_by(parent_id=sub_category_1_id).all()
                form.sub_category_2_id.choices = [(0, '-- اختر الفئة الفرعية الثانية --')] + [(c.id, c.get_display_name()) for c in sub_categories_2]

                sub_category_2_id = request.form.get('sub_category_2_id', type=int)
                if sub_category_2_id and sub_category_2_id > 0:
                    sub_categories_3 = Category.query.filter_by(parent_id=sub_category_2_id).all()
                    form.sub_category_3_id.choices = [(0, '-- اختر الفئة الفرعية الثالثة --')] + [(c.id, c.get_display_name()) for c in sub_categories_3]

        current_app.logger.debug(f"Form choices after validation: main={form.main_category_id.choices}, sub1={form.sub_category_1_id.choices}, sub2={form.sub_category_2_id.choices}, sub3={form.sub_category_3_id.choices}")

        # Check if form validates
        if not form.validate_on_submit():
            current_app.logger.error(f"Form validation errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"خطأ في الحقل {field}: {error}", 'danger')
            return render_template('documents/create.html', form=form)

        # Process form submission
        try:
            current_app.logger.info("Form validated successfully")

            # Handle file upload
            file = form.document_file.data
            if not file:
                flash('يرجى تحديد ملف للوثيقة', 'danger')
                return render_template('documents/create.html', form=form, categories=categories)

            current_app.logger.info(f"File received: {file.filename}")

            # Create secure filename
            filename = secure_filename(file.filename)
            unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"

            # Ensure upload directory exists
            upload_dir = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)

            # Save file
            file_path = os.path.join(upload_dir, unique_filename)
            current_app.logger.info(f"Saving file to: {file_path}")
            file.save(file_path)

            # Verify file was saved
            if not os.path.exists(file_path):
                current_app.logger.error(f"File was not saved to {file_path}")
                flash('فشل في حفظ الملف', 'danger')
                return render_template('documents/create.html', form=form, categories=categories)

            # Get file type and size
            file_ext = os.path.splitext(filename)[1].lower().replace('.', '')
            file_size = os.path.getsize(file_path)

            current_app.logger.info(f"File saved successfully. Type: {file_ext}, Size: {file_size}")

            # Create document
            document = Document(
                title=form.title.data,
                description=form.description.data,
                file_path=file_path,
                original_filename=filename,
                file_type=file_ext,  # تأكد من تعيين نوع الملف
                file_size=file_size,
                status=form.status.data,
                is_confidential=form.is_confidential.data,
                author_id=current_user.id
            )

            # Set category if selected (من النظام الهرمي)
            final_category_id = None

            # تحديد الفئة النهائية من النظام الهرمي
            if form.sub_category_3_id.data and form.sub_category_3_id.data > 0:
                final_category_id = form.sub_category_3_id.data
            elif form.sub_category_2_id.data and form.sub_category_2_id.data > 0:
                final_category_id = form.sub_category_2_id.data
            elif form.sub_category_1_id.data and form.sub_category_1_id.data > 0:
                final_category_id = form.sub_category_1_id.data
            elif form.main_category_id.data and form.main_category_id.data > 0:
                # لا يمكن حفظ الوثيقة في الفئة الرئيسية مباشرة
                # يجب اختيار فئة فرعية
                flash('يرجى اختيار فئة فرعية وليس الفئة الرئيسية فقط', 'warning')
                return render_template('documents/create.html', form=form)

            if final_category_id:
                document.category_id = final_category_id

            # Set expiry date if provided
            if form.expiry_date.data:
                document.expiry_date = form.expiry_date.data

            current_app.logger.info(f"Document object created: {document.title}")

            # Add document to database
            db.session.add(document)
            db.session.flush()  # Get document ID

            current_app.logger.info(f"Document added to session with ID: {document.id}")

            # Create initial document version
            version = DocumentVersion(
                document_id=document.id,
                version_number='1.0',  # استخدام تنسيق ثابت للإصدار الأول
                filename=filename,
                file_path=file_path,
                file_size=file_size,
                created_by_id=current_user.id,
                comment='الإصدار الأولي'
            )

            db.session.add(version)

            # Ensure file type is set before committing
            document.ensure_file_type()

            # Commit changes
            db.session.commit()

            # Log document creation
            AuditLog.log_document_action(
                action=AuditAction.DOCUMENT_CREATE,
                document=document,
                user=current_user,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )

            # Add to search index
            search_manager = get_search_manager()
            if search_manager:
                search_manager.add_document(document)

            flash('تم إنشاء الوثيقة بنجاح', 'success')
            current_app.logger.info(f"Document created successfully, redirecting to view page for document {document.id}")

            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': 'تم إنشاء الوثيقة بنجاح',
                    'redirect_url': url_for('documents.view_document', id=document.id)
                })

            return redirect(url_for('documents.view_document', id=document.id))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating document: {str(e)}")
            flash(f'حدث خطأ أثناء إنشاء الوثيقة: {str(e)}', 'danger')
            # Try to delete the uploaded file if it exists
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
                current_app.logger.info(f"Deleted file {file_path} after error")

    # Show create form
    return render_template('documents/create.html',
                          form=form,
                          categories=categories)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_document(id):
    """Edit an existing document"""
    document = Document.query.get_or_404(id)

    # Check if user has permission to edit
    if not (current_user.can('edit_document') or current_user.id == document.author_id):
        flash('ليس لديك صلاحية لتعديل هذه الوثيقة', 'danger')
        return redirect(url_for('documents.view_document', id=document.id))

    # Create form
    form = DocumentForm()

    # Get categories for the hierarchical form
    main_categories = Category.query.filter_by(parent_id=None).all()

    # Set choices for main categories
    form.main_category_id.choices = [(0, '-- اختر الفئة الرئيسية --')] + [(c.id, c.get_display_name()) for c in main_categories]

    # Initialize subcategory choices as empty
    form.sub_category_1_id.choices = [(0, '-- اختر الفئة الفرعية الأولى --')]
    form.sub_category_2_id.choices = [(0, '-- اختر الفئة الفرعية الثانية --')]
    form.sub_category_3_id.choices = [(0, '-- اختر الفئة الفرعية الثالثة --')]
    form.category_id.choices = [(0, '-- اختر الفئة --')]

    if request.method == 'POST':
        # إعادة تعيين خيارات الفئات قبل التحقق من صحة النموذج
        main_categories = Category.query.filter_by(parent_id=None).all()
        form.main_category_id.choices = [(0, '-- اختر الفئة الرئيسية --')] + [(c.id, c.get_display_name()) for c in main_categories]

        # إعادة تعيين خيارات الفئات الفرعية بناءً على البيانات المرسلة
        main_category_id = request.form.get('main_category_id', type=int)
        if main_category_id and main_category_id > 0:
            sub_categories_1 = Category.query.filter_by(parent_id=main_category_id).all()
            form.sub_category_1_id.choices = [(0, '-- اختر الفئة الفرعية الأولى --')] + [(c.id, c.get_display_name()) for c in sub_categories_1]

            sub_category_1_id = request.form.get('sub_category_1_id', type=int)
            if sub_category_1_id and sub_category_1_id > 0:
                sub_categories_2 = Category.query.filter_by(parent_id=sub_category_1_id).all()
                form.sub_category_2_id.choices = [(0, '-- اختر الفئة الفرعية الثانية --')] + [(c.id, c.get_display_name()) for c in sub_categories_2]

                sub_category_2_id = request.form.get('sub_category_2_id', type=int)
                if sub_category_2_id and sub_category_2_id > 0:
                    sub_categories_3 = Category.query.filter_by(parent_id=sub_category_2_id).all()
                    form.sub_category_3_id.choices = [(0, '-- اختر الفئة الفرعية الثالثة --')] + [(c.id, c.get_display_name()) for c in sub_categories_3]

        if form.validate_on_submit():
            # Update document data
            document.title = form.title.data
            document.description = form.description.data
            document.status = form.status.data
            document.is_confidential = form.is_confidential.data

            # Update category if selected (من النظام الهرمي)
            final_category_id = None

            # تحديد الفئة النهائية من النظام الهرمي
            if form.sub_category_3_id.data and form.sub_category_3_id.data > 0:
                final_category_id = form.sub_category_3_id.data
            elif form.sub_category_2_id.data and form.sub_category_2_id.data > 0:
                final_category_id = form.sub_category_2_id.data
            elif form.sub_category_1_id.data and form.sub_category_1_id.data > 0:
                final_category_id = form.sub_category_1_id.data
            elif form.main_category_id.data and form.main_category_id.data > 0:
                # لا يمكن حفظ الوثيقة في الفئة الرئيسية مباشرة
                # يجب اختيار فئة فرعية
                flash('يرجى اختيار فئة فرعية وليس الفئة الرئيسية فقط', 'warning')
                return render_template('documents/edit.html', form=form, document=document)

            if final_category_id:
                document.category_id = final_category_id
            else:
                document.category_id = None

            # Update expiry date if provided
            if form.expiry_date.data:
                document.expiry_date = form.expiry_date.data
            else:
                document.expiry_date = None

            # Calculate new version number for any update
            latest_version = DocumentVersion.query.filter_by(document_id=document.id).order_by(DocumentVersion.version_number.desc()).first()
            if latest_version:
                try:
                    # Try to parse version as float and increment
                    version_num = float(latest_version.version_number)
                    # تنسيق رقم الإصدار بحيث لا يحتوي على أصفار زائدة
                    new_version_num = version_num + 0.1
                    # استخدام تنسيق رقمي مناسب
                    if new_version_num == int(new_version_num):
                        # إذا كان الرقم صحيحًا، لا نضيف أصفار بعد العلامة العشرية
                        new_version = str(int(new_version_num))
                    else:
                        # إذا كان الرقم عشريًا، نستخدم رقم عشري واحد فقط
                        new_version = f"{int(new_version_num)}.{int((new_version_num % 1) * 10)}"
                except ValueError:
                    # If parsing fails, just append .1
                    new_version = f"{latest_version.version_number}.1"
            else:
                new_version = "1.0"

            # Handle file upload if a new file is provided
            file = form.document_file.data
            if file and file.filename:
                current_app.logger.info(f"New file received: {file.filename}")

                # Create secure filename
                filename = secure_filename(file.filename)
                unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"

                # Ensure upload directory exists
                upload_dir = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_dir, exist_ok=True)

                # Save file
                file_path = os.path.join(upload_dir, unique_filename)
                current_app.logger.info(f"Saving file to: {file_path}")
                file.save(file_path)

                # Verify file was saved
                if not os.path.exists(file_path):
                    current_app.logger.error(f"File was not saved to {file_path}")
                    flash('فشل في حفظ الملف', 'danger')
                    return render_template('documents/edit.html', form=form, document=document)

                # Get file type and size
                file_ext = os.path.splitext(filename)[1].lower().replace('.', '')
                file_size = os.path.getsize(file_path)

                current_app.logger.info(f"File saved successfully. Type: {file_ext}, Size: {file_size}")

                # Update document file info
                document.file_path = file_path
                document.original_filename = filename
                document.file_type = file_ext
                document.file_size = file_size

                # Create new document version with new file
                version = DocumentVersion(
                    document_id=document.id,
                    version_number=new_version,
                    filename=filename,
                    file_path=file_path,
                    file_size=file_size,
                    created_by_id=current_user.id,
                    comment=form.version_comment.data or 'تحديث الملف'
                )
            else:
                # Create new version even without file change (metadata update)
                version = DocumentVersion(
                    document_id=document.id,
                    version_number=new_version,
                    filename=document.original_filename,
                    file_path=document.file_path,
                    file_size=document.file_size,
                    created_by_id=current_user.id,
                    comment=form.version_comment.data or 'تحديث البيانات الوصفية'
                )

            db.session.add(version)

            # Update document
            document.updated_at = datetime.now()

            # Ensure file type is set
            document.ensure_file_type()

            db.session.commit()

            # Update search index
            try:
                from app.utils.search import get_search_manager
                search_manager = get_search_manager()
                if search_manager:
                    search_manager.update_document(document)
                    current_app.logger.info(f"Search index updated for document {document.id}")
            except Exception as e:
                current_app.logger.error(f"Error updating search index: {str(e)}")

            # Log document update
            AuditLog.log_document_action(
                action=AuditAction.DOCUMENT_UPDATE,
                document=document,
                user=current_user,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )

            flash('تم تحديث الوثيقة بنجاح', 'success')
            current_app.logger.info(f"Document {document.id} updated successfully, redirecting to view page")

            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': 'تم تحديث الوثيقة بنجاح',
                    'redirect_url': url_for('documents.view_document', id=document.id)
                })

            return redirect(url_for('documents.view_document', id=document.id))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"خطأ في الحقل {field}: {error}", 'danger')

    # For GET requests, populate form with document data
    if request.method == 'GET':
        form.title.data = document.title
        form.description.data = document.description
        form.category_id.data = document.category_id or 0
        form.status.data = document.status
        form.is_confidential.data = document.is_confidential
        form.expiry_date.data = document.expiry_date

    return render_template('documents/edit.html', form=form, document=document)

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_document(id):
    """Delete a document"""
    document = Document.query.get_or_404(id)

    # Check if user has permission to delete
    if not (current_user.can('delete_document') or current_user.id == document.author_id):
        flash('ليس لديك صلاحية لحذف هذه الوثيقة', 'danger')
        return redirect(url_for('documents.view_document', id=document.id))

    try:
        # Log document deletion
        AuditLog.log_document_action(
            action=AuditAction.DOCUMENT_DELETE,
            document=document,
            user=current_user,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )

        # Remove from search index
        search_manager = get_search_manager()
        if search_manager:
            search_manager.remove_document(document.id)

        # Store file paths to delete after DB transaction
        file_paths = [document.file_path]
        for version in document.versions:
            if version.file_path != document.file_path:  # Avoid duplicates
                file_paths.append(version.file_path)

        # Delete the document (versions will be deleted automatically due to cascade)
        db.session.delete(document)
        db.session.commit()

        # Delete physical files
        for file_path in file_paths:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    current_app.logger.error(f"Error deleting file {file_path}: {str(e)}")

        flash('تم حذف الوثيقة بنجاح.', 'success')
        return redirect(url_for('documents.list_documents'))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting document: {str(e)}")
        flash(f'حدث خطأ أثناء حذف الوثيقة: {str(e)}', 'danger')
        return redirect(url_for('documents.view_document', id=document.id))



@bp.route('/api/category-hierarchy/<int:category_id>')
@login_required
def get_category_hierarchy(category_id):
    """Get the full hierarchy path for a category"""
    category = Category.query.get_or_404(category_id)

    hierarchy = []
    current = category

    # Build hierarchy from current category to root
    while current:
        hierarchy.insert(0, {
            'id': current.id,
            'name': current.get_display_name(),
            'level': len(hierarchy) + 1
        })
        current = current.parent

    return jsonify(hierarchy)

@bp.route('/ajax/delete/<int:id>', methods=['POST'])
@login_required
def delete_document_ajax(id):
    """Delete a document via AJAX"""
    try:
        document = Document.query.get_or_404(id)

        # Check permissions
        if not (current_user.can('delete_document') or current_user.id == document.author_id):
            return jsonify({'success': False, 'message': 'ليس لديك صلاحية لحذف هذه الوثيقة'}), 403

        # Delete the file from filesystem
        if document.file_path and os.path.exists(document.file_path):
            try:
                os.remove(document.file_path)
            except OSError:
                pass  # File might already be deleted

        # Remove from search index
        try:
            from app.services.search import SearchService
            search_service = SearchService()
            search_service.remove_document(document.id)
        except ImportError:
            pass  # Search service not available

        # Delete from database
        db.session.delete(document)
        db.session.commit()

        # Log the action
        from app.models.audit import AuditLog
        AuditLog.log_action(
            user=current_user,
            action='document_delete',
            details=f'حذف الوثيقة: {document.title}',
            success=True
        )

        return jsonify({'success': True, 'message': 'تم حذف الوثيقة بنجاح'})

    except Exception as e:
        current_app.logger.error(f"Error deleting document {id}: {str(e)}")
        return jsonify({'success': False, 'message': 'حدث خطأ أثناء حذف الوثيقة'}), 500

@bp.route('/bulk-delete', methods=['POST'])
@login_required
def bulk_delete_documents():
    """Delete multiple documents via AJAX"""
    try:
        # Try to get document_ids from form data or JSON
        document_ids = request.form.getlist('document_ids')
        if not document_ids and request.is_json:
            data = request.get_json()
            document_ids = data.get('document_ids', [])

        current_app.logger.debug(f"Bulk delete request: document_ids={document_ids}")
        current_app.logger.debug(f"Request form data: {request.form}")
        current_app.logger.debug(f"Request is_json: {request.is_json}")

        if not document_ids:
            return jsonify({'success': False, 'message': 'لم يتم تحديد أي وثائق للحذف'}), 400

        deleted_count = 0
        failed_count = 0

        for doc_id in document_ids:
            try:
                document = Document.query.get(doc_id)
                if not document:
                    failed_count += 1
                    continue

                # Check permissions
                if not (current_user.can('delete_document') or current_user.id == document.author_id):
                    failed_count += 1
                    continue

                # Delete the file from filesystem
                if document.file_path and os.path.exists(document.file_path):
                    try:
                        os.remove(document.file_path)
                    except OSError:
                        pass  # File might already be deleted

                # Remove from search index
                try:
                    from app.services.search import SearchService
                    search_service = SearchService()
                    search_service.remove_document(document.id)
                except ImportError:
                    pass  # Search service not available

                # Delete from database
                db.session.delete(document)
                deleted_count += 1

                # Log the action
                from app.models.audit import AuditLog
                AuditLog.log_action(
                    user=current_user,
                    action='document_delete',
                    details=f'حذف الوثيقة: {document.title}',
                    success=True
                )

            except Exception as e:
                current_app.logger.error(f"Error deleting document {doc_id}: {str(e)}")
                failed_count += 1

        db.session.commit()

        if deleted_count > 0:
            message = f'تم حذف {deleted_count} وثيقة بنجاح'
            if failed_count > 0:
                message += f' وفشل حذف {failed_count} وثيقة'
            return jsonify({'success': True, 'message': message, 'deleted_count': deleted_count})
        else:
            return jsonify({'success': False, 'message': 'فشل في حذف جميع الوثائق المحددة'}), 400

    except Exception as e:
        current_app.logger.error(f"Error in bulk delete: {str(e)}")
        return jsonify({'success': False, 'message': 'حدث خطأ أثناء حذف الوثائق'}), 500

@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Alias for create_document"""
    return create_document()

@bp.route('/preview/<int:id>')
@login_required
def preview_document(id):
    """Preview a document"""
    document = Document.query.get_or_404(id)

    # Check if file exists
    if not os.path.exists(document.file_path):
        flash('الملف غير موجود', 'danger')
        return redirect(url_for('documents.view_document', id=document.id))

    # Log document preview
    AuditLog.log_document_action(
        action=AuditAction.DOCUMENT_VIEW,
        document=document,
        user=current_user,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )

    # For images and PDFs, we can directly serve the file for preview (not download)
    if document.file_type in ['pdf', 'jpg', 'jpeg', 'png', 'gif']:
        # Set appropriate mimetype for proper browser handling
        if document.file_type == 'pdf':
            mimetype = 'application/pdf'
        elif document.file_type in ['jpg', 'jpeg']:
            mimetype = 'image/jpeg'
        elif document.file_type == 'png':
            mimetype = 'image/png'
        elif document.file_type == 'gif':
            mimetype = 'image/gif'
        else:
            mimetype = None



        # Use send_file with proper parameters to prevent download
        return send_file(
            document.file_path,
            mimetype=mimetype,
            as_attachment=False,
            download_name=None
        )

    # For other file types, redirect to download
    return redirect(url_for('documents.download_document', id=document.id))

@bp.route('/pdf-viewer/<int:id>')
@login_required
def pdf_viewer(id):
    """PDF viewer using PDF.js"""
    document = Document.query.get_or_404(id)

    # Check if file exists and is PDF
    if not os.path.exists(document.file_path) or document.file_type != 'pdf':
        flash('ملف PDF غير موجود', 'danger')
        return redirect(url_for('documents.view_document', id=document.id))

    # Get PDF info
    pdf_info = get_pdf_info(document.file_path)

    return render_template('documents/pdf_viewer.html',
                          document=document,
                          pdf_info=pdf_info)

@bp.route('/pdf-thumbnail/<int:id>')
@login_required
def pdf_thumbnail(id):
    """Generate PDF thumbnail"""
    document = Document.query.get_or_404(id)

    # Check if file exists and is PDF
    if not os.path.exists(document.file_path) or document.file_type != 'pdf':
        # Return a default PDF icon image
        return redirect(url_for('static', filename='images/pdf-icon.png'))

    # For now, return a simple response indicating PDF
    # In a production environment, you might want to generate actual thumbnails
    from flask import make_response
    response = make_response()
    response.headers['Content-Type'] = 'image/svg+xml'

    svg_content = '''
    <svg xmlns="http://www.w3.org/2000/svg" width="200" height="250" viewBox="0 0 200 250">
        <rect width="200" height="250" fill="#f8f9fa" stroke="#dee2e6" stroke-width="2"/>
        <text x="100" y="100" text-anchor="middle" font-family="Arial" font-size="16" fill="#6c757d">PDF</text>
        <text x="100" y="130" text-anchor="middle" font-family="Arial" font-size="12" fill="#6c757d">معاينة غير متاحة</text>
        <text x="100" y="150" text-anchor="middle" font-family="Arial" font-size="12" fill="#6c757d">انقر للعرض</text>
    </svg>
    '''

    response.data = svg_content
    return response

@bp.route('/download-version/<int:id>')
@login_required
def download_version(id):
    """Download a specific version of a document"""
    version = DocumentVersion.query.get_or_404(id)
    document = version.document

    # Check if file exists
    if not os.path.exists(version.file_path):
        flash('الملف غير موجود', 'danger')
        return redirect(url_for('documents.view_document', id=document.id))

    # Log version download
    AuditLog.log_document_action(
        action=AuditAction.DOCUMENT_VERSION_DOWNLOAD,
        document=document,
        user=current_user,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )

    # Get file extension from original filename
    file_ext = os.path.splitext(version.filename)[1]

    # تأكد من أن امتداد الملف موجود
    if not file_ext or file_ext == '':
        if document.file_type:
            file_ext = f".{document.file_type}"
        else:
            # تخمين الامتداد من نوع الملف
            mime_type = mimetypes.guess_type(version.file_path)[0]
            if mime_type == 'application/pdf':
                file_ext = '.pdf'
            elif mime_type and 'image' in mime_type:
                file_ext = f".{mime_type.split('/')[-1]}"
            else:
                file_ext = ''

    # Create download filename
    download_filename = f"{document.title}_v{version.version_number}{file_ext}"

    return send_file(version.file_path,
                    download_name=download_filename,
                    as_attachment=True)

def get_pdf_info(file_path):
    """استخراج معلومات ملف PDF"""
    info = {
        'pages': 0,
        'size_mb': 0,
        'title': '',
        'author': '',
        'creation_date': None
    }

    try:
        # Get file size
        file_size = os.path.getsize(file_path)
        info['size_mb'] = round(file_size / (1024 * 1024), 2)

        # Try to extract PDF metadata
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                info['pages'] = len(pdf_reader.pages)

                # Get metadata if available
                if pdf_reader.metadata:
                    info['title'] = pdf_reader.metadata.get('/Title', '')
                    info['author'] = pdf_reader.metadata.get('/Author', '')
                    creation_date = pdf_reader.metadata.get('/CreationDate')
                    if creation_date:
                        info['creation_date'] = str(creation_date)

        except ImportError:
            current_app.logger.warning("PyPDF2 not installed, cannot extract PDF metadata")
        except Exception as e:
            current_app.logger.error(f"Error extracting PDF metadata: {str(e)}")

    except Exception as e:
        current_app.logger.error(f"Error getting PDF info: {str(e)}")

    return info















