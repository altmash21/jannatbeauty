from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Notification


class Command(BaseCommand):
    help = 'Create sample notifications for testing'

    def handle(self, *args, **kwargs):
        # Get the first user (or you can specify a username)
        try:
            user = User.objects.first()
            if not user:
                self.stdout.write(self.style.ERROR('No users found. Please create a user first.'))
                return
            
            # Create sample notifications
            notifications_data = [
                {
                    'notification_type': 'order',
                    'title': 'Order Shipped!',
                    'message': 'Your order #12345 has been shipped and is on its way to you.',
                    'link': '/orders/order/12345/'
                },
                {
                    'notification_type': 'promotion',
                    'title': 'Special Offer - 20% Off!',
                    'message': 'Get 20% off on all electronics this weekend. Use code: TECH20',
                    'link': '/store/category/electronics/'
                },
                {
                    'notification_type': 'product',
                    'title': 'Product Back in Stock',
                    'message': 'Good news! The product you were interested in is now back in stock.',
                    'link': '/store/products/'
                },
                {
                    'notification_type': 'system',
                    'title': 'Welcome to Our Store!',
                    'message': 'Thank you for joining us. Explore our wide range of products and enjoy shopping!',
                    'link': '/store/'
                },
                {
                    'notification_type': 'account',
                    'title': 'Profile Updated',
                    'message': 'Your profile information has been successfully updated.',
                    'link': '/accounts/customer/profile/'
                },
            ]
            
            created_count = 0
            for data in notifications_data:
                Notification.objects.create(
                    user=user,
                    **data
                )
                created_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created {created_count} sample notifications for user: {user.username}'
                )
            )
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
