from django.contrib import admin
from .models import OfferBanner

@admin.register(OfferBanner)
class OfferBannerAdmin(admin.ModelAdmin):
    list_display = ('text', 'active', 'expires_at', 'created', 'updated')
    list_filter = ('active',)
    search_fields = ('text',)
    ordering = ('-created',)
