from django.urls import path
from . import views
from .views_pincode import check_pincode

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('confirmation/<uuid:order_id>/', views.confirmation, name='confirmation'),
    path('<str:order_id>/', views.order_detail, name='order_detail'),
    path('track/', views.track_order, name='track_order'),
    path('seller/orders/', views.seller_orders, name='seller_orders'),
    path('seller/orders/<uuid:order_id>/<int:item_id>/update/', views.update_order_status, name='update_order_status'),
    path('cashfree/verify/', views.cashfree_verify, name='cashfree_verify'),
    # Shiprocket routes
    path('<uuid:order_id>/shiprocket/create/', views.create_shiprocket_order, name='create_shiprocket_order'),
    path('<uuid:order_id>/track/', views.track_shipment, name='track_shipment'),
    path('shiprocket/webhook/', views.shiprocket_webhook, name='shiprocket_webhook'),

    # Seller: Cancel order
    path('seller/orders/<uuid:order_id>/cancel/', views.cancel_order, name='cancel_order'),

    # AJAX endpoint for pincode check
    path('ajax/check-pincode/', check_pincode, name='check_pincode'),
]