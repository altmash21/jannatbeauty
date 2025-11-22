"""Signals for accounts app - handle email notifications"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import SellerProfile
from .utils import send_seller_approval_email

# Track previous approval status to detect changes
_previous_seller_status = {}


@receiver(pre_save, sender=SellerProfile)
def save_previous_seller_status(sender, instance, **kwargs):
    """Save previous approval status before save"""
    if instance.pk:
        try:
            old_instance = SellerProfile.objects.get(pk=instance.pk)
            _previous_seller_status[instance.pk] = old_instance.approval_status
        except SellerProfile.DoesNotExist:
            pass


@receiver(post_save, sender=SellerProfile)
def send_seller_status_email(sender, instance, created, **kwargs):
    """Send email when seller approval status changes"""
    if not created:
        previous_status = _previous_seller_status.get(instance.pk)
        status_changed = previous_status and previous_status != instance.approval_status
        
        if status_changed and instance.approval_status in ['approved', 'rejected', 'suspended']:
            try:
                send_seller_approval_email(instance, instance.approval_status)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Failed to send seller status email to {instance.id}: {str(e)}')
        
        # Clean up previous status tracking
        if instance.pk in _previous_seller_status:
            del _previous_seller_status[instance.pk]

