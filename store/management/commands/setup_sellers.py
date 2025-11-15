from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from store.models import Product

class Command(BaseCommand):
    help = "Set up Sellers group and permissions"

    def handle(self, *args, **kwargs):
        seller_group, created = Group.objects.get_or_create(name="Sellers")
        content_type = ContentType.objects.get_for_model(Product)
        permission, _ = Permission.objects.get_or_create(
            codename="can_add_product",
            content_type=content_type,
        )
        seller_group.permissions.add(permission)
        self.stdout.write(self.style.SUCCESS("Sellers group and permissions set up successfully."))