"""
Authentication forms
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional
from app.models.user import User

class LoginForm(FlaskForm):
    """User login form"""
    username = StringField('اسم المستخدم أو البريد الإلكتروني', 
                          validators=[DataRequired(message='هذا الحقل مطلوب')],
                          render_kw={'placeholder': 'أدخل اسم المستخدم أو البريد الإلكتروني'})
    
    password = PasswordField('كلمة المرور', 
                            validators=[DataRequired(message='هذا الحقل مطلوب')],
                            render_kw={'placeholder': 'أدخل كلمة المرور'})
    
    remember_me = BooleanField('تذكرني')
    submit = SubmitField('تسجيل الدخول')

class RegistrationForm(FlaskForm):
    """User registration form"""
    username = StringField('اسم المستخدم', 
                          validators=[
                              DataRequired(message='هذا الحقل مطلوب'),
                              Length(min=3, max=64, message='اسم المستخدم يجب أن يكون بين 3 و 64 حرف')
                          ],
                          render_kw={'placeholder': 'أدخل اسم المستخدم'})
    
    email = StringField('البريد الإلكتروني', 
                       validators=[
                           DataRequired(message='هذا الحقل مطلوب'),
                           Email(message='البريد الإلكتروني غير صحيح')
                       ],
                       render_kw={'placeholder': 'أدخل البريد الإلكتروني'})
    
    first_name = StringField('الاسم الأول', 
                            validators=[
                                DataRequired(message='هذا الحقل مطلوب'),
                                Length(max=64, message='الاسم الأول لا يجب أن يتجاوز 64 حرف')
                            ],
                            render_kw={'placeholder': 'أدخل الاسم الأول'})
    
    last_name = StringField('اسم العائلة', 
                           validators=[
                               DataRequired(message='هذا الحقل مطلوب'),
                               Length(max=64, message='اسم العائلة لا يجب أن يتجاوز 64 حرف')
                           ],
                           render_kw={'placeholder': 'أدخل اسم العائلة'})
    
    department = StringField('القسم', 
                            validators=[Length(max=100, message='اسم القسم لا يجب أن يتجاوز 100 حرف')],
                            render_kw={'placeholder': 'أدخل اسم القسم'})
    
    phone = StringField('رقم الهاتف', 
                       validators=[Length(max=20, message='رقم الهاتف لا يجب أن يتجاوز 20 رقم')],
                       render_kw={'placeholder': 'أدخل رقم الهاتف'})
    
    password = PasswordField('كلمة المرور', 
                            validators=[
                                DataRequired(message='هذا الحقل مطلوب'),
                                Length(min=6, message='كلمة المرور يجب أن تكون على الأقل 6 أحرف')
                            ],
                            render_kw={'placeholder': 'أدخل كلمة المرور'})
    
    password2 = PasswordField('تأكيد كلمة المرور', 
                             validators=[
                                 DataRequired(message='هذا الحقل مطلوب'),
                                 EqualTo('password', message='كلمات المرور غير متطابقة')
                             ],
                             render_kw={'placeholder': 'أعد إدخال كلمة المرور'})
    
    submit = SubmitField('إنشاء الحساب')
    
    def validate_username(self, username):
        """Validate username uniqueness"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('اسم المستخدم موجود بالفعل. يرجى اختيار اسم آخر.')
    
    def validate_email(self, email):
        """Validate email uniqueness"""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('البريد الإلكتروني موجود بالفعل. يرجى استخدام بريد إلكتروني آخر.')

