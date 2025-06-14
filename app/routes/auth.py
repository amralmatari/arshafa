"""
Authentication routes
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app, abort
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from urllib.parse import urlparse
from datetime import datetime
from app import db
from app.models.user import User, Role
from app.models.audit import AuditLog, AuditAction
from app.forms.auth import LoginForm, RegistrationForm, ChangePasswordForm, ForgotPasswordForm, ResetPasswordForm
from urllib.parse import urlparse

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(
            (User.username == form.username.data) | 
            (User.email == form.username.data)
        ).first()
        
        if user and user.check_password(form.password.data) and user.is_active:
            # Successful login
            login_user(user, remember=form.remember_me.data)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Log successful login
            AuditLog.log_login_attempt(
                user=user,
                success=True,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            flash('تم تسجيل الدخول بنجاح!', 'success')
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('main.dashboard')
            return redirect(next_page)
        else:
            # Failed login
            AuditLog.log_login_attempt(
                user=user,
                success=False,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                error_message='Invalid credentials or inactive account'
            )
            
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
    
    return render_template('auth/login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    """User logout"""
    # Log logout
    AuditLog.log_action(
        action=AuditAction.LOGOUT,
        user=current_user,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Get default role
        default_role = Role.query.filter_by(is_default=True).first()
        if not default_role:
            default_role = Role.query.filter_by(name='viewer').first()
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            department=form.department.data,
            phone=form.phone.data,
            role=default_role,
            is_active=True  # Auto-activate for now, can be changed to require admin approval
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        # Log user creation
        AuditLog.log_user_action(
            action=AuditAction.USER_CREATE,
            target_user=user,
            user=None,  # Self-registration
            description='User self-registration',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        flash('تم إنشاء الحساب بنجاح! يمكنك الآن تسجيل الدخول.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('auth/profile.html', user=current_user)

@bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    from app.forms.auth import EditProfileForm
    
    form = EditProfileForm(original_email=current_user.email)
    
    if request.method == 'GET':
        # Pre-populate form with current user data
        form.email.data = current_user.email
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.department.data = current_user.department
        form.phone.data = current_user.phone
    
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.department = form.department.data
        current_user.phone = form.phone.data
        
        # Update email if changed
        if form.email.data != current_user.email:
            current_user.email = form.email.data
            if hasattr(current_user, 'email_confirmed'):
                current_user.email_confirmed = False  # Require re-confirmation
        
        db.session.commit()
        
        # Log profile update
        AuditLog.log_user_action(
            action=AuditAction.USER_UPDATE,
            target_user=current_user,
            user=current_user,
            description='Profile updated',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        flash('تم تحديث الملف الشخصي بنجاح!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/edit_profile.html', form=form)

@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            
            # Log password change
            AuditLog.log_user_action(
                action=AuditAction.USER_UPDATE,
                target_user=current_user,
                user=current_user,
                description='Password changed',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            flash('تم تغيير كلمة المرور بنجاح!', 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash('كلمة المرور الحالية غير صحيحة', 'error')
    
    return render_template('auth/change_password.html', form=form)

@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password form"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            try:
                from app.email import send_password_reset_email
                send_password_reset_email(user)
                # Always show success message for security (even if email fails)
                flash('تم إرسال رابط إعادة تعيين كلمة المرور إلى بريدك الإلكتروني. تحقق من صندوق الوارد أو البريد المهمل.', 'success')
                current_app.logger.info(f'Password reset requested for user: {user.username} ({user.email})')
            except Exception as e:
                current_app.logger.error(f'Failed to send password reset email to {user.email}: {str(e)}')
                # Still show success message for security, but log the error
                flash('تم إرسال رابط إعادة تعيين كلمة المرور إلى بريدك الإلكتروني. تحقق من صندوق الوارد أو البريد المهمل.', 'success')
                # In development, also show a warning
                if current_app.config.get('FLASK_ENV') == 'development':
                    flash('تنبيه للمطور: فشل إرسال البريد الإلكتروني. تحقق من console للحصول على رابط إعادة التعيين.', 'warning')
        else:
            # Always show the same message for security
            flash('إذا كان البريد الإلكتروني موجود في النظام، ستتلقى رسالة لإعادة تعيين كلمة المرور.', 'info')

        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html', form=form)

@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    user = User.verify_reset_password_token(token)
    if not user:
        flash('رابط إعادة تعيين كلمة المرور غير صالح أو منتهي الصلاحية.', 'error')
        return redirect(url_for('auth.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.updated_at = datetime.now()
        db.session.commit()

        flash('تم تغيير كلمة المرور بنجاح. يمكنك الآن تسجيل الدخول.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form)

@bp.route('/users')
@login_required
def users():
    """List all users (admin only)"""
    if not current_user.can('manage_users'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('main.dashboard'))
    
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.username).paginate(
        page=page,
        per_page=current_app.config['USERS_PER_PAGE'],
        error_out=False
    )
    
    return render_template('auth/users.html', users=users)

@bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    """Toggle user active status (admin only)"""
    if not current_user.can('manage_users'):
        flash('ليس لديك صلاحية لتنفيذ هذا الإجراء', 'error')
        return redirect(url_for('main.dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # Prevent admin from deactivating themselves
    if user.id == current_user.id:
        flash('لا يمكنك إلغاء تفعيل حسابك الخاص', 'error')
        return redirect(url_for('auth.users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    # Log action
    action = AuditAction.USER_ACTIVATE if user.is_active else AuditAction.USER_DEACTIVATE
    AuditLog.log_user_action(
        action=action,
        target_user=user,
        user=current_user,
        description=f'User {"activated" if user.is_active else "deactivated"}',
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    
    status = 'تم تفعيل' if user.is_active else 'تم إلغاء تفعيل'
    flash(f'{status} المستخدم {user.username} بنجاح', 'success')
    
    return redirect(url_for('auth.users'))

@bp.route('/users/<int:user_id>/change-role', methods=['POST'])
@login_required
def change_user_role(user_id):
    """Change user role (admin only)"""
    if not current_user.can('manage_users'):
        flash('ليس لديك صلاحية لتنفيذ هذا الإجراء', 'error')
        return redirect(url_for('main.dashboard'))

    user = User.query.get_or_404(user_id)
    new_role_name = request.form.get('role_name')

    if not new_role_name:
        flash('لم يتم تحديد الدور الجديد', 'error')
        return redirect(url_for('auth.users'))

    new_role = Role.query.filter_by(name=new_role_name).first()
    if not new_role:
        flash('الدور المحدد غير موجود', 'error')
        return redirect(url_for('auth.users'))

    # Prevent admin from changing their own role
    if user.id == current_user.id:
        flash('لا يمكنك تغيير دورك الخاص', 'error')
        return redirect(url_for('auth.users'))

    # Only super admin can assign admin role
    if new_role_name == 'admin' and (not current_user.role or current_user.role.name != 'super_admin'):
        flash('فقط مدير النظام يمكنه تعيين دور المدير', 'error')
        return redirect(url_for('auth.users'))

    # Prevent changing super admin role
    if user.role and user.role.name == 'super_admin':
        flash('لا يمكن تغيير دور مدير النظام', 'error')
        return redirect(url_for('auth.users'))

    old_role = user.role.name if user.role else 'None'
    user.role = new_role
    db.session.commit()

    # Log action
    AuditLog.log_user_action(
        action=AuditAction.USER_ROLE_CHANGE,
        target_user=user,
        user=current_user,
        description=f'Role changed from {old_role} to {new_role.name}',
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )

    # Translate role names for display
    role_names = {
        'user': 'مستخدم عادي',
        'manager': 'مشرف',
        'admin': 'مدير',
        'super_admin': 'مدير النظام'
    }

    display_role = role_names.get(new_role.name, new_role.name)
    flash(f'تم تغيير دور المستخدم {user.username} إلى {display_role}', 'success')
    return redirect(url_for('auth.users'))







