"""
Reusable decorators for views and functions.
"""
from functools import wraps
from typing import Callable
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect
from accounts.services import UserService


def seller_required(view_func: Callable) -> Callable:
    """
    Decorator to ensure user is a seller.
    
    Usage:
        @seller_required
        def my_view(request):
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not UserService.is_seller(request.user):
            messages.error(request, 'Access denied. Seller account required.')
            return redirect('accounts:customer_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def customer_required(view_func: Callable) -> Callable:
    """
    Decorator to ensure user is a customer (not seller).
    
    Usage:
        @customer_required
        def my_view(request):
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if UserService.is_seller(request.user):
            messages.error(request, 'Access denied. This is a customer-only area.')
            return redirect('accounts:seller_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def profile_required(view_func: Callable) -> Callable:
    """
    Decorator to ensure user has a profile.
    
    Usage:
        @profile_required
        def my_view(request):
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not UserService.get_user_profile(request.user):
            messages.error(request, 'Profile not found. Please contact support.')
            return redirect('store:home')
        return view_func(request, *args, **kwargs)
    return wrapper

