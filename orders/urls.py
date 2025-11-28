from django.urls import path
from . import views, views_checkout
from .views_pincode import check_pincode

app_name = 'orders'

urlpatterns = [
    # Checkout and payment
    path('checkout/', views_checkout.checkout, name='checkout'),
    path('cashfree/return/', views_checkout.cashfree_return, name='cashfree_return'),
    path('cashfree/webhook/', views_checkout.cashfree_webhook, name='cashfree_webhook'),
    path('cashfree/status/', views_checkout.cashfree_status, name='cashfree_status'),
    path('payment-failed/', views_checkout.payment_failed, name='payment_failed'),
    path('confirmation/<uuid:order_id>/', views_checkout.confirmation, name='confirmation'),
    
    # Order management
    path('track/', views.track_order, name='track_order'),
    path('<str:order_id>/', views.order_detail, name='order_detail'),
    
    # Seller routes
    path('seller/orders/', views.seller_orders, name='seller_orders'),
    path('seller/orders/<uuid:order_id>/<int:item_id>/update/', views.update_order_status, name='update_order_status'),
    path('seller/orders/<uuid:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    
    # Shiprocket routes
    path('<uuid:order_id>/shiprocket/create/', views.create_shiprocket_order, name='create_shiprocket_order'),
    path('<uuid:order_id>/track/', views.track_shipment, name='track_shipment'),
    path('shiprocket/webhook/', views.shiprocket_webhook, name='shiprocket_webhook'),
    
    # AJAX endpoints
    path('ajax/check-pincode/', check_pincode, name='check_pincode'),
]