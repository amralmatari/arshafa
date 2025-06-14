"""
Email utilities for the application
"""

from flask import current_app, render_template
from flask_mail import Message
from app import mail
import threading


def send_async_email(app, msg):
    """Send email asynchronously"""
    with app.app_context():
        try:
            mail.send(msg)
            current_app.logger.info(f'Email sent successfully to {msg.recipients}')
            print(f"✅ Email sent successfully to {', '.join(msg.recipients)}")
        except Exception as e:
            error_msg = str(e)
            current_app.logger.error(f'Failed to send email to {msg.recipients}: {error_msg}')

            # Check for common Gmail errors
            if 'Authentication failed' in error_msg or '535' in error_msg:
                print(f"\n{'='*60}")
                print(f"❌ GMAIL AUTHENTICATION ERROR")
                print(f"{'='*60}")
                print(f"Error: {error_msg}")
                print(f"")
                print(f"🔧 To fix this issue:")
                print(f"1. Enable 2-Factor Authentication on your Gmail account")
                print(f"2. Generate an App Password:")
                print(f"   - Go to: https://myaccount.google.com/apppasswords")
                print(f"   - Select 'Mail' and your device")
                print(f"   - Copy the 16-character password")
                print(f"3. Update MAIL_PASSWORD in .env file with the App Password")
                print(f"4. Make sure MAIL_USERNAME is your full Gmail address")
                print(f"{'='*60}\n")
            elif 'Connection refused' in error_msg or 'timeout' in error_msg:
                print(f"\n{'='*60}")
                print(f"🌐 NETWORK CONNECTION ERROR")
                print(f"{'='*60}")
                print(f"Error: {error_msg}")
                print(f"")
                print(f"🔧 Check your internet connection and firewall settings")
                print(f"{'='*60}\n")
            else:
                print(f"\n{'='*60}")
                print(f"📧 EMAIL SENDING FAILED - SHOWING CONTENT")
                print(f"{'='*60}")
                print(f"Error: {error_msg}")
                print(f"")

            # Always show email content for debugging
            print(f"📬 To: {', '.join(msg.recipients)}")
            print(f"📝 Subject: {msg.subject}")
            print(f"📄 Body:")
            print(f"{'-'*40}")
            print(msg.body)
            print(f"{'-'*40}")

            # Extract reset URL from email body
            import re
            url_match = re.search(r'http://[^\s]+/auth/reset-password/[^\s]+', msg.body)
            if url_match:
                reset_url = url_match.group()
                print(f"🔗 DIRECT RESET LINK:")
                print(f"   {reset_url}")
                print(f"{'-'*40}")

            if msg.html:
                print(f"🌐 HTML Version Available")
            print(f"{'='*60}\n")


def send_email(subject, sender, recipients, text_body, html_body):
    """Send email with both text and HTML versions"""
    try:
        msg = Message(subject, sender=sender, recipients=recipients)
        msg.body = text_body
        msg.html = html_body

        # Send email asynchronously
        app = current_app._get_current_object()
        thread = threading.Thread(target=send_async_email, args=(app, msg))
        thread.start()
        return thread
    except Exception as e:
        current_app.logger.error(f'Error creating email message: {str(e)}')
        raise


def send_password_reset_email(user):
    """Send password reset email to user"""
    from flask import url_for

    token = user.get_reset_password_token()

    subject = 'إعادة تعيين كلمة المرور - نظام أرشفة'
    sender = current_app.config.get('MAIL_DEFAULT_SENDER') or current_app.config.get('MAIL_USERNAME') or 'noreply@arshafa.com'

    # Generate reset URL for console display
    reset_url = url_for('auth.reset_password', token=token, _external=True)

    # Text version
    text_body = render_template('email/reset_password.txt',
                               user=user, token=token)

    # HTML version
    html_body = render_template('email/reset_password.html',
                               user=user, token=token)

    # Add reset URL to console output
    current_app.logger.info(f'Password reset URL for {user.username}: {reset_url}')

    send_email(subject, sender, [user.email], text_body, html_body)


def send_welcome_email(user, password=None):
    """Send welcome email to new user"""
    subject = 'مرحباً بك في نظام أرشفة'
    sender = current_app.config['MAIL_USERNAME'] or 'noreply@arshafa.com'
    
    # Text version
    text_body = render_template('email/welcome.txt',
                               user=user, password=password)
    
    # HTML version
    html_body = render_template('email/welcome.html',
                               user=user, password=password)
    
    send_email(subject, sender, [user.email], text_body, html_body)


def send_notification_email(user, subject, message):
    """Send general notification email"""
    sender = current_app.config['MAIL_USERNAME'] or 'noreply@arshafa.com'
    
    # Text version
    text_body = f"""
مرحباً {user.username},

{message}

مع تحيات فريق نظام أرشفة
"""
    
    # HTML version
    html_body = render_template('email/notification.html',
                               user=user, message=message)
    
    send_email(subject, sender, [user.email], text_body, html_body)
