"""Utility functions for account-related email notifications"""
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone


def send_welcome_email(user):
    """Send welcome email after account creation using HTML template"""
    try:
        from django.template.loader import render_to_string
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@jannatlibrary.com')
        recipient_email = user.email
        
        if not recipient_email:
            return
        
        subject = 'Welcome to JannatLibrary.com - Your Journey Begins!'
        
        # Render HTML template
        html_message = render_to_string('emails/welcome.html', {
            'user_name': user.first_name or user.username,
            'user_email': recipient_email,
        })
        
        # Plain text fallback
        plain_message = f'''Hello {user.first_name or user.username},

Welcome to JannatLibrary.com! We're thrilled to have you as part of our community dedicated to authentic Islamic products and knowledge.

Your account has been successfully created. You can now:
✓ Browse our extensive collection of Islamic books and products
✓ Enjoy secure checkout and order tracking
✓ Save your favorite items for later
✓ Receive exclusive offers and updates

Get Started:
🌐 Visit our store: {getattr(settings, 'SITE_URL', 'https://jannatlibrary.com')}
📚 Browse categories: {getattr(settings, 'SITE_URL', 'https://jannatlibrary.com')}/products/
👤 Manage your account: {getattr(settings, 'SITE_URL', 'https://jannatlibrary.com')}/accounts/dashboard/

New Customer Offer: Use code WELCOME10 for 10% off your first order above ₹500!

At JannatLibrary.com, we're committed to providing you with authentic Islamic products that enrich your spiritual journey.

Thank you for choosing us as your trusted partner!

Best regards,
Jannat Library Team
JannatLibrary.com

---
Questions? Contact us at {from_email}
'''
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=[recipient_email],
            html_message=html_message,
            fail_silently=False,
        )
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Failed to send welcome email to user {user.id}: {str(e)}')


def send_seller_approval_email(seller_profile, status):
    """Send email to seller when their account is approved/rejected/suspended using HTML template"""
    try:
        from django.template.loader import render_to_string
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@jannatlibrary.com')
        recipient_email = seller_profile.user.email or seller_profile.business_email
        
        if not recipient_email:
            return
        
        subject_map = {
            'approved': 'Seller Account Approved - JannatLibrary.com',
            'rejected': 'Seller Account Application Update - JannatLibrary.com',
            'suspended': 'Seller Account Suspended - JannatLibrary.com',
        }
        
        message_map = {
            'approved': f'''Hello {seller_profile.user.first_name or seller_profile.user.username},

🎉 Congratulations! Your seller account has been approved on JannatLibrary.com!

Business Details:
• Business Name: {seller_profile.business_name}
• Account Status: APPROVED ✅

You can now start your journey as a seller on our platform:

✓ Add authentic Islamic products to your inventory
✓ Manage your product listings through the seller dashboard
✓ Track orders and sales in real-time
✓ Access detailed seller analytics and insights
✓ Reach thousands of customers looking for quality Islamic products

Next Steps:
1. Visit your seller dashboard: https://jannatlibrary.com/accounts/seller/dashboard/
2. Add your first product listing
3. Complete your seller profile
4. Start connecting with customers!

We're excited to have you as part of the JannatLibrary.com seller community. Together, we can serve the Muslim community with authentic, quality products.

Welcome aboard!

Best regards,
JannatLibrary.com Team
Your Partner in Islamic Commerce

---
Need assistance? Contact us at {from_email}
''',
            'rejected': f'''Hello {seller_profile.user.first_name or seller_profile.user.username},

Thank you for your interest in becoming a seller on JannatLibrary.com.

After careful review of your application, we are unable to approve your seller account at this time.

Business Name: {seller_profile.business_name}
Application Status: Not Approved

This decision may be due to various factors including documentation requirements, business verification criteria, or platform capacity.

What you can do:
• Review our seller guidelines at: https://jannatlibrary.com/seller-guidelines/
• Ensure all required documentation is complete
• You may reapply in the future once requirements are met

If you have questions about this decision or need clarification on our requirements, please don't hesitate to contact our seller support team.

We appreciate your interest in JannatLibrary.com and wish you success in your business endeavors.

Best regards,
JannatLibrary.com Team

---
Questions? Contact us at {from_email}
''',
            'suspended': f'''Hello {seller_profile.user.first_name or seller_profile.user.username},

Your seller account on JannatLibrary.com has been temporarily suspended.

Business Name: {seller_profile.business_name}
Account Status: SUSPENDED

Your seller privileges have been temporarily suspended due to policy violations or account security concerns. During this period, your products will not be visible to customers and you cannot process new orders.

Important Actions Required:
1. Review our seller policies and terms of service
2. Contact our support team to understand the suspension reason
3. Provide any requested documentation or clarification
4. Wait for account review and potential reinstatement

To resolve this matter quickly:
📧 Email us at: {from_email}
📞 Contact seller support for immediate assistance

We value our seller community and want to work with you to resolve any issues promptly.

Best regards,
JannatLibrary.com Team

---
This is an automated notification. Please contact support for immediate assistance.
''',
        }
        
        # Render HTML template
        html_message = render_to_string('emails/seller_status_update.html', {
            'seller_profile': seller_profile,
            'status': status,
        })
        
        subject = subject_map.get(status, 'Seller Account Update - JannatLibrary.com')
        plain_message = message_map.get(status, 'Your seller account status has been updated.')
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=[recipient_email],
            html_message=html_message,
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
        
        subject = 'Password Changed Successfully - JannatLibrary.com'
        
        message = f'''Hello {user.first_name or user.username},

🔒 Your password has been successfully changed for your JannatLibrary.com account.

Account Security Confirmation:
• Account: {user.email}
• Change Date: {timezone.now().strftime("%B %d, %Y at %I:%M %p")}
• Change Method: Secure password update

If you made this change, no further action is required. Your account remains secure.

⚠️ If you did not make this change:
1. Contact our support team immediately at {from_email}
2. Review your account activity
3. Consider enabling additional security measures

Security Best Practices:
✓ Use a strong, unique password for your account
✓ Never share your login credentials with anyone
✓ Log out when using shared or public computers
✓ Regularly review your account activity

Your account security is our top priority. Thank you for keeping your JannatLibrary.com account safe!

Best regards,
JannatLibrary.com Security Team

---
Immediate assistance needed? Contact: {from_email}
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

