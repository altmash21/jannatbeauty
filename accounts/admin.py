from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django import forms
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile, SellerProfile, Notification
from .forms import SellerProfileAdminForm
from .utils import send_seller_approval_email


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ['role', 'phone', 'address', 'city', 'state', 'zipcode', 'country']


class SellerProfileInline(admin.StackedInline):
    model = SellerProfile
    can_delete = False
    verbose_name_plural = 'Seller Profile'
    fields = ['business_name', 'business_description', 'business_address', 'business_phone', 
             'business_email', 'tax_id', 'bank_account', 'approval_status', 'commission_rate', 'allowed_major_categories']
    extra = 0


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    
    def get_inline_instances(self, request, obj=None):
        inline_instances = super().get_inline_instances(request, obj)
        
        # Only show SellerProfileInline for sellers
        if obj and hasattr(obj, 'profile') and obj.profile.is_seller:
            inline_instances.append(SellerProfileInline(self.model, self.admin_site))
        
        return inline_instances


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone', 'city', 'state', 'country', 'created']
    list_filter = ['role', 'country', 'state', 'created']
    search_fields = ['user__username', 'user__email', 'phone', 'city']
    readonly_fields = ['created', 'updated']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'role')
        }),
        ('Contact Information', {
            'fields': ('phone', 'address', 'city', 'state', 'zipcode', 'country')
        }),
        ('Timestamps', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    form = SellerProfileAdminForm
    list_display = ['business_name', 'user', 'approval_status', 'commission_rate', 'get_allowed_categories_display', 'created']
    list_filter = ['approval_status', 'created', 'updated']
    search_fields = ['business_name', 'user__username', 'business_email', 'tax_id']
    readonly_fields = ['created', 'updated']
    list_editable = ['approval_status', 'commission_rate']
    
    def get_allowed_categories_display(self, obj):
        """Display allowed major categories status"""
        if not obj.allowed_major_categories or len(obj.allowed_major_categories) == 0:
            return "Not Allowed"
        return "Allowed"
    get_allowed_categories_display.short_description = "Major Categories"
    
    fieldsets = (
        ('Business Information', {
            'fields': ('user', 'business_name', 'business_description')
        }),
        ('Contact Details', {
            'fields': ('business_address', 'business_phone', 'business_email')
        }),
        ('Business Details', {
            'fields': ('tax_id', 'bank_account')
        }),
        ('Status & Commission', {
            'fields': ('approval_status', 'commission_rate')
        }),
        ('Major Category Permissions', {
            'fields': ('allowed_major_categories',),
            'description': 'Select major categories this seller can manage. Leave all unchecked to restrict access (seller will not see major category field). Check categories to allow the seller to use them for their products.'
        }),
        ('Timestamps', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    
    actions = ['approve_sellers', 'reject_sellers', 'suspend_sellers']
    
    def approve_sellers(self, request, queryset):
        # Store seller profiles before update
        seller_profiles = list(queryset)
        updated = queryset.update(approval_status='approved')
        # Send email to each approved seller (reload from DB to get updated status)
        for seller_profile in seller_profiles:
            seller_profile.refresh_from_db()
            try:
                send_seller_approval_email(seller_profile, 'approved')
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Failed to send approval email to seller {seller_profile.id}: {str(e)}')
        self.message_user(request, f'{updated} sellers approved successfully.')
    approve_sellers.short_description = "Approve selected sellers"
    
    def reject_sellers(self, request, queryset):
        # Store seller profiles before update
        seller_profiles = list(queryset)
        updated = queryset.update(approval_status='rejected')
        # Send email to each rejected seller (reload from DB to get updated status)
        for seller_profile in seller_profiles:
            seller_profile.refresh_from_db()
            try:
                send_seller_approval_email(seller_profile, 'rejected')
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Failed to send rejection email to seller {seller_profile.id}: {str(e)}')
        self.message_user(request, f'{updated} sellers rejected.')
    reject_sellers.short_description = "Reject selected sellers"
    
    def suspend_sellers(self, request, queryset):
        # Store seller profiles before update
        seller_profiles = list(queryset)
        updated = queryset.update(approval_status='suspended')
        # Send email to each suspended seller (reload from DB to get updated status)
        for seller_profile in seller_profiles:
            seller_profile.refresh_from_db()
            try:
                send_seller_approval_email(seller_profile, 'suspended')
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Failed to send suspension email to seller {seller_profile.id}: {str(e)}')
        self.message_user(request, f'{updated} sellers suspended.')
    suspend_sellers.short_description = "Suspend selected sellers"
    
    def save_model(self, request, obj, form, change):
        """Send email when approval_status changes in admin"""
        if change:
            # Get previous approval_status from database
            old_obj = SellerProfile.objects.get(pk=obj.pk)
            old_status = old_obj.approval_status
            new_status = obj.approval_status
            
            # If approval_status changed, send email
            if old_status != new_status and new_status in ['approved', 'rejected', 'suspended']:
                super().save_model(request, obj, form, change)
                try:
                    send_seller_approval_email(obj, new_status)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f'Failed to send seller status email to {obj.id}: {str(e)}')
                return
        super().save_model(request, obj, form, change)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notification_type', 'is_read', 'created']
    list_filter = ['notification_type', 'is_read', 'created']
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = ['created']
    list_editable = ['is_read']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'notification_type', 'title', 'message', 'link')
        }),
        ('Status', {
            'fields': ('is_read', 'created')
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notifications marked as read.')
    mark_as_read.short_description = "Mark selected as read"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} notifications marked as unread.')
    mark_as_unread.short_description = "Mark selected as unread"
