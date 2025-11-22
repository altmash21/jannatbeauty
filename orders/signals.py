from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Order
from accounts.models import Notification
from .utils import (
    send_order_confirmation_email,
    send_order_status_update_email,
    send_new_order_notification_to_seller,
    send_order_notification_to_admin
)


# Track previous order status to detect changes
_previous_status = {}


@receiver(pre_save, sender=Order)
def save_previous_status(sender, instance, **kwargs):
    """Save previous order status before save"""
    if instance.pk:
        try:
            old_instance = Order.objects.get(pk=instance.pk)
            _previous_status[instance.pk] = old_instance.order_status
        except Order.DoesNotExist:
            pass


@receiver(post_save, sender=Order)
def create_order_notification(sender, instance, created, **kwargs):
    """Create notification and send emails when order is created or status changes"""
    
    if created:
        # New order notification (in-app)
        if instance.user:
            Notification.objects.create(
                user=instance.user,
                notification_type='order',
                title=f'Order Placed Successfully!',
                message=f'Your order #{instance.order_number or str(instance.id)[:8]} has been placed successfully. Total: ₹{instance.total_amount}',
                link=f'/orders/order/{instance.id}/'
            )
        
        # Send order confirmation email to customer
        try:
            send_order_confirmation_email(instance)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Failed to send order confirmation email: {str(e)}')
        
        # Send order notification email to sellers
        try:
            send_new_order_notification_to_seller(instance)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Failed to send order notification to sellers: {str(e)}')
        
        # Send order notification email to admin
        try:
            send_order_notification_to_admin(instance)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Failed to send order notification to admin: {str(e)}')
            
    else:
        # Check if order status changed
        previous_status = _previous_status.get(instance.pk)
        status_changed = previous_status and previous_status != instance.order_status
        
        # Also check if order_status was in update_fields
        update_fields = kwargs.get('update_fields')
        status_in_update = update_fields and 'order_status' in update_fields
        
        if status_changed or (status_in_update and previous_status != instance.order_status):
            # Order status update notification (in-app)
            status_messages = {
                'processing': 'Your order is now being processed.',
                'shipped': 'Great news! Your order has been shipped.',
                'delivered': 'Your order has been delivered. Enjoy your purchase!',
                'cancelled': 'Your order has been cancelled.',
            }
            
            if instance.order_status in status_messages and instance.user:
                Notification.objects.create(
                    user=instance.user,
                    notification_type='order',
                    title=f'Order {instance.order_status.title()}',
                    message=f'Order #{instance.order_number or str(instance.id)[:8]}: {status_messages[instance.order_status]}',
                    link=f'/orders/order/{instance.id}/'
                )
            
            # Send order status update email to customer
            if instance.order_status in status_messages:
                try:
                    send_order_status_update_email(instance)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f'Failed to send order status update email: {str(e)}')
        
        # Clean up previous status tracking
        if instance.pk in _previous_status:
            del _previous_status[instance.pk]
