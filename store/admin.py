from django.contrib import admin
from .models import Category, Product, ProductImage, SubCategory, Lead


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created', 'updated']
    list_filter = ['created', 'updated']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created', 'updated']


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'seller', 'category', 'major_category', 'price', 'stock', 'available', 'approved', 'created']
    list_filter = ['available', 'approved', 'featured', 'created', 'updated', 'category', 'major_category', 'seller']
    list_editable = ['price', 'stock', 'available', 'approved']
    search_fields = ['name', 'sku', 'description', 'seller__username', 'seller__seller_profile__business_name']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created', 'updated']
    inlines = [ProductImageInline]
    
    fieldsets = (
        (None, {
            'fields': ('name', 'sku', 'slug', 'seller', 'category', 'major_category', 'description')
        }),
        ('Pricing', {
            'fields': ('price', 'compare_price')
        }),
        ('Inventory & Status', {
            'fields': ('stock', 'available', 'approved', 'featured')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Timestamps', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.seller:
            obj.seller = request.user
        
        # Track previous approval status to detect changes
        if change:
            old_obj = Product.objects.get(pk=obj.pk)
            old_approved = old_obj.approved
            new_approved = obj.approved
            
            # If approval status changed, send email
            if old_approved != new_approved:
                super().save_model(request, obj, form, change)
                try:
                    send_product_approval_email(obj, new_approved)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f'Failed to send product approval email for product {obj.id}: {str(e)}')
                return
        
        super().save_model(request, obj, form, change)


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'alt_text', 'created']
    list_filter = ['created']
    search_fields = ['product__name', 'alt_text']


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'category', 'created', 'updated']
    list_filter = ['created', 'updated', 'category']
    search_fields = ['name', 'description', 'category__name']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created', 'updated']


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['name', 'mobile', 'coupon_code', 'email_sent', 'created']
    list_filter = ['email_sent', 'created']
    search_fields = ['name', 'mobile', 'coupon_code']
    readonly_fields = ['created', 'updated']
    list_editable = ['email_sent']
