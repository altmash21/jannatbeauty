from django.contrib import admin
from .models import Coupon, CouponUsage

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_value', 'active', 'valid_from', 'valid_to', 'usage_count']
    list_filter = ['active', 'discount_type', 'created_at']
    search_fields = ['code']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ['coupon', 'user', 'discount_amount', 'used_at']
    list_filter = ['used_at']
    search_fields = ['coupon__code', 'user__username']
    date_hierarchy = 'used_at'
    ordering = ['-used_at']
