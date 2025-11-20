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
    list_display = ['name', 'seller', 'category', 'major_category', 'price', 'stock', 'available', 'approved', 'created']
    list_filter = ['available', 'approved', 'featured', 'created', 'updated', 'category', 'major_category', 'seller']
    list_editable = ['price', 'stock', 'available', 'approved']
    search_fields = ['name', 'description', 'seller__username', 'seller__seller_profile__business_name']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created', 'updated']
    inlines = [ProductImageInline]
    
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'seller', 'category', 'major_category', 'description')
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
    list_display = ['name', 'mobile', 'email_sent', 'created']
    list_filter = ['email_sent', 'created']
    search_fields = ['name', 'mobile']
    readonly_fields = ['created', 'updated']
    list_editable = ['email_sent']
