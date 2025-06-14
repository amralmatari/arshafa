from app import create_app
from app.models.document import Document

app = create_app('development')

with app.app_context():
    print("🎯 اختبار شامل نهائي لأنواع الملفات:")
    print("=" * 60)
    
    # Get all documents
    documents = Document.query.all()
    
    print(f"📄 إجمالي الوثائق: {len(documents)}")
    
    # Test each document
    print(f"\n📋 اختبار كل وثيقة:")
    print("-" * 50)
    
    success_count = 0
    problem_count = 0
    
    with app.test_request_context():
        filter_func = app.jinja_env.filters.get('file_type_display')
        
        for doc in documents:
            print(f"\n📄 الوثيقة {doc.id}:")
            print(f"   العنوان: {doc.title}")
            print(f"   نوع الملف: '{doc.file_type}'")
            print(f"   اسم الملف: '{doc.original_filename}'")
            
            if filter_func:
                display = filter_func(doc.file_type)
                print(f"   العرض: '{display}'")
                
                if display == "غير محدد":
                    problem_count += 1
                    print(f"   ❌ مشكلة: يظهر 'غير محدد'")
                    
                    # Try to fix using the new method
                    print(f"   🔧 محاولة الإصلاح...")
                    doc.ensure_file_type()
                    
                    # Test again
                    new_display = filter_func(doc.file_type)
                    print(f"   🧪 بعد الإصلاح: '{doc.file_type}' → '{new_display}'")
                    
                    if new_display != "غير محدد":
                        print(f"   ✅ تم الإصلاح!")
                        success_count += 1
                        problem_count -= 1
                        
                        # Save the fix
                        from app import db
                        db.session.commit()
                        
                        # Update search index
                        from app.utils.search import get_search_manager
                        search_manager = get_search_manager()
                        search_manager.update_document(doc)
                    else:
                        print(f"   ❌ لم يتم الإصلاح")
                else:
                    success_count += 1
                    print(f"   ✅ يعرض بشكل صحيح")
            else:
                print(f"   ❌ الـ filter غير موجود")
                problem_count += 1
    
    # Group by file type
    print(f"\n📊 تجميع حسب نوع الملف:")
    print("-" * 40)
    
    file_types = {}
    for doc in documents:
        file_type = doc.file_type or 'فارغ'
        if file_type not in file_types:
            file_types[file_type] = []
        file_types[file_type].append(doc)
    
    with app.test_request_context():
        filter_func = app.jinja_env.filters.get('file_type_display')
        
        for file_type, docs in file_types.items():
            display = filter_func(file_type) if filter_func else file_type
            count = len(docs)
            status = "✅" if display != "غير محدد" else "❌"
            
            print(f"{status} {file_type:8} → {display:15} ({count} وثيقة)")
    
    # Final statistics
    print(f"\n📈 الإحصائيات النهائية:")
    print("-" * 30)
    print(f"   ✅ وثائق تعرض بشكل صحيح: {success_count}")
    print(f"   ❌ وثائق تحتاج إصلاح: {problem_count}")
    print(f"   📊 نسبة النجاح: {(success_count/len(documents)*100):.1f}%")
    
    if problem_count == 0:
        print(f"\n🎉 تم حل جميع مشاكل عرض أنواع الملفات!")
        print(f"✨ جميع الوثائق تعرض أنواع الملفات بأسماء واضحة")
        
        # Test specific scenarios
        print(f"\n🧪 اختبار سيناريوهات محددة:")
        print("-" * 40)
        
        # Test DOCX files specifically
        docx_docs = [doc for doc in documents if doc.file_type == 'docx']
        print(f"📝 ملفات DOCX: {len(docx_docs)}")
        for doc in docx_docs:
            with app.test_request_context():
                display = filter_func(doc.file_type)
                print(f"   • {doc.title[:30]:30} → {display}")
        
        # Test Excel files
        excel_docs = [doc for doc in documents if doc.file_type in ['xlsx', 'xls']]
        print(f"📊 ملفات Excel: {len(excel_docs)}")
        for doc in excel_docs:
            with app.test_request_context():
                display = filter_func(doc.file_type)
                print(f"   • {doc.title[:30]:30} → {display}")
        
    else:
        print(f"\n⚠️ لا تزال هناك {problem_count} وثيقة تحتاج إصلاح يدوي")
    
    print(f"\n🔗 روابط الاختبار:")
    print("   تفاصيل الوثائق:")
    for doc in documents[:3]:  # Show first 3 documents
        print(f"     • http://127.0.0.1:5000/documents/view/{doc.id}")
    
    print("   نتائج البحث:")
    print("     • http://127.0.0.1:5000/search?search_submitted=1")
    print("     • http://127.0.0.1:5000/search?search_submitted=1&type=docx")
    print("     • http://127.0.0.1:5000/search?search_submitted=1&type=xlsx")
    
    print(f"\n" + "=" * 60)
