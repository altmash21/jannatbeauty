"""
Clean Accounts Views - Separated Customer and Seller Logic
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from django.core.exceptions import FieldError
from functools import wraps

from .models import Profile, SellerProfile
from .forms import CustomerRegistrationForm, SellerRegistrationForm, ProfileUpdateForm, SellerProfileUpdateForm
from orders.models import Order, OrderItem


# ============================================================================
# AUTHENTICATION VIEWS
# ============================================================================

def register_choice(request):
    """Let users choose between customer or seller registration"""
    return render(request, 'accounts/register_choice.html')


def register_customer(request):
    """Customer registration"""
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Account created successfully! You can now log in.')
            return redirect('accounts:login')
    else:
        form = CustomerRegistrationForm()
    return render(request, 'accounts/register_customer.html', {'form': form})


def register_seller(request):
    """Seller registration with business details"""
    if request.method == 'POST':
        form = SellerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Seller account created! Your account is pending approval.')
            return redirect('accounts:login')
    else:
        form = SellerRegistrationForm()
    return render(request, 'accounts/register_seller.html', {'form': form})


def user_login(request):
    """Login view - redirects to appropriate dashboard"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            
            # Redirect based on user type
            if hasattr(user, 'profile') and user.profile.is_seller:
                return redirect('accounts:seller_dashboard')
            else:
                return redirect('accounts:customer_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/login.html')


