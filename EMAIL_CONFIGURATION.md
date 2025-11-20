# Email Configuration Guide

## Current Setup (Development)
Your project is currently configured to print emails to the console. This is perfect for development and testing.

## How to Configure Real Email Sending

### Option 1: Gmail SMTP (Recommended for Testing)

Add these settings to `ecommerce/settings.py`:

```python
# Email Configuration for Gmail
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'  # Your Gmail address
EMAIL_HOST_PASSWORD = 'your-app-password'  # Gmail App Password (not regular password)
DEFAULT_FROM_EMAIL = 'your-email@gmail.com'
```

**Important for Gmail:**
1. Enable 2-Factor Authentication on your Gmail account
2. Generate an "App Password" from Google Account settings
3. Use the App Password (not your regular password) in `EMAIL_HOST_PASSWORD`

### Option 2: Other SMTP Providers

#### Outlook/Hotmail:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp-mail.outlook.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@outlook.com'
EMAIL_HOST_PASSWORD = 'your-password'
DEFAULT_FROM_EMAIL = 'your-email@outlook.com'
```

#### SendGrid (Recommended for Production):
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = 'your-sendgrid-api-key'
DEFAULT_FROM_EMAIL = 'noreply@jannatbeauty.com'
```

#### Mailgun:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.mailgun.org'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-mailgun-username'
EMAIL_HOST_PASSWORD = 'your-mailgun-password'
DEFAULT_FROM_EMAIL = 'noreply@jannatbeauty.com'
```

### Option 3: Keep Console Backend for Development

For local development, you can keep the console backend and check the terminal for OTPs:

```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@jannatbeauty.com'
```

## Testing OTP Functionality

1. **With Console Backend (Current Setup):**
   - Start server: `python manage.py runserver`
   - Go to `/accounts/forgot-password/`
   - Enter an email address
   - Check the terminal - you'll see the OTP email printed there
   - Copy the OTP and use it to verify

2. **With SMTP Configured:**
   - Configure SMTP settings as shown above
   - Restart the server
   - Go to `/accounts/forgot-password/`
   - Enter an email address
   - Check the email inbox for the OTP

## Security Notes

- Never commit email credentials to version control
- Use environment variables for sensitive information:
  ```python
  import os
  EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
  EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
  ```

## Current Status

✅ OTP generation is working
✅ Email sending code is implemented
✅ OTP verification is working
✅ Password reset flow is complete
⚠️ Currently using console backend (emails print to terminal)

