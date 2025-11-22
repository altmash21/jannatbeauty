# SMTP Email Configuration Guide

This guide will help you set up SMTP email for your Django application.

## Quick Setup

1. **Create a `.env` file** in your project root (same directory as `manage.py`)

2. **Add your SMTP configuration** to the `.env` file (see examples below)

3. **Test your configuration** using:
   ```bash
   python manage.py test_email
   ```

## SMTP Provider Examples

### Zoho Mail (Current Configuration)

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.zoho.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=support@jannatlibrary.com
EMAIL_HOST_PASSWORD=your-app-password-here
DEFAULT_FROM_EMAIL=support@jannatlibrary.com
```

**Important for Zoho:**
- Enable 2-Step Verification in your Zoho account
- Generate an App Password (not your regular password)
- Use the App Password in `EMAIL_HOST_PASSWORD`
- If port 587 doesn't work, try port 465 with SSL:
  ```env
  EMAIL_PORT=465
  EMAIL_USE_TLS=False
  EMAIL_USE_SSL=True
  ```

### Gmail

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

**Gmail Setup:**
1. Enable 2-Step Verification
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use the 16-character app password

### Outlook/Hotmail

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-email@outlook.com
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=your-email@outlook.com
```

### Custom SMTP Server

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.yourdomain.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-email@yourdomain.com
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=your-email@yourdomain.com
```

## Testing Your Configuration

Run the test command:
```bash
python manage.py test_email
```

This will:
- Try multiple SMTP configurations automatically
- Show which configuration works
- Display any errors with helpful troubleshooting tips

## Security Best Practices

1. **Never commit `.env` file to git** - It's already in `.gitignore`
2. **Use App Passwords** instead of regular passwords
3. **Keep credentials secure** - Don't share them publicly
4. **Use environment variables** in production (not hardcoded values)

## Troubleshooting

### Authentication Failed (535 Error)
- Verify your app password is correct
- Make sure 2FA is enabled (required for app passwords)
- Check if your email provider requires specific settings
- Try different ports (587 vs 465)

### Connection Timeout
- Check your firewall settings
- Verify SMTP host and port are correct
- Some networks block SMTP ports

### SSL/TLS Errors
- Try switching between TLS (port 587) and SSL (port 465)
- Verify your email provider supports the chosen method

## Current Configuration

Your current settings are configured to use:
- **Backend**: Console (emails print to console) - Change to SMTP in `.env`
- **Default Host**: smtp.zoho.com
- **Default Port**: 587 (TLS)

To activate SMTP, create a `.env` file with your credentials.

