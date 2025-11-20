from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('store', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='major_category',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('new_arrivals', 'New Arrivals'),
                    ('featured', 'Featured'),
                    ('best_selling', 'Best Selling'),
                    ('none', 'None'),
                ],
                default='none',
                blank=True,
            ),
        ),
    ]
