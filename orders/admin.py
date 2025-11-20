from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from django.conf import settings
from .models import Order, OrderItem
from .shiprocket import ShiprocketAPI


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'full_name', 'email', 'order_status', 'paid', 'shiprocket_order_id', 'awb_code', 'create_shipment_link', 'total_amount', 'created']
    list_filter = ['paid', 'order_status', 'created', 'updated']
    list_editable = ['order_status', 'paid']
    search_fields = ['id', 'first_name', 'last_name', 'email', 'shiprocket_order_id', 'awb_code']
    inlines = [OrderItemInline]
    readonly_fields = ['id', 'created', 'updated', 'shiprocket_order_id', 'shiprocket_shipment_id', 'awb_code', 'courier_name', 'create_shipment_button']
    actions = ['create_shipment_action']
    
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
        ('Shiprocket Integration', {
            'fields': ('create_shipment_button', 'shiprocket_order_id', 'shiprocket_shipment_id', 'awb_code', 'courier_name'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    def create_shipment_link(self, obj):
        """Display a button to create shipment in list view"""
        if not obj:
            return "-"
        # Show COD for unpaid COD orders
        if not obj.paid and getattr(obj, 'payment_method', None) == 'cod':
            if obj.shiprocket_order_id:
                return format_html(
                    '<span style="color: #28a745;">✓ Created</span><br>'
                    '<small style="color: #666;">ID: {}</small>',
                    obj.shiprocket_order_id
                )
            if not getattr(settings, 'SHIPROCKET_ENABLED', False):
                return format_html('<span style="color: #999;">Disabled</span>')
            return format_html(
                '<a href="/admin/orders/order/{}/create-shipment/" class="button" style="background-color: #28a745; color: white; padding: 6px 12px; text-decoration: none; border-radius: 4px; display: inline-block; font-size: 12px;">Create Shipment (COD)</a>',
                obj.id
            )
        # Prepaid logic
        if not obj.paid:
            return format_html('<span style="color: #999;">Not Paid</span>')
        if obj.shiprocket_order_id:
            return format_html(
                '<span style="color: #28a745;">✓ Created</span><br>'
                '<small style="color: #666;">ID: {}</small>',
                obj.shiprocket_order_id
            )
        if not getattr(settings, 'SHIPROCKET_ENABLED', False):
            return format_html('<span style="color: #999;">Disabled</span>')
        return format_html(
            '<a href="/admin/orders/order/{}/create-shipment/" class="button" style="background-color: #28a745; color: white; padding: 6px 12px; text-decoration: none; border-radius: 4px; display: inline-block; font-size: 12px;">Create Shipment</a>',
            obj.id
        )
    create_shipment_link.short_description = "Shipment"
    
    def create_shipment_button(self, obj):
        """Display a button to create shipment in detail view"""
        if not obj:
            return "Save order first to create shipment"
        # Allow shipment for unpaid COD orders
        if not obj.paid and getattr(obj, 'payment_method', None) == 'cod':
            if obj.shiprocket_order_id:
                return f"Shipment already created. Order ID: {obj.shiprocket_order_id}"
            if not getattr(settings, 'SHIPROCKET_ENABLED', False):
                return "Shiprocket integration is disabled"
            return format_html(
                '<a href="/admin/orders/order/{}/create-shipment/" class="button" style="background-color: #28a745; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px; display: inline-block;">Create Shipment (COD)</a>',
                obj.id
            )
        # Prepaid logic
        if not obj.paid:
            return "Order must be paid before creating shipment"
        if obj.shiprocket_order_id:
            return f"Shipment already created. Order ID: {obj.shiprocket_order_id}"
        if not getattr(settings, 'SHIPROCKET_ENABLED', False):
            return "Shiprocket integration is disabled"
        return format_html(
            '<a href="/admin/orders/order/{}/create-shipment/" class="button" style="background-color: #28a745; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px; display: inline-block;">Create Shipment</a>',
            obj.id
        )
    create_shipment_button.short_description = "Create Shipment"
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<uuid:order_id>/create-shipment/', self.admin_site.admin_view(self.create_shipment_view), name='orders_order_create_shipment'),
        ]
        return custom_urls + urls
    
    def create_shipment_view(self, request, order_id):
        """Admin view to create shipment for an order"""
        from django.shortcuts import redirect, get_object_or_404
        order = get_object_or_404(Order, id=order_id)
        # Allow shipment for unpaid COD orders
        if not order.paid and getattr(order, 'payment_method', None) != 'cod':
            messages.error(request, 'Order must be paid before creating shipment.')
            return redirect('admin:orders_order_change', order.id)
        if order.shiprocket_order_id:
            messages.warning(request, f'Shipment already created. Order ID: {order.shiprocket_order_id}')
            return redirect('admin:orders_order_change', order.id)
        if not getattr(settings, 'SHIPROCKET_ENABLED', False):
            messages.error(request, 'Shiprocket integration is currently disabled.')
            return redirect('admin:orders_order_change', order.id)
        try:
            # Create Shiprocket order
            shiprocket = ShiprocketAPI()
            result = shiprocket.create_order(order)
            if result.get('order_id'):
                order.shiprocket_order_id = result.get('order_id')
                order.shiprocket_shipment_id = result.get('shipment_id')
                
                # Try to get AWB code if available in response
                if result.get('awb_code'):
                    order.awb_code = result.get('awb_code')
                
                # Get courier name if available
                if result.get('courier_name'):
                    order.courier_name = result.get('courier_name')
                
                # Update order status to processing
                order.order_status = 'processing'
                order.save()
                
                messages.success(request, f'Shipment created successfully! Order ID: {result.get("order_id")}')
                
                if not order.awb_code:
                    messages.info(request, 'AWB will be assigned when courier picks up the package.')
            else:
                error_msg = result.get('error', 'Unknown error')
                messages.error(request, f'Failed to create shipment: {error_msg}')
        except Exception as e:
            messages.error(request, f'Error creating shipment: {str(e)}')
        
        return redirect('admin:orders_order_change', order.id)
    
    def create_shipment_action(self, request, queryset):
        """Admin action to create shipments for selected orders"""
        if not getattr(settings, 'SHIPROCKET_ENABLED', False):
            messages.error(request, 'Shiprocket integration is currently disabled.')
            return
        
        created_count = 0
        skipped_count = 0
        error_count = 0
        
        for order in queryset:
            if not order.paid:
                skipped_count += 1
                continue
            
            if order.shiprocket_order_id:
                skipped_count += 1
                continue
            
            try:
                shiprocket = ShiprocketAPI()
                result = shiprocket.create_order(order)
                
                if result.get('order_id'):
                    order.shiprocket_order_id = result.get('order_id')
                    order.shiprocket_shipment_id = result.get('shipment_id')
                    
                    if result.get('awb_code'):
                        order.awb_code = result.get('awb_code')
                    
                    if result.get('courier_name'):
                        order.courier_name = result.get('courier_name')
                    
                    order.order_status = 'processing'
                    order.save()
                    created_count += 1
                else:
                    error_count += 1
            except Exception as e:
                error_count += 1
        
        if created_count > 0:
            messages.success(request, f'Successfully created {created_count} shipment(s).')
        if skipped_count > 0:
            messages.warning(request, f'Skipped {skipped_count} order(s) (already shipped or not paid).')
        if error_count > 0:
            messages.error(request, f'Failed to create {error_count} shipment(s).')
    
    create_shipment_action.short_description = "Create shipment for selected orders"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'price', 'quantity']
    list_filter = ['order__created']
    search_fields = ['order__id', 'product__name']
