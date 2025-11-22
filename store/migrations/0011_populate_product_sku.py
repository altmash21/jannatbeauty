# Generated manually for populating SKU field for existing products

from django.db import migrations


def populate_sku(apps, schema_editor):
    """Populate SKU for existing products"""
    Product = apps.get_model('store', 'Product')
    # Update all products that don't have SKU using bulk_update for efficiency
    products_to_update = []
    for product in Product.objects.filter(sku=''):
        product.sku = f"PROD-{product.id:05d}"
        products_to_update.append(product)
    
    # Bulk update all at once
    if products_to_update:
        Product.objects.bulk_update(products_to_update, ['sku'])


def reverse_populate_sku(apps, schema_editor):
    """Reverse migration - set SKU to empty for all products"""
    Product = apps.get_model('store', 'Product')
    Product.objects.update(sku='')


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0010_product_sku'),
    ]

    operations = [
        migrations.RunPython(populate_sku, reverse_populate_sku),
    ]

