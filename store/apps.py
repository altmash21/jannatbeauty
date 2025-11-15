from django.apps import AppConfig
from django.db.models.signals import post_migrate


class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'store'

    def ready(self):
        from .signals import create_seller_group_and_permissions

        # Connect signal to create seller group and permissions after migration
        post_migrate.connect(create_seller_group_and_permissions, sender=self)
