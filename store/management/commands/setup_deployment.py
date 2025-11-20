from django.core.management.base import BaseCommand
from django.core.management import execute_from_command_line
import os
import sys


class Command(BaseCommand):
    help = 'Setup the project for deployment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--environment',
            type=str,
            default='local',
            choices=['local', 'production'],
            help='Specify the environment (local/production)',
        )

    def handle(self, *args, **options):
        environment = options['environment']
        
        self.stdout.write(
            self.style.SUCCESS(f'🚀 Setting up Jannat Beauty for {environment} environment...')
        )

        if environment == 'production':
            self.setup_production()
        else:
            self.setup_local()

        self.stdout.write(
            self.style.SUCCESS('✅ Setup completed successfully!')
        )

    def setup_local(self):
        """Setup for local development"""
        self.stdout.write('Setting up for local development...')
        
        # Check if .env exists
        if not os.path.exists('.env'):
            self.stdout.write(
                self.style.WARNING('⚠️  .env file not found. Copying from .env.example...')
            )
            if os.path.exists('.env.example'):
                import shutil
                shutil.copy('.env.example', '.env')
                self.stdout.write(
                    self.style.SUCCESS('📋 .env file created from .env.example')
                )
                self.stdout.write(
                    self.style.WARNING('⚠️  Please update .env with your local settings!')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('❌ .env.example not found!')
                )
                return

        # Run migrations
        self.stdout.write('Running migrations...')
        execute_from_command_line(['manage.py', 'migrate'])

        # Collect static files
        self.stdout.write('Collecting static files...')
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])

        self.stdout.write(
            self.style.SUCCESS('🎉 Local development setup complete!')
        )
        self.stdout.write('Run: python manage.py runserver')

    def setup_production(self):
        """Setup for production"""
        self.stdout.write('Setting up for production deployment...')
        
        # Check if .env exists
        if not os.path.exists('.env'):
            self.stdout.write(
                self.style.ERROR('❌ .env file required for production!')
            )
            self.stdout.write('Please create .env file with production settings.')
            return

        # Run migrations
        self.stdout.write('Running migrations...')
        execute_from_command_line(['manage.py', 'migrate'])

        # Collect static files
        self.stdout.write('Collecting static files...')
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])

        # Create logs directory
        os.makedirs('logs', exist_ok=True)

        self.stdout.write(
            self.style.SUCCESS('🎉 Production setup complete!')
        )
        self.stdout.write('Configure your web server and start the application.')