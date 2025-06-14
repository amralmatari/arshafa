from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SelectMultipleField, BooleanField, DateField, FileField
from wtforms.validators import DataRequired, Length, Optional
from flask_wtf.file import FileRequired, FileAllowed

class DocumentForm(FlaskForm):
    """Form for creating and editing documents"""
    title = StringField('عنوان الوثيقة', validators=[
        DataRequired(message='يرجى إدخال عنوان الوثيقة'),
        Length(min=3, max=255, message='يجب أن يكون العنوان بين 3 و 255 حرفًا')
    ])

    description = TextAreaField('وصف الوثيقة', validators=[
        Optional(),
        Length(max=2000, message='يجب أن لا يتجاوز الوصف 2000 حرف')
    ])

    # نظام الفئات الهرمي
    main_category_id = SelectField('الفئة الرئيسية', coerce=int, validators=[
        Optional()
    ])

    sub_category_1_id = SelectField('الفئة الفرعية الأولى', coerce=int, validators=[
        Optional()
    ])

    sub_category_2_id = SelectField('الفئة الفرعية الثانية', coerce=int, validators=[
        Optional()
    ])

    sub_category_3_id = SelectField('الفئة الفرعية الثالثة', coerce=int, validators=[
        Optional()
    ])

    # الحقل المخفي للفئة النهائية المختارة
    category_id = SelectField('الفئة', coerce=int, validators=[
        Optional()
    ])

    # حذف حقل العلامات
    # tags = SelectMultipleField('العلامات', coerce=int, validators=[
    #     Optional()
    # ])

    # حذف طريقة تعيين خيارات العلامات
    # def set_tag_choices(self, tags):
    #     self.tags.choices = [(tag.id, tag.name) for tag in tags]

    status = SelectField('الحالة', validators=[
        DataRequired(message='يرجى اختيار حالة الوثيقة')
    ])

    def __init__(self, *args, **kwargs):
        super(DocumentForm, self).__init__(*args, **kwargs)
        # استخدام الحالات من DocumentStatus
        from app.models.document import DocumentStatus
        self.status.choices = DocumentStatus.choices()

    is_confidential = BooleanField('وثيقة سرية')

    expiry_date = DateField('تاريخ انتهاء الصلاحية', validators=[
        Optional()
    ])

    document_file = FileField('ملف الوثيقة', validators=[
        Optional(),
        FileAllowed(['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'jpg', 'jpeg', 'png', 'gif'],
                   'يرجى اختيار ملف بتنسيق مدعوم')
    ])

    version_comment = TextAreaField('تعليق على الإصدار', validators=[
        Optional(),
        Length(max=500, message='يجب أن لا يتجاوز التعليق 500 حرف')
    ])





