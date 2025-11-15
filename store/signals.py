from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Product

def create_seller_group_and_permissions(sender, **kwargs):
    """Create the Sellers group and assign permissions"""
    seller_group, created = Group.objects.get_or_create(name="Sellers")

    # Get the content type for Product model
    content_type = ContentType.objects.get_for_model(Product)
    
    # Add the "can_add_product" permission to the group
    add_permission, _ = Permission.objects.get_or_create(
        codename="can_add_product",
        content_type=content_type,
        defaults={'name': 'Can add product'}
    )
    seller_group.permissions.add(add_permission)
    
    # Add the "can_approve_product" permission to admin-like groups
    approve_permission, _ = Permission.objects.get_or_create(
        codename="can_approve_product",
        content_type=content_type,
        defaults={'name': 'Can approve product'}
    )
    
    # Create admin group if it doesn't exist
    admin_group, created = Group.objects.get_or_create(name="Admins")
    admin_group.permissions.add(approve_permission)


@receiver(post_save, sender=Product)
def auto_approve_admin_products(sender, instance, created, **kwargs):
    """Automatically approve products created by superusers"""
    if created and instance.seller and instance.seller.is_superuser:
        instance.approved = True
        Product.objects.filter(pk=instance.pk).update(approved=True)