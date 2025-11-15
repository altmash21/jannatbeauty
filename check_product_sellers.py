import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Product
from django.contrib.auth.models import User

products = Product.objects.all()
print(f'Total products: {products.count()}\n')

for p in products:
    print(f'Product: {p.name}')
    print(f'  - Seller ID: {p.seller.id}')
    print(f'  - Seller Username: {p.seller.username}')
    print(f'  - Is Superuser: {p.seller.is_superuser}')
    print()

# Check all users
print('\n--- All Users ---')
users = User.objects.all()
for u in users:
    print(f'ID: {u.id}, Username: {u.username}, Superuser: {u.is_superuser}')
    if hasattr(u, 'seller_profile'):
        print(f'  - Has seller profile: {u.seller_profile.approval_status}')
