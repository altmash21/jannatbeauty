from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('products/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('about/', views.about_page, name='about'),
    
    # Seller product management
    path('add/', views.add_product, name='add_product'),
    path('edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('seller/products/', views.seller_products, name='seller_products'),
    
    # Admin product management
    path('admin/add-product/', views.admin_add_product, name='admin_add_product'),
    path('admin/manage-products/', views.admin_manage_products, name='admin_manage_products'),
    path('admin/approve-product/<int:product_id>/', views.approve_product, name='approve_product'),
    path('admin/manage-sellers/', views.manage_sellers, name='manage_sellers'),
]