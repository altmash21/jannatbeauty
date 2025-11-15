from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'full_name', 'email', 'order_status', 'paid', 'total_amount', 'created']
    list_filter = ['paid', 'order_status', 'created', 'updated']
    list_editable = ['order_status', 'paid']
    search_fields = ['id', 'first_name', 'last_name', 'email']
    inlines = [OrderItemInline]
    readonly_fields = ['id', 'created', 'updated']
    
    fieldsets = (
        (None, {
            'fields': ('id', 'user', 'order_status', 'paid', 'total_amount')
        }),
        ('Customer Information', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Shipping Information', {
            'fields': ('address', 'city', 'state', 'zipcode')
        }),
        ('Timestamps', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'price', 'quantity']
    list_filter = ['order__created']
    search_fields = ['order__id', 'product__name']
