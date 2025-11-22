# Generated manually for adding allowed_major_categories field to SellerProfile

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_registrationotp'),
    ]

    operations = [
        migrations.AddField(
            model_name='sellerprofile',
            name='allowed_major_categories',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='List of major categories this seller can manage (e.g., ["new_arrivals", "featured", "best_selling"]). Empty list means all categories.'
            ),
        ),
    ]
