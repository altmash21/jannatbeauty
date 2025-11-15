from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile, SellerProfile, Notification


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
             'business_email', 'tax_id', 'bank_account', 'approval_status', 'commission_rate']
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
    list_display = ['business_name', 'user', 'approval_status', 'commission_rate', 'created']
    list_filter = ['approval_status', 'created', 'updated']
    search_fields = ['business_name', 'user__username', 'business_email', 'tax_id']
    readonly_fields = ['created', 'updated']
    list_editable = ['approval_status', 'commission_rate']
    
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
        ('Timestamps', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_sellers', 'reject_sellers', 'suspend_sellers']
    
    def approve_sellers(self, request, queryset):
        updated = queryset.update(approval_status='approved')
        self.message_user(request, f'{updated} sellers approved successfully.')
    approve_sellers.short_description = "Approve selected sellers"
    
    def reject_sellers(self, request, queryset):
        updated = queryset.update(approval_status='rejected')
        self.message_user(request, f'{updated} sellers rejected.')
    reject_sellers.short_description = "Reject selected sellers"
    
    def suspend_sellers(self, request, queryset):
        updated = queryset.update(approval_status='suspended')
        self.message_user(request, f'{updated} sellers suspended.')
    suspend_sellers.short_description = "Suspend selected sellers"


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
