#!/usr/bin/env python
"""
Test script to verify Zoho SMTP email configuration
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email():
    """Test sending email via Zoho SMTP"""
    
    # Configure Zoho SMTP settings
    settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    settings.EMAIL_HOST = 'smtp.zoho.com'
    settings.EMAIL_PORT = 587
    settings.EMAIL_USE_TLS = True
    settings.EMAIL_USE_SSL = False
    settings.EMAIL_HOST_USER = 'support@jannatlibrary.com'
    settings.EMAIL_HOST_PASSWORD = '21uqdR8NxEkr'
    settings.DEFAULT_FROM_EMAIL = 'support@jannatlibrary.com'
    settings.SERVER_EMAIL = 'support@jannatlibrary.com'
    
    try:
        print("Testing Zoho SMTP configuration...")
        print(f"SMTP Host: {settings.EMAIL_HOST}")
        print(f"Port: {settings.EMAIL_PORT}")
        print(f"TLS: {settings.EMAIL_USE_TLS}")
        print(f"From: {settings.EMAIL_HOST_USER}")
        print("\nSending test email...")
        
        # Send test email
        send_mail(
            subject='Test Email from Jannat Library',
            message='This is a test email to verify Zoho SMTP configuration is working correctly.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['support@jannatlibrary.com'],  # Send to yourself for testing
            fail_silently=False,
        )
        
        print("✅ SUCCESS! Email sent successfully!")
        print("Please check your inbox at support@jannatlibrary.com")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Failed to send email")
        print(f"Error details: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False

if __name__ == '__main__':
    test_email()

