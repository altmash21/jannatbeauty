from django.core.management.base import BaseCommand
from django.core.mail import send_mail, get_connection
from django.conf import settings


class Command(BaseCommand):
    help = 'Test Zoho SMTP email configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--port',
            type=int,
            default=587,
            help='SMTP port to use (587 for TLS, 465 for SSL)',
        )
        parser.add_argument(
            '--ssl',
            action='store_true',
            help='Use SSL instead of TLS',
        )

    def handle(self, *args, **options):
        port = options['port']
        use_ssl = options['ssl']
        use_tls = not use_ssl
        
        # Try different configurations
        configs = [
            {
                'name': 'Port 587 with TLS',
                'host': 'smtp.zoho.com',
                'port': 587,
                'use_tls': True,
                'use_ssl': False,
            },
            {
                'name': 'Port 465 with SSL',
                'host': 'smtp.zoho.com',
                'port': 465,
                'use_tls': False,
                'use_ssl': True,
            },
            {
                'name': 'Port 587 with TLS (smtp.zoho.in)',
                'host': 'smtp.zoho.in',
                'port': 587,
                'use_tls': True,
                'use_ssl': False,
            },
        ]
        
        # If user specified port/ssl, use that
        if port != 587 or use_ssl:
            configs = [{
                'name': f'Port {port} with {"SSL" if use_ssl else "TLS"}',
                'host': 'smtp.zoho.com',
                'port': port,
                'use_tls': use_tls,
                'use_ssl': use_ssl,
            }]
        
        email_user = 'support@jannatlibrary.com'
        email_password = '21uqdR8NxEkr'
        
        for config in configs:
            self.stdout.write(self.style.WARNING(f'\n{"="*60}'))
            self.stdout.write(self.style.WARNING(f'Trying: {config["name"]}'))
            self.stdout.write(self.style.WARNING(f'{"="*60}'))
            
            try:
                # Create connection with specific config
                connection = get_connection(
                    backend='django.core.mail.backends.smtp.EmailBackend',
                    host=config['host'],
                    port=config['port'],
                    username=email_user,
                    password=email_password,
                    use_tls=config['use_tls'],
                    use_ssl=config['use_ssl'],
                    fail_silently=False,
                )
                
                self.stdout.write(f'SMTP Host: {config["host"]}')
                self.stdout.write(f'Port: {config["port"]}')
                self.stdout.write(f'TLS: {config["use_tls"]}')
                self.stdout.write(f'SSL: {config["use_ssl"]}')
                self.stdout.write(f'Username: {email_user}')
                self.stdout.write('Password: [HIDDEN]')
                self.stdout.write('\nConnecting and sending test email...')
                
                # Send test email
                send_mail(
                    subject='Test Email from Jannat Library',
                    message='This is a test email to verify Zoho SMTP configuration is working correctly.',
                    from_email=email_user,
                    recipient_list=[email_user],
                    connection=connection,
                    fail_silently=False,
                )
                
                self.stdout.write(self.style.SUCCESS('\n✅ SUCCESS! Email sent successfully!'))
                self.stdout.write(self.style.SUCCESS(f'Configuration that worked: {config["name"]}'))
                self.stdout.write(f'Please check your inbox at {email_user}')
                
                # Update settings with working configuration
                self.stdout.write(self.style.WARNING('\n⚠️  Update your settings.py with these values:'))
                self.stdout.write(f'EMAIL_HOST = "{config["host"]}"')
                self.stdout.write(f'EMAIL_PORT = {config["port"]}')
                self.stdout.write(f'EMAIL_USE_TLS = {config["use_tls"]}')
                self.stdout.write(f'EMAIL_USE_SSL = {config["use_ssl"]}')
                
                return
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'\n❌ Failed: {str(e)}'))
                self.stdout.write(self.style.ERROR(f'Error type: {type(e).__name__}'))
                
                # If it's an authentication error, provide helpful tips
                if 'Authentication' in str(e) or '535' in str(e):
                    self.stdout.write(self.style.WARNING('\n💡 Authentication Error Tips:'))
                    self.stdout.write('1. Verify the app password is correct')
                    self.stdout.write('2. Make sure you\'re using an App Password, not your regular password')
                    self.stdout.write('3. Check if 2FA is enabled on your Zoho account')
                    self.stdout.write('4. Verify the email address is correct')
                    self.stdout.write('5. Try generating a new app password in Zoho Mail settings')
                
                continue
        
        self.stdout.write(self.style.ERROR('\n❌ All configurations failed. Please check:'))
        self.stdout.write('1. Your Zoho Mail account settings')
        self.stdout.write('2. App password is correctly generated')
        self.stdout.write('3. Email address is correct')
        self.stdout.write('4. Your Zoho account allows SMTP access')

