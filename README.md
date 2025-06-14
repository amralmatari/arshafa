# أرشفة - نظام إدارة الوثائق
# Arshafa - Document Management System

نظام شامل لإدارة وأرشفة الوثائق مع دعم كامل للغة العربية وتخطيط من اليمين إلى اليسار.

A comprehensive document management and archiving system with full Arabic language support and right-to-left layout.

## المميزات الرئيسية / Key Features

### 🔐 الأمان والصلاحيات / Security & Permissions
- نظام مصادقة آمن مع تشفير كلمات المرور
- إدارة الأدوار والصلاحيات المتقدمة
- سجل مراجعة شامل لجميع العمليات
- تشفير الوثائق الحساسة

### 📁 إدارة الوثائق / Document Management
- رفع وتنظيم الوثائق بأنواع مختلفة
- نظام تصنيف هرمي للفئات
- إدارة دورة حياة الوثيقة الكاملة
- نظام إصدارات متقدم
- تواريخ انتهاء الصلاحية والتذكيرات

### 🔍 البحث المتقدم / Advanced Search
- محرك بحث قوي مع دعم النصوص العربية
- البحث في محتوى الملفات (PDF, Word, etc.)
- فلترة متقدمة حسب الفئة والتاريخ والنوع
- اقتراحات البحث التلقائية

### 🌐 دعم اللغة العربية / Arabic Language Support
- واجهة مستخدم كاملة باللغة العربية
- تخطيط من اليمين إلى اليسار (RTL)
- خطوط عربية جميلة ومقروءة
- دعم البحث في النصوص العربية

### 📊 التقارير والإحصائيات / Reports & Analytics
- تقارير شاملة عن استخدام النظام
- إحصائيات الوثائق والمستخدمين
- تقارير التخزين والمساحة
- تصدير التقارير بصيغ مختلفة

### 💾 النسخ الاحتياطي / Backup & Recovery
- نسخ احتياطي تلقائي للبيانات
- جدولة النسخ الاحتياطي
- استعادة البيانات
- مراقبة مساحة التخزين

## متطلبات النظام / System Requirements

- Python 3.8+
- Flask 2.3+
- SQLAlchemy 2.0+
- Bootstrap 5
- PostgreSQL أو SQLite

## التثبيت والإعداد / Installation & Setup

### 1. استنساخ المشروع / Clone the Repository
```bash
git clone https://github.com/your-repo/arshafa.git
cd arshafa
```

### 2. إنشاء البيئة الافتراضية / Create Virtual Environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. تثبيت المتطلبات / Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. إعداد متغيرات البيئة / Environment Variables
```bash
# إنشاء ملف .env
cp .env.example .env
```

### 5. تهيئة النظام / Initialize System
```bash
# تشغيل script التهيئة لإنشاء الأدوار والصلاحيات ومستخدم Super Admin
python init_system.py
```

### 6. تشغيل التطبيق / Run Application
```bash
python run.py
```

## تسجيل الدخول الأولي / Initial Login

بعد تشغيل script التهيئة، يمكنك تسجيل الدخول باستخدام:

- **اسم المستخدم / Username**: `admin`
- **كلمة المرور / Password**: `admin@123`
- **الدور / Role**: مدير النظام (Super Admin)

## نظام الأدوار والصلاحيات / Roles & Permissions

### الأدوار المتاحة / Available Roles

#### 🔴 مدير النظام (Super Admin)
- جميع الصلاحيات بما في ذلك:
- إدارة النظام والإعدادات
- إدارة المستخدمين والأدوار
- إدارة الوثائق والفئات
- عرض جميع التقارير والإحصائيات
- النسخ الاحتياطي واستعادة البيانات

#### 🟡 مدير (Admin)
- إدارة الوثائق (إنشاء، تعديل، حذف)
- إدارة المستخدمين (إنشاء، تعديل)
- عرض الوثائق السرية
- إدارة الفئات
- عرض سجلات المراجعة

#### 🔵 مشرف (Manager)
- إدارة الوثائق (إنشاء، تعديل)
- عرض الوثائق السرية
- إدارة الفئات
- عرض الوثائق والبحث المتقدم

#### 🟢 مستخدم عادي (User)
- عرض الوثائق العامة
- رفع وثائق جديدة
- تعديل الوثائق الخاصة
- البحث الأساسي

