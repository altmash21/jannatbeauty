"""
Clean URL Configuration for Accounts App
Separated customer and seller routes
"""
from django.urls import path
from . import views_new as views, views_address

app_name = 'accounts'

urlpatterns = [
    # ============================================================================
    # AUTHENTICATION
    # ============================================================================
    path('register/customer/', views.register_customer, name='register_customer'),
    path('register/seller/', views.register_seller, name='register_seller'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # AJAX: Check if email is taken
    path('ajax/check-email/', views.check_email_taken, name='check_email_taken'),
    
    # Password Reset
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),
    
    # Registration OTP
    path('verify-registration-otp/', views.verify_registration_otp, name='verify_registration_otp'),

    # Resend OTP endpoints (AJAX)
    path('resend-registration-otp/', views.resend_registration_otp, name='resend_registration_otp'),
    path('resend-passwordreset-otp/', views.resend_passwordreset_otp, name='resend_passwordreset_otp'),
    
    # ============================================================================
    # CUSTOMER ROUTES - /accounts/customer/*
    # ============================================================================
    path('customer/dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('customer/profile/', views.customer_profile, name='customer_profile'),
    path('customer/orders/', views.customer_orders, name='customer_orders'),
    path('customer/notifications/', views.customer_notifications, name='customer_notifications'),
    path('customer/addresses/', views.customer_addresses, name='customer_addresses'),
    
    # ============================================================================
    # ADDRESS MANAGEMENT
    # ============================================================================
    path('address/save/', views_address.save_address, name='save_address'),
    path('address/select/', views_address.select_address, name='select_address'),
    
    # ============================================================================
    # LEGACY ROUTES - For backward compatibility
    # ============================================================================
    path('profile/', views.customer_profile, name='profile'),
    path('orders/', views.customer_orders, name='order_history'),
    
    # ============================================================================
    # SELLER ROUTES - /accounts/seller/*
    # ============================================================================
    path('seller/dashboard/', views.seller_dashboard, name='seller_dashboard'),
    path('seller/products/', views.seller_products, name='seller_products'),
    path('seller/orders/', views.seller_orders, name='seller_orders'),
    path('seller/analytics/', views.seller_analytics, name='seller_analytics'),
    path('seller/profile/', views.seller_profile, name='seller_profile'),
]