class EditProfileForm(FlaskForm):
    """Edit user profile form"""
    email = StringField('البريد الإلكتروني', 
                       validators=[
                           DataRequired(message='هذا الحقل مطلوب'),
                           Email(message='البريد الإلكتروني غير صحيح')
                       ],
                       render_kw={'placeholder': 'أدخل البريد الإلكتروني'})
    
    first_name = StringField('الاسم الأول', 
                            validators=[
                                DataRequired(message='هذا الحقل مطلوب'),
                                Length(max=64, message='الاسم الأول لا يجب أن يتجاوز 64 حرف')
                            ],
                            render_kw={'placeholder': 'أدخل الاسم الأول'})
    
    last_name = StringField('اسم العائلة', 
                           validators=[
                               DataRequired(message='هذا الحقل مطلوب'),
                               Length(max=64, message='اسم العائلة لا يجب أن يتجاوز 64 حرف')
                           ],
                           render_kw={'placeholder': 'أدخل اسم العائلة'})
    
    department = StringField('القسم', 
                            validators=[Length(max=100, message='اسم القسم لا يجب أن يتجاوز 100 حرف')],
                            render_kw={'placeholder': 'أدخل اسم القسم'})
    
    phone = StringField('رقم الهاتف', 
                       validators=[Length(max=20, message='رقم الهاتف لا يجب أن يتجاوز 20 رقم')],
                       render_kw={'placeholder': 'أدخل رقم الهاتف'})
    
    submit = SubmitField('حفظ التغييرات')
    
    def __init__(self, original_email, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_email = original_email
    
    def validate_email(self, email):
        """Validate email uniqueness (excluding current user)"""
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('البريد الإلكتروني موجود بالفعل. يرجى استخدام بريد إلكتروني آخر.')

class ChangePasswordForm(FlaskForm):
    """Change password form"""
    current_password = PasswordField('كلمة المرور الحالية', 
                                    validators=[DataRequired(message='هذا الحقل مطلوب')],
                                    render_kw={'placeholder': 'أدخل كلمة المرور الحالية'})
    
    new_password = PasswordField('كلمة المرور الجديدة', 
                                validators=[
                                    DataRequired(message='هذا الحقل مطلوب'),
                                    Length(min=6, message='كلمة المرور يجب أن تكون على الأقل 6 أحرف')
                                ],
                                render_kw={'placeholder': 'أدخل كلمة المرور الجديدة'})
    
    confirm_password = PasswordField('تأكيد كلمة المرور الجديدة', 
                                   validators=[
                                       DataRequired(message='هذا الحقل مطلوب'),
                                       EqualTo('new_password', message='كلمات المرور غير متطابقة')
                                   ],
                                   render_kw={'placeholder': 'أعد إدخال كلمة المرور الجديدة'})
    
    submit = SubmitField('تغيير كلمة المرور')

class ForgotPasswordForm(FlaskForm):
    """Forgot password form"""
    email = StringField('البريد الإلكتروني',
                       validators=[
                           DataRequired(message='هذا الحقل مطلوب'),
                           Email(message='البريد الإلكتروني غير صحيح')
                       ],
                       render_kw={'placeholder': 'أدخل البريد الإلكتروني'})

    submit = SubmitField('إرسال رابط إعادة التعيين')

class ResetPasswordForm(FlaskForm):
    """Reset password form"""
    password = PasswordField('كلمة المرور الجديدة',
                            validators=[
                                DataRequired(message='هذا الحقل مطلوب'),
                                Length(min=6, message='كلمة المرور يجب أن تكون 6 أحرف على الأقل')
                            ],
                            render_kw={'placeholder': 'أدخل كلمة المرور الجديدة'})

    password2 = PasswordField('تأكيد كلمة المرور',
                             validators=[
                                 DataRequired(message='هذا الحقل مطلوب'),
                                 EqualTo('password', message='كلمات المرور غير متطابقة')
                             ],
                             render_kw={'placeholder': 'أعد إدخال كلمة المرور الجديدة'})

    submit = SubmitField('تعيين كلمة المرور')

class UserForm(FlaskForm):
    """Admin user management form"""
    username = StringField('اسم المستخدم', 
                          validators=[
                              DataRequired(message='هذا الحقل مطلوب'),
                              Length(min=3, max=64, message='اسم المستخدم يجب أن يكون بين 3 و 64 حرف')
                          ])
    
    email = StringField('البريد الإلكتروني', 
                       validators=[
                           DataRequired(message='هذا الحقل مطلوب'),
                           Email(message='البريد الإلكتروني غير صحيح')
                       ])
    
    first_name = StringField('الاسم الأول', 
                            validators=[
                                DataRequired(message='هذا الحقل مطلوب'),
                                Length(max=64, message='الاسم الأول لا يجب أن يتجاوز 64 حرف')
                            ])
    
    last_name = StringField('اسم العائلة', 
                           validators=[
                               DataRequired(message='هذا الحقل مطلوب'),
                               Length(max=64, message='اسم العائلة لا يجب أن يتجاوز 64 حرف')
                           ])
    
    department = StringField('القسم', 
                            validators=[Length(max=100, message='اسم القسم لا يجب أن يتجاوز 100 حرف')])
    
    phone = StringField('رقم الهاتف', 
                       validators=[Length(max=20, message='رقم الهاتف لا يجب أن يتجاوز 20 رقم')])
    
    role = SelectField('الدور', coerce=int, validators=[DataRequired(message='هذا الحقل مطلوب')])
    
    is_active = BooleanField('نشط')
    
    password = PasswordField('كلمة المرور', 
                            validators=[
                                Optional(),
                                Length(min=6, message='كلمة المرور يجب أن تكون على الأقل 6 أحرف')
                            ])
    
    submit = SubmitField('حفظ')
    
    def __init__(self, user=None, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        from app.models.user import Role
        self.role.choices = [(r.id, r.name) for r in Role.query.order_by(Role.name).all()]
        self.user = user
    
    def validate_username(self, username):
        """Validate username uniqueness"""
        if self.user and username.data == self.user.username:
            return
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('اسم المستخدم موجود بالفعل. يرجى اختيار اسم آخر.')
    
    def validate_email(self, email):
        """Validate email uniqueness"""
        if self.user and email.data == self.user.email:
            return
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('البريد الإلكتروني موجود بالفعل. يرجى استخدام بريد إلكتروني آخر.')