### الصلاحيات المتاحة / Available Permissions

- `view_documents` - عرض الوثائق
- `create_documents` - إنشاء الوثائق
- `edit_documents` - تعديل الوثائق
- `delete_documents` - حذف الوثائق
- `view_confidential_documents` - عرض الوثائق السرية
- `manage_categories` - إدارة التصنيفات
- `manage_users` - إدارة المستخدمين
- `manage_roles` - إدارة الأدوار
- `manage_system` - إدارة النظام
- `view_audit_logs` - عرض سجلات المراجعة
- `backup_system` - نسخ احتياطي للنظام
- `restore_system` - استعادة النظام
cp .env.example .env
# تحرير الملف وإضافة الإعدادات المطلوبة
```

### 5. إعداد قاعدة البيانات / Database Setup
```bash
# إنشاء قاعدة البيانات
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# إضافة البيانات الافتراضية
flask init-db
```

### 6. إنشاء مستخدم مدير / Create Admin User
```bash
flask create-admin
```

### 7. تشغيل التطبيق / Run the Application
```bash
# للتطوير
python run.py

# للإنتاج
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

## الحسابات الافتراضية / Default Accounts

بعد تشغيل `flask init-db`، ستتوفر الحسابات التالية:

| الدور | اسم المستخدم | كلمة المرور | الصلاحيات |
|-------|-------------|------------|-----------|
| مدير النظام | admin | admin@123 | جميع الصلاحيات |
| محرر | user | user123 | إنشاء وتعديل الوثائق |
| مشاهد | viewer | viewer123 | عرض الوثائق فقط |

## هيكل المشروع / Project Structure

```
arshafa/
├── app/
│   ├── models/          # نماذج قاعدة البيانات
│   ├── routes/          # مسارات التطبيق
│   ├── templates/       # قوالب HTML
│   ├── static/          # الملفات الثابتة
│   ├── utils/           # الأدوات المساعدة
│   └── forms/           # نماذج الويب
├── migrations/          # ملفات الهجرة
├── tests/              # الاختبارات
├── docs/               # الوثائق
├── config.py           # إعدادات التطبيق
├── run.py              # نقطة دخول التطبيق
└── requirements.txt    # المتطلبات
```

## الاستخدام / Usage

### رفع الوثائق / Uploading Documents
1. سجل الدخول إلى النظام
2. انقر على "رفع وثيقة جديدة"
3. اختر الملف وأدخل البيانات المطلوبة
4. حدد الفئة والعلامات
5. احفظ الوثيقة

### البحث في الوثائق / Searching Documents
1. استخدم مربع البحث في الأعلى
2. أو انتقل إلى صفحة البحث المتقدم
3. استخدم الفلاتر لتضييق النتائج
4. انقر على الوثيقة لعرضها

### إدارة الفئات / Managing Categories
1. انتقل إلى صفحة الفئات
2. أنشئ فئات جديدة أو عدل الموجودة
3. رتب الفئات هرمياً
4. حدد الألوان والأيقونات

## التطوير / Development

### إضافة ميزات جديدة / Adding New Features
1. أنشئ فرع جديد للميزة
2. اكتب الكود والاختبارات
3. تأكد من اتباع معايير الكود
4. أرسل طلب دمج

### تشغيل الاختبارات / Running Tests
```bash
python -m pytest tests/
```

### إنشاء هجرة جديدة / Creating Migrations
```bash
flask db migrate -m "وصف التغيير"
flask db upgrade
```

## الأمان / Security

- تشفير كلمات المرور باستخدام bcrypt
- حماية CSRF لجميع النماذج
- تشفير الجلسات
- تسجيل جميع العمليات الحساسة
- فحص أنواع الملفات المرفوعة
- حدود حجم الملفات

## الدعم / Support

للحصول على المساعدة أو الإبلاغ عن مشاكل:
- افتح تذكرة في GitHub Issues
- راسلنا على البريد الإلكتروني
- راجع الوثائق في مجلد `docs/`

## الترخيص / License

هذا المشروع مرخص تحت رخصة MIT. راجع ملف `LICENSE` للتفاصيل.

## المساهمة / Contributing

نرحب بالمساهمات! يرجى قراءة `CONTRIBUTING.md` للتفاصيل.

---

**أرشفة** - نظام إدارة الوثائق الحديث مع دعم كامل للغة العربية
