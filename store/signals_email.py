"""Signals for product approval email notifications"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Product
from .utils import send_product_approval_email

# Track previous approval status to detect changes
_previous_product_approved = {}


@receiver(pre_save, sender=Product)
def save_previous_product_approved(sender, instance, **kwargs):
    """Save previous approval status before save"""
    if instance.pk:
        try:
            old_instance = Product.objects.get(pk=instance.pk)
            _previous_product_approved[instance.pk] = old_instance.approved
        except Product.DoesNotExist:
            pass


@receiver(post_save, sender=Product)
def send_product_approval_status_email(sender, instance, created, **kwargs):
    """Send email when product approval status changes (only if not auto-approved)"""
    if not created:
        previous_approved = _previous_product_approved.get(instance.pk)
        approval_changed = previous_approved is not None and previous_approved != instance.approved
        
        # Only send email if approval status actually changed (not on auto-approve)
        if approval_changed:
            try:
                send_product_approval_email(instance, instance.approved)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Failed to send product approval email for product {instance.id}: {str(e)}')
        
        # Clean up previous status tracking
        if instance.pk in _previous_product_approved:
            del _previous_product_approved[instance.pk]

