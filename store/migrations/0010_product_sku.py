# Generated manually for adding SKU field to Product model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0009_lead'),
    ]

    operations = [
        # Step 1: Add SKU field WITHOUT unique constraint first
        migrations.AddField(
            model_name='product',
            name='sku',
            field=models.CharField(blank=True, db_index=True, help_text='Stock Keeping Unit - Leave blank to auto-generate', max_length=100, default=''),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['sku'], name='store_produ_sku_idx'),
        ),
    ]

