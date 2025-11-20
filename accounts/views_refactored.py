"""
Refactored accounts views using service layer and type hints.
Expert-level code organization with separation of concerns.
"""
from typing import Optional, Dict, Any
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from utils.decorators import seller_required, customer_required, profile_required
from utils.logging_config import get_logger, log_view_execution
from .services import UserService, SellerAnalyticsService, CustomerService

logger = get_logger(__name__)


@profile_required
@customer_required
@log_view_execution(logger)
def customer_dashboard(request: HttpRequest) -> HttpResponse:
    """
    Main customer dashboard with profile and navigation.
    
    Args:
        request: HTTP request object.
        
    Returns:
        HTTP response with customer dashboard.
    """
    from orders.models import Order
    
    # Get customer orders with optimized query
    orders = CustomerService.get_customer_orders(request.user)[:10]
    
    context = {
        'profile': request.user.profile,
        'orders': orders,
        'current_page': 'home',
    }
    return render(request, 'accounts/customer_dashboard.html', context)


@profile_required
@customer_required
@log_view_execution(logger)
def customer_profile(request: HttpRequest) -> HttpResponse:
    """
    Customer profile edit page.
    
    Args:
        request: HTTP request object.
        
    Returns:
        HTTP response with profile edit form.
    """
    from .forms import ProfileUpdateForm
    
    if request.method == 'POST':
        form = ProfileUpdateForm(
            request.POST,
            instance=request.user.profile,
            user=request.user
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:customer_dashboard')
    else:
        form = ProfileUpdateForm(
            instance=request.user.profile,
            user=request.user
        )
    
    context = {
        'form': form,
        'profile': request.user.profile,
        'current_page': 'profile',
    }
    return render(request, 'accounts/customer_dashboard.html', context)


@profile_required
@customer_required
@log_view_execution(logger)
def customer_orders(request: HttpRequest) -> HttpResponse:
    """
    Customer order history page.
    
    Args:
        request: HTTP request object.
        
    Returns:
        HTTP response with order history.
    """
    orders = CustomerService.get_customer_orders(request.user)
    
    context = {
        'orders': orders,
        'profile': request.user.profile,
        'current_page': 'orders',
    }
    return render(request, 'accounts/customer_dashboard.html', context)


@profile_required
@customer_required
@log_view_execution(logger)
def customer_notifications(request: HttpRequest) -> HttpResponse:
    """
    Customer notifications page.
    
    Args:
        request: HTTP request object.
        
    Returns:
        HTTP response with notifications.
    """
    notifications = CustomerService.get_customer_notifications(request.user)
    
    context = {
        'notifications': notifications,
        'profile': request.user.profile,
        'current_page': 'notifications',
    }
    return render(request, 'accounts/customer_dashboard.html', context)


@profile_required
@customer_required
@log_view_execution(logger)
def customer_addresses(request: HttpRequest) -> HttpResponse:
    """
    Customer saved addresses page.
    
    Args:
        request: HTTP request object.
        
    Returns:
        HTTP response with addresses.
    """
    context = {
        'profile': request.user.profile,
        'current_page': 'addresses',
    }
    return render(request, 'accounts/customer_dashboard.html', context)


@profile_required
@seller_required
@log_view_execution(logger)
def seller_dashboard(request: HttpRequest) -> HttpResponse:
    """
    Main seller dashboard with analytics and recent data.
    
    Args:
        request: HTTP request object.
        
    Returns:
        HTTP response with seller dashboard.
    """
    # Get dashboard data using service
    dashboard_data = SellerAnalyticsService.get_seller_dashboard_data(request.user)
    
    if not dashboard_data:
        messages.error(request, 'Seller profile not found. Please contact support.')
        return redirect('store:home')
    
    seller_profile = dashboard_data['seller_profile']
    
    # Check approval status
    if not seller_profile.is_approved:
        messages.warning(
            request,
            f'Your seller account is {seller_profile.get_approval_status_display()}.'
        )
    
    return render(request, 'accounts/seller_dashboard.html', dashboard_data)


@profile_required
@seller_required
@log_view_execution(logger)
def seller_products(request: HttpRequest) -> HttpResponse:
    """
    Seller products management page.
    
    Args:
        request: HTTP request object.
        
    Returns:
        HTTP response with seller products.
    """
    from store.models import Product
    
    # Optimize query
    products = Product.objects.filter(
        seller=request.user
    ).select_related('category').order_by('-created')
    
    seller_profile = UserService.get_seller_profile(request.user)
    
    context = {
        'products': products,
        'seller_profile': seller_profile,
    }
    return render(request, 'accounts/seller_products.html', context)


@profile_required
@seller_required
@log_view_execution(logger)
def seller_orders(request: HttpRequest) -> HttpResponse:
    """
    Seller orders management page.
    
    Args:
        request: HTTP request object.
        
    Returns:
        HTTP response with seller orders.
    """
    from orders.services import OrderService
    
    order_items = OrderService.get_order_items_for_seller(request.user)
    seller_profile = UserService.get_seller_profile(request.user)
    
    context = {
        'order_items': order_items,
        'seller_profile': seller_profile,
    }
    return render(request, 'accounts/seller_orders.html', context)


@profile_required
@seller_required
@log_view_execution(logger)
def seller_analytics(request: HttpRequest) -> HttpResponse:
    """
    Seller analytics and insights page.
    
    Args:
        request: HTTP request object.
        
    Returns:
        HTTP response with analytics.
    """
    analytics = SellerAnalyticsService.get_seller_analytics(request.user)
    seller_profile = UserService.get_seller_profile(request.user)
    
    context = {
        'analytics': analytics,
        'seller_profile': seller_profile,
    }
    return render(request, 'accounts/seller_analytics.html', context)

