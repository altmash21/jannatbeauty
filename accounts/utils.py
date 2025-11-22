"""Utility functions for account-related email notifications"""
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User


def send_welcome_email(user):
    """Send welcome email after account creation"""
    try:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@jannatlibrary.com')
        recipient_email = user.email
        
        if not recipient_email:
            return
        
        subject = 'Welcome to Jannat Library!'
        
        message = f'''Hello {user.first_name or user.username},

Welcome to Jannat Library! We're thrilled to have you as part of our community.

Your account has been successfully created. You can now:
- Browse our extensive collection of Islamic books and products
- Add items to your cart and checkout securely
- Track your orders from your dashboard
- Save your favorite products

Get Started:
- Visit our store: {getattr(settings, 'SITE_URL', 'https://jannatlibrary.com')}
- Browse categories: {getattr(settings, 'SITE_URL', 'https://jannatlibrary.com')}/products/

Thank you for choosing Jannat Library!

Best regards,
Jannat Library Team

---
Need help? Contact us at {from_email}
'''
        
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Failed to send welcome email to user {user.id}: {str(e)}')


def send_seller_approval_email(seller_profile, status):
    """Send email to seller when their account is approved/rejected/suspended"""
    try:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@jannatlibrary.com')
        recipient_email = seller_profile.user.email or seller_profile.business_email
        
        if not recipient_email:
            return
        
        subject_map = {
            'approved': 'Seller Account Approved - Jannat Library',
            'rejected': 'Seller Account Application Update - Jannat Library',
            'suspended': 'Seller Account Suspended - Jannat Library',
        }
        
        message_map = {
            'approved': f'''Hello {seller_profile.user.first_name or seller_profile.user.username},

Great news! Your seller account has been approved.

Business Name: {seller_profile.business_name}

You can now:
- Add products to your seller dashboard
- Manage your product listings
- Track orders and sales
- Access seller analytics

Get started by visiting your seller dashboard and adding your first product.

We're excited to have you as part of the Jannat Library seller community!

Best regards,
Jannat Library Team
''',
            'rejected': f'''Hello {seller_profile.user.first_name or seller_profile.user.username},

Thank you for your interest in becoming a seller on Jannat Library.

Unfortunately, we are unable to approve your seller account application at this time.

Business Name: {seller_profile.business_name}

If you have any questions or would like to reapply in the future, please contact us.

Best regards,
Jannat Library Team
''',
            'suspended': f'''Hello {seller_profile.user.first_name or seller_profile.user.username},

Your seller account has been suspended.

Business Name: {seller_profile.business_name}

Your account privileges have been temporarily suspended. Please contact our support team for more information.

If you have any questions, please contact us at {from_email}

Best regards,
Jannat Library Team
''',
        }
        
        subject = subject_map.get(status, 'Seller Account Update - Jannat Library')
        message = message_map.get(status, 'Your seller account status has been updated.')
        
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Failed to send seller approval email to {seller_profile.id}: {str(e)}')


def send_password_change_confirmation_email(user):
    """Send confirmation email when password is changed"""
    try:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@jannatlibrary.com')
        recipient_email = user.email
        
        if not recipient_email:
            return
        
        subject = 'Password Changed Successfully - Jannat Library'
        
        message = f'''Hello {user.first_name or user.username},

Your password has been successfully changed.

If you did not make this change, please contact us immediately at {from_email}

For your security:
- Use a strong, unique password
- Never share your password with anyone
- Log out when using shared computers

Thank you for keeping your account secure!

Best regards,
Jannat Library Team
'''
        
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Failed to send password change confirmation email to user {user.id}: {str(e)}')

