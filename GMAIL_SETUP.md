# إعداد Gmail لإرسال البريد الإلكتروني

## الخطوات المطلوبة لإعداد Gmail SMTP

### 1. تفعيل المصادقة الثنائية (2FA)
1. اذهب إلى [إعدادات حساب Google](https://myaccount.google.com/)
2. انقر على "الأمان" (Security)
3. في قسم "تسجيل الدخول إلى Google"، انقر على "التحقق بخطوتين"
4. اتبع التعليمات لتفعيل المصادقة الثنائية

### 2. إنشاء كلمة مرور التطبيق (App Password)
1. بعد تفعيل المصادقة الثنائية، اذهب إلى [كلمات مرور التطبيق](https://myaccount.google.com/apppasswords)
2. قد تحتاج لتسجيل الدخول مرة أخرى
3. في قائمة "تحديد التطبيق"، اختر "البريد" (Mail)
4. في قائمة "تحديد الجهاز"، اختر "جهاز كمبيوتر Windows" أو "أخرى"
5. انقر على "إنشاء" (Generate)
6. انسخ كلمة المرور المكونة من 16 حرف (مثل: abcd efgh ijkl mnop)

### 3. تحديث ملف .env
افتح ملف `.env` وحدث الإعدادات التالية:

```env
# Gmail SMTP Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=abcd efgh ijkl mnop
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

**ملاحظات مهمة:**
- استبدل `your-email@gmail.com` ببريدك الإلكتروني الحقيقي
- استبدل `abcd efgh ijkl mnop` بكلمة مرور التطبيق التي حصلت عليها
- لا تستخدم كلمة مرور حسابك العادية، استخدم كلمة مرور التطبيق فقط

### 4. إعادة تشغيل التطبيق
بعد تحديث ملف `.env`، أعد تشغيل التطبيق:

```bash
python run.py
```

### 5. اختبار الإعداد
1. اذهب إلى صفحة نسيان كلمة المرور: `http://127.0.0.1:5000/auth/forgot-password`
2. أدخل بريد إلكتروني موجود في النظام
3. انقر على "إرسال رابط إعادة التعيين"
4. تحقق من صندوق الوارد في Gmail

## استكشاف الأخطاء

### خطأ المصادقة (Authentication Error)
```
535-5.7.8 Username and Password not accepted
```
**الحل:**
- تأكد من تفعيل المصادقة الثنائية
- تأكد من استخدام كلمة مرور التطبيق وليس كلمة مرور الحساب
- تأكد من صحة البريد الإلكتروني

### خطأ الاتصال (Connection Error)
```
[WinError 10061] No connection could be made
```
**الحل:**
- تحقق من اتصال الإنترنت
- تحقق من إعدادات الجدار الناري (Firewall)
- تأكد من أن المنفذ 587 غير محجوب

### خطأ TLS/SSL
```
SSL: CERTIFICATE_VERIFY_FAILED
```
**الحل:**
- تأكد من أن `MAIL_USE_TLS=true`
- تأكد من أن `MAIL_USE_SSL=false`
- تأكد من أن `MAIL_PORT=587`

## أمان المعلومات

⚠️ **تحذير أمني:**
- لا تشارك كلمة مرور التطبيق مع أحد
- لا تضع كلمة مرور التطبيق في الكود المصدري
- استخدم ملف `.env` فقط وتأكد من إضافته إلى `.gitignore`
- يمكنك إلغاء كلمة مرور التطبيق في أي وقت من إعدادات Google

## للإنتاج

في بيئة الإنتاج، استخدم متغيرات البيئة بدلاً من ملف `.env`:

```bash
export MAIL_USERNAME=your-email@gmail.com
export MAIL_PASSWORD=your-app-password
export MAIL_DEFAULT_SENDER=your-email@gmail.com
```
