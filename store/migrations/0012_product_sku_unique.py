# Generated manually for adding unique constraint to SKU field after populating

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0011_populate_product_sku'),
    ]

    operations = [
        # Step 3: Add unique constraint after all SKUs are populated
        # Django will automatically handle the index when unique=True is added
        migrations.AlterField(
            model_name='product',
            name='sku',
            field=models.CharField(blank=True, db_index=True, help_text='Stock Keeping Unit - Leave blank to auto-generate', max_length=100, unique=True),
        ),
    ]

