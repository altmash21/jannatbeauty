from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from accounts.models import Profile, SellerProfile

class Command(BaseCommand):
    help = "Create a test seller user and assign them to Sellers group"

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='testseller', help='Username for the test seller')
        parser.add_argument('--password', type=str, default='testpass123', help='Password for the test seller')
        parser.add_argument('--email', type=str, default='testseller@example.com', help='Email for the test seller')

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        password = kwargs['password']
        email = kwargs['email']
        
        # Create or get the user
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': 'Test',
                'last_name': 'Seller'
            }
        )
        
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Created new user: {username}'))
        else:
            self.stdout.write(self.style.WARNING(f'User {username} already exists'))
        
        # Set user role to seller
        profile = user.profile
        profile.role = 'seller'
        profile.save()
        self.stdout.write(self.style.SUCCESS(f'Set user role to seller'))
        
        # Create or update seller profile
        seller_profile, created = SellerProfile.objects.get_or_create(
            user=user,
            defaults={
                'business_name': f'{username} Business',
                'business_description': 'Test business for selling products',
                'business_address': '123 Business St, Business City',
                'business_phone': '+1234567890',
                'business_email': email,
                'approval_status': 'approved'
            }
        )
        
        if not created:
            seller_profile.approval_status = 'approved'
            seller_profile.save()
        
        self.stdout.write(self.style.SUCCESS(f'Created/updated seller profile'))
        
        # Add user to Sellers group
        sellers_group, _ = Group.objects.get_or_create(name='Sellers')
        user.groups.add(sellers_group)
        self.stdout.write(self.style.SUCCESS(f'Added user to Sellers group'))
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Test seller setup complete!\n'
                f'Username: {username}\n'
                f'Password: {password}\n'
                f'Email: {email}\n'
                f'Role: Seller\n'
                f'Status: Approved'
            )
        )