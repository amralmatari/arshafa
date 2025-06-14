# حذف قاعدة البيانات الحالية
rm -f instance/arshafa.db

# إعادة تهيئة قاعدة البيانات
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# إضافة البيانات الافتراضية
flask init-db

# إضافة الحقل last_seen إلى نموذج User
flask db migrate -m "Add last_seen field to User model"
flask db upgrade

# إضافة البيانات الافتراضية
flask init-db

# إضافة الحقل expiry_date إلى نموذج Document
flask db migrate -m "Add expiry_date field to Document model"
flask db upgrade

# إضافة البيانات الافتراضية
flask init-db

# إنشاء هجرة جديدة لإضافة الأعمدة المفقودة
flask db migrate -m "Add missing columns to Document model"
flask db upgrade

# إضافة البيانات الافتراضية
flask init-db