def user_logout(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('store:home')


# ============================================================================
# CUSTOMER VIEWS
# ============================================================================

@login_required
def customer_dashboard(request):
    """Main customer dashboard with accordion sections"""
    if request.user.profile.is_seller:
        messages.error(request, 'Access denied. This is a customer-only area.')
        return redirect('accounts:seller_dashboard')
    
    # Get customer data
    orders = Order.objects.filter(user=request.user).order_by('-created')[:10]
    
    # Get notifications
    notifications = []
    if hasattr(request.user, 'notifications'):
        # Notification model usually uses `created`; some installs may use `created_at`.
        # Try ordering by the canonical `created` first, then fall back to `created_at`.
        try:
            notifications = request.user.notifications.all().order_by('-created')[:10]
        except FieldError:
            # Fallback for different notification implementations
            notifications = request.user.notifications.all().order_by('-created_at')[:10]
    
    context = {
        'orders': orders,
        'notifications': notifications,
        'profile': request.user.profile,
    }
    return render(request, 'accounts/customer_dashboard.html', context)


@login_required
def customer_profile(request):
    """Customer profile edit"""
    if request.user.profile.is_seller:
        messages.error(request, 'Access denied. This is a customer-only area.')
        return redirect('accounts:seller_dashboard')
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user.profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:customer_dashboard')
    else:
        form = ProfileUpdateForm(instance=request.user.profile, user=request.user)
    
    context = {
        'form': form,
        'profile': request.user.profile,
    }
    return render(request, 'accounts/customer_dashboard.html', context)


@login_required
def customer_orders(request):
    """Customer order history"""
    if request.user.profile.is_seller:
        messages.error(request, 'Access denied. This is a customer-only area.')
        return redirect('accounts:seller_dashboard')
    
    orders = Order.objects.filter(user=request.user).order_by('-created')
    
    context = {
        'orders': orders,
        'profile': request.user.profile,
    }
    return render(request, 'accounts/customer_dashboard.html', context)


@login_required
def customer_notifications(request):
    """Customer notifications"""
    if request.user.profile.is_seller:
        messages.error(request, 'Access denied. This is a customer-only area.')
        return redirect('accounts:seller_dashboard')
    
    notifications = []
    if hasattr(request.user, 'notifications'):
        # Notification model usually uses `created`; some installs may use `created_at`.
        try:
            notifications = request.user.notifications.all().order_by('-created')
        except FieldError:
            notifications = request.user.notifications.all().order_by('-created_at')
    
    context = {
        'notifications': notifications,
        'profile': request.user.profile,
    }
    return render(request, 'accounts/customer_dashboard.html', context)


# ============================================================================
# SELLER VIEWS
# ============================================================================

@login_required
def seller_dashboard(request):
    """Main seller dashboard"""
    if not request.user.profile.is_seller:
        messages.error(request, 'Access denied. Seller account required.')
        return redirect('accounts:customer_dashboard')
    
    try:
        seller_profile = request.user.seller_profile
    except SellerProfile.DoesNotExist:
        messages.error(request, 'Seller profile not found. Please contact support.')
        return redirect('store:home')
    
    # Check approval status
    if not seller_profile.is_approved:
        messages.warning(request, f'Your seller account is {seller_profile.get_approval_status_display()}.')
    
    # Get seller's products
    products = request.user.products.all()[:10] if hasattr(request.user, 'products') else []
    
    # Get seller's orders
    order_items = OrderItem.objects.filter(product__seller=request.user).select_related('order', 'product')
    orders = Order.objects.filter(items__product__seller=request.user).distinct()
    
    # Calculate analytics
    total_products = request.user.products.count() if hasattr(request.user, 'products') else 0
    total_orders = orders.count()
    total_sales = order_items.aggregate(total=models.Sum('quantity'))['total'] or 0
    total_revenue = order_items.aggregate(
        total=models.Sum(models.F('price') * models.F('quantity'))
    )['total'] or 0
    pending_orders = orders.filter(order_status='pending').count()
    
    # Count orders that are paid but don't have shiprocket order created yet
    pending_shipments = orders.filter(paid=True, shiprocket_order_id__isnull=True).count()
    
    context = {
        'seller_profile': seller_profile,
        'products': products,
        'order_items': order_items[:20],
        'total_products': total_products,
        'total_orders': total_orders,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'pending_orders': pending_orders,
        'pending_shipments': pending_shipments,
    }
    return render(request, 'accounts/seller_dashboard.html', context)


@login_required
def seller_products(request):
    """Seller products management"""
    if not request.user.profile.is_seller:
        messages.error(request, 'Access denied. Seller account required.')
        return redirect('accounts:customer_dashboard')
    
    products = request.user.products.all() if hasattr(request.user, 'products') else []
    
    context = {
        'products': products,
        'seller_profile': request.user.seller_profile,
    }
    return render(request, 'accounts/seller_products.html', context)


@login_required
def seller_orders(request):
    """Seller orders management"""
    if not request.user.profile.is_seller:
        messages.error(request, 'Access denied. Seller account required.')
        return redirect('accounts:customer_dashboard')
    
    order_items = OrderItem.objects.filter(product__seller=request.user).select_related('order', 'product').order_by('-order__created')
    
    context = {
        'order_items': order_items,
        'seller_profile': request.user.seller_profile,
    }
    return render(request, 'accounts/seller_orders.html', context)


@login_required
def seller_analytics(request):
    """Seller analytics and insights"""
    if not request.user.profile.is_seller:
        messages.error(request, 'Access denied. Seller account required.')
        return redirect('accounts:customer_dashboard')
    
    order_items = OrderItem.objects.filter(product__seller=request.user)
    orders = Order.objects.filter(items__product__seller=request.user).distinct()
    
    # Calculate detailed analytics
    analytics = {
        'total_sales': order_items.aggregate(total=models.Sum('quantity'))['total'] or 0,
        'total_revenue': order_items.aggregate(
            total=models.Sum(models.F('price') * models.F('quantity'))
        )['total'] or 0,
        'total_orders': orders.count(),
        'pending_orders': orders.filter(order_status='pending').count(),
        'completed_orders': orders.filter(order_status='completed').count(),
        'average_order_value': 0,
    }
    
    if analytics['total_orders'] > 0:
        analytics['average_order_value'] = analytics['total_revenue'] / analytics['total_orders']
    
    context = {
        'analytics': analytics,
        'seller_profile': request.user.seller_profile,
    }
    return render(request, 'accounts/seller_analytics.html', context)


@login_required
def seller_profile(request):
    """Seller profile view and edit"""
    if not request.user.profile.is_seller:
        messages.error(request, 'Access denied. Seller account required.')
        return redirect('accounts:customer_dashboard')
    
    try:
        seller_profile = request.user.seller_profile
    except SellerProfile.DoesNotExist:
        messages.error(request, 'Seller profile not found.')
        return redirect('store:home')
    
    if request.method == 'POST':
        profile_form = ProfileUpdateForm(request.POST, instance=request.user.profile, user=request.user)
        seller_form = SellerProfileUpdateForm(request.POST, instance=seller_profile)
        
        if profile_form.is_valid() and seller_form.is_valid():
            profile_form.save()
            seller_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:seller_dashboard')
    else:
        profile_form = ProfileUpdateForm(instance=request.user.profile, user=request.user)
        seller_form = SellerProfileUpdateForm(instance=seller_profile)
    
    context = {
        'profile_form': profile_form,
        'seller_form': seller_form,
        'seller_profile': seller_profile,
    }
    return render(request, 'accounts/seller_profile.html', context)
