from django.urls import path
from . import views

app_name = 'coupons'

urlpatterns = [
    path('apply/', views.apply_coupon, name='apply_coupon'),
    path('remove/', views.remove_coupon, name='remove_coupon'),
    path('get-discount/', views.get_discount_popup, name='get_discount_popup'),
]
