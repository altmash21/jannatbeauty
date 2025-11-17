from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from accounts.models import Notification


@receiver(post_save, sender=Order)
def create_order_notification(sender, instance, created, **kwargs):
    """Create notification when order is created or status changes"""
    
    if created:
        # New order notification
        Notification.objects.create(
            user=instance.user,
            notification_type='order',
            title=f'Order Placed Successfully!',
            message=f'Your order #{str(instance.id)[:8]} has been placed successfully. Total: ₹{instance.total_amount}',
            link=f'/orders/order/{instance.id}/'
        )
    else:
        # Order status update notification
        status_messages = {
            'processing': 'Your order is now being processed.',
            'shipped': 'Great news! Your order has been shipped.',
            'delivered': 'Your order has been delivered. Enjoy your purchase!',
            'cancelled': 'Your order has been cancelled.',
        }
        
        if instance.order_status in status_messages:
            Notification.objects.create(
                user=instance.user,
                notification_type='order',
                title=f'Order {instance.order_status.title()}',
                message=f'Order #{str(instance.id)[:8]}: {status_messages[instance.order_status]}',
                link=f'/orders/order/{instance.id}/'
            )
