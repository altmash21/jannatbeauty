from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from coupons.models import Coupon


class Command(BaseCommand):
    help = 'Create sample coupons'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        
        sample_coupons = [
            {
                'code': 'WELCOME10',
                'discount_type': 'percentage',
                'discount_value': 10,
                'min_purchase_amount': 0,
                'max_discount_amount': 100,
                'valid_from': now,
                'valid_to': now + timedelta(days=30),
                'usage_limit': 100,
            },
            {
                'code': 'RAMADAN20',
                'discount_type': 'percentage',
                'discount_value': 20,
                'min_purchase_amount': 500,
                'max_discount_amount': 200,
                'valid_from': now,
                'valid_to': now + timedelta(days=60),
                'usage_limit': 50,
            },
            {
                'code': 'SAVE50',
                'discount_type': 'fixed',
                'discount_value': 50,
                'min_purchase_amount': 300,
                'valid_from': now,
                'valid_to': now + timedelta(days=90),
                'usage_limit': None,
            },
            {
                'code': 'FIRSTORDER',
                'discount_type': 'percentage',
                'discount_value': 15,
                'min_purchase_amount': 200,
                'max_discount_amount': 150,
                'valid_from': now,
                'valid_to': now + timedelta(days=365),
                'usage_limit': 200,
            },
        ]

        created_count = 0
        for coupon_data in sample_coupons:
            coupon, created = Coupon.objects.get_or_create(
                code=coupon_data['code'],
                defaults=coupon_data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created coupon: {coupon.code} - {coupon.discount_value}{"%" if coupon.discount_type == "percentage" else " fixed"}'))

        if created_count > 0:
            self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created {created_count} coupons!'))
        else:
            self.stdout.write(self.style.WARNING('All sample coupons already exist.'))
