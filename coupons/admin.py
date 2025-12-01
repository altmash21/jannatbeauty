from django.contrib import admin
from .models import Coupon, CouponUsage

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_value', 'active', 'valid_from', 'valid_to', 'usage_count', 'show_on_banner']
    list_filter = ['active', 'discount_type', 'created_at', 'show_on_banner']
    search_fields = ['code']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    fields = ('code', 'discount_type', 'discount_value', 'min_purchase_amount', 'max_discount_amount', 'usage_limit', 'valid_from', 'valid_to', 'active', 'show_on_banner')

@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ['coupon', 'user', 'discount_amount', 'used_at']
    list_filter = ['used_at']
    search_fields = ['coupon__code', 'user__username']
    date_hierarchy = 'used_at'
    ordering = ['-used_at']
