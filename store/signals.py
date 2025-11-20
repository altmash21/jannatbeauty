from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Product, Category

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


def _invalidate_product_cache(product_slug=None, category_id=None):
    """Helper function to invalidate product-related cache"""
    if product_slug:
        cache.delete(f'product_detail_{product_slug}')
    
    # Clear home page caches
    cache.delete('home_new_arrivals')
    cache.delete('home_featured_products')
    cache.delete('home_best_selling_products')
    
    # Clear category caches
    cache.delete('all_categories')
    cache.delete('home_categories')
    
    # Clear related products cache for this category
    # Note: We can't use delete_pattern with standard cache API,
    # so we'll use a version-based approach or clear on category change
    if category_id:
        # Try to use django-redis pattern deletion if available
        try:
            from django_redis import get_redis_connection
            redis_client = get_redis_connection("default")
            pattern = f'ecommerce:related_products_{category_id}_*'
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
        except Exception:
            # If Redis pattern deletion fails, just clear all related product caches
            # This is acceptable as related products cache is not critical
            pass


@receiver(post_save, sender=Product)
def auto_approve_admin_products(sender, instance, created, **kwargs):
    """Automatically approve products created by superusers"""
    if created and instance.seller and instance.seller.is_superuser:
        instance.approved = True
        Product.objects.filter(pk=instance.pk).update(approved=True)
    
    # Invalidate cache when product is saved/updated
    _invalidate_product_cache(product_slug=instance.slug, category_id=instance.category_id)


@receiver(post_delete, sender=Product)
def invalidate_cache_on_delete(sender, instance, **kwargs):
    """Invalidate cache when product is deleted"""
    _invalidate_product_cache(product_slug=instance.slug, category_id=instance.category_id)


@receiver(post_save, sender=Category)
def invalidate_cache_on_category_save(sender, instance, **kwargs):
    """Invalidate cache when category is saved"""
    cache.delete('all_categories')
    cache.delete('home_categories')