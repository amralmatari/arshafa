#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to create sample documents for testing
Creates 50 diverse documents with different types, statuses, and authors
Distributes them across subcategories
"""

import os
import sys
import random
from datetime import datetime, timedelta

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.document import Document, DocumentStatus, Category
from app.models.user import User

def create_sample_documents():
    """Create 50 sample documents with diverse properties"""
    
    app = create_app('development')
    with app.app_context():
        print("🚀 بدء إنشاء الوثائق التجريبية...")
        
        # Get all categories (prefer subcategories)
        all_categories = Category.query.all()
        subcategories = [cat for cat in all_categories if cat.parent_id is not None]
        main_categories = [cat for cat in all_categories if cat.parent_id is None]
        
        # Use subcategories if available, otherwise use main categories
        target_categories = subcategories if subcategories else main_categories
        
        if not target_categories:
            print("❌ لا توجد فئات في النظام. يرجى إنشاء فئات أولاً.")
            return
        
        print(f"📁 تم العثور على {len(target_categories)} فئة للتوزيع")
        
        # Get all users for random assignment
        users = User.query.filter_by(is_active=True).all()
        if not users:
            print("❌ لا يوجد مستخدمون في النظام.")
            return
        
        print(f"👥 تم العثور على {len(users)} مستخدم")
        
        # Document types with Arabic names and extensions
        document_types = [
            {'type': 'pdf', 'name_ar': 'تقرير', 'name_en': 'Report', 'extensions': ['.pdf']},
            {'type': 'docx', 'name_ar': 'مذكرة', 'name_en': 'Memo', 'extensions': ['.docx', '.doc']},
            {'type': 'xlsx', 'name_ar': 'جدول بيانات', 'name_en': 'Spreadsheet', 'extensions': ['.xlsx', '.xls']},
            {'type': 'pptx', 'name_ar': 'عرض تقديمي', 'name_en': 'Presentation', 'extensions': ['.pptx', '.ppt']},
            {'type': 'jpg', 'name_ar': 'صورة', 'name_en': 'Image', 'extensions': ['.jpg', '.png', '.gif']},
            {'type': 'txt', 'name_ar': 'ملف نصي', 'name_en': 'Text File', 'extensions': ['.txt']},
            {'type': 'zip', 'name_ar': 'ملف آخر', 'name_en': 'Other File', 'extensions': ['.zip', '.rar']},
        ]
        
        # Document statuses
        statuses = [
            DocumentStatus.DRAFT,
            DocumentStatus.UNDER_REVIEW,
            DocumentStatus.APPROVED,
            DocumentStatus.REJECTED,
            DocumentStatus.ARCHIVED
        ]
        
        # Arabic document titles and descriptions
        arabic_titles = [
            "تقرير الأداء السنوي",
            "خطة التطوير الاستراتيجية",
            "دليل الإجراءات والسياسات",
            "تحليل السوق والمنافسين",
            "تقرير الموارد البشرية",
            "خطة التسويق الرقمي",
            "دراسة الجدوى الاقتصادية",
            "تقرير الأمن والسلامة",
            "خطة إدارة المخاطر",
            "تحليل البيانات المالية",
            "دليل المستخدم",
            "تقرير مراجعة الحسابات",
            "خطة التدريب والتطوير",
            "تحليل رضا العملاء",
            "تقرير الجودة والامتثال",
            "خطة الطوارئ والأزمات",
            "دراسة تحليل التكاليف",
            "تقرير الابتكار والتطوير",
            "خطة التحول الرقمي",
            "تحليل الأداء التشغيلي"
        ]
        
        arabic_descriptions = [
            "وثيقة تحتوي على تحليل شامل للأداء والنتائج المحققة خلال الفترة المحددة",
            "خطة استراتيجية تهدف إلى تحقيق الأهداف طويلة المدى للمؤسسة",
            "دليل شامل يوضح الإجراءات والسياسات المعتمدة في المؤسسة",
            "تحليل مفصل لوضع السوق والمنافسين والفرص المتاحة",
            "تقرير يغطي جميع جوانب إدارة الموارد البشرية والتطوير",
            "خطة متكاملة للتسويق الرقمي والوصول للعملاء المستهدفين",
            "دراسة اقتصادية تحلل جدوى المشاريع والاستثمارات المقترحة",
            "تقرير شامل عن إجراءات الأمن والسلامة في بيئة العمل",
            "خطة لإدارة المخاطر المحتملة وطرق التعامل معها",
            "تحليل مالي مفصل للبيانات والمؤشرات المالية الرئيسية"
        ]
        
        created_documents = []
        
        for i in range(50):
            try:
                # Random document type
                doc_type_info = random.choice(document_types)
                doc_type = doc_type_info['type']
                extension = random.choice(doc_type_info['extensions'])
                
                # Random category
                category = random.choice(target_categories)
                
                # Random user
                user = random.choice(users)
                
                # Random status
                status = random.choice(statuses)
                
                # Random title and description
                if random.choice([True, False]):  # 50% Arabic, 50% English
                    title = random.choice(arabic_titles) + f" - {i+1:02d}"
                    description = random.choice(arabic_descriptions)
                else:
                    english_titles = [
                        "Annual Performance Report", "Strategic Development Plan",
                        "Policy and Procedures Manual", "Market Analysis Report",
                        "Human Resources Report", "Digital Marketing Plan",
                        "Economic Feasibility Study", "Safety and Security Report",
                        "Risk Management Plan", "Financial Data Analysis"
                    ]
                    title = random.choice(english_titles) + f" - {i+1:02d}"
                    description = "This document contains important information and analysis for business operations and strategic planning."

                # Random filename
                words = ["report", "document", "file", "data", "analysis", "plan", "study", "manual"]
                filename = f"document_{i+1:02d}_{random.choice(words)}{extension}"

                # Random dates
                days_ago = random.randint(1, 365)
                created_date = datetime.now() - timedelta(days=days_ago)
                update_days = random.randint(0, days_ago)
                updated_date = created_date + timedelta(days=update_days)
                
                # Create document
                document = Document(
                    title=title,
                    description=description,
                    filename=filename,
                    original_filename=filename,
                    file_path=f"uploads/documents/{filename}",
                    file_size=random.randint(1024, 10485760),  # 1KB to 10MB
                    file_type=doc_type,
                    status=status,
                    category_id=category.id,
                    author_id=user.id,
                    created_at=created_date,
                    updated_at=updated_date
                )
                
                db.session.add(document)
                created_documents.append({
                    'title': title,
                    'type': doc_type,
                    'status': status,
                    'category': category.name_ar or category.name,
                    'user': user.username
                })
                
                if (i + 1) % 10 == 0:
                    print(f"📄 تم إنشاء {i + 1} وثيقة...")
                
            except Exception as e:
                print(f"❌ خطأ في إنشاء الوثيقة {i+1}: {str(e)}")
                continue
        
        try:
            db.session.commit()
            print(f"✅ تم إنشاء {len(created_documents)} وثيقة بنجاح!")
            
            # Print summary
            print("\n📊 ملخص الوثائق المنشأة:")
            print("-" * 50)
            
            # Group by category
            category_counts = {}
            type_counts = {}
            status_counts = {}
            
            for doc in created_documents:
                category_counts[doc['category']] = category_counts.get(doc['category'], 0) + 1
                type_counts[doc['type']] = type_counts.get(doc['type'], 0) + 1
                status_counts[doc['status']] = status_counts.get(doc['status'], 0) + 1
            
            print("\n🗂️ التوزيع حسب الفئات:")
            for category, count in sorted(category_counts.items()):
                print(f"  • {category}: {count} وثيقة")
            
            print("\n📋 التوزيع حسب النوع:")
            for doc_type, count in sorted(type_counts.items()):
                print(f"  • {doc_type}: {count} وثيقة")
            
            print("\n📈 التوزيع حسب الحالة:")
            for status, count in sorted(status_counts.items()):
                print(f"  • {status}: {count} وثيقة")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ خطأ في حفظ الوثائق: {str(e)}")

if __name__ == "__main__":
    create_sample_documents()
