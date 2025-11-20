"""
Service layer for accounts business logic.
Handles user authentication, profiles, and dashboard data.
"""
from typing import Optional, Dict, List, Tuple, Any
from django.contrib.auth.models import User
from django.db.models import Sum, F, Count, Q, QuerySet
from django.db import transaction
from .models import Profile, SellerProfile
from orders.models import Order, OrderItem


class UserService:
    """Service for user-related operations."""
    
    @staticmethod
    def get_user_profile(user: User) -> Optional[Profile]:
        """
        Get user profile safely.
        
        Args:
            user: User instance.
            
        Returns:
            Profile instance or None.
        """
        if not user or not user.is_authenticated:
            return None
        return getattr(user, 'profile', None)
    
    @staticmethod
    def is_seller(user: User) -> bool:
        """
        Check if user is a seller.
        
        Args:
            user: User instance.
            
        Returns:
            True if user is a seller.
        """
        profile = UserService.get_user_profile(user)
        return profile.is_seller if profile else False
    
    @staticmethod
    def get_seller_profile(user: User) -> Optional[SellerProfile]:
        """
        Get seller profile safely.
        
        Args:
            user: User instance.
            
        Returns:
            SellerProfile instance or None.
        """
        if not UserService.is_seller(user):
            return None
        try:
            return user.seller_profile
        except SellerProfile.DoesNotExist:
            return None


class SellerAnalyticsService:
    """Service for seller analytics and statistics."""
    
    @staticmethod
    def get_seller_dashboard_data(user: User) -> Dict[str, any]:
        """
        Get comprehensive dashboard data for a seller.
        
        Args:
            user: Seller user instance.
            
        Returns:
            Dictionary with all dashboard metrics.
        """
        seller_profile = UserService.get_seller_profile(user)
        if not seller_profile:
            return {}
        
        # Optimize queries with select_related and prefetch_related
        products_qs = user.products.all().select_related('category')
        order_items_qs = OrderItem.objects.filter(
            product__seller=user
        ).select_related('order', 'product', 'order__user')
        
        orders_qs = Order.objects.filter(
            items__product__seller=user
        ).distinct().select_related('user')
        
        # Calculate metrics in single queries where possible
        total_products = products_qs.count()
        total_orders = orders_qs.count()
        
        # Aggregate sales and revenue in one query
        sales_data = order_items_qs.aggregate(
            total_sales=Sum('quantity'),
            total_revenue=Sum(F('price') * F('quantity'))
        )
        
        total_sales = sales_data['total_sales'] or 0
        total_revenue = sales_data['total_revenue'] or 0
        
        # Get pending orders count
        pending_orders = orders_qs.filter(order_status='pending').count()
        
        # Get pending shipments
        pending_shipments = orders_qs.filter(
            paid=True,
            shiprocket_order_id__isnull=True
        ).count()
        
        return {
            'seller_profile': seller_profile,
            'products': list(products_qs[:10]),
            'order_items': list(order_items_qs[:20]),
            'total_products': total_products,
            'total_orders': total_orders,
            'total_sales': total_sales,
            'total_revenue': total_revenue,
            'pending_orders': pending_orders,
            'pending_shipments': pending_shipments,
        }
    
    @staticmethod
    def get_seller_analytics(user: User) -> Dict[str, any]:
        """
        Get detailed analytics for seller.
        
        Args:
            user: Seller user instance.
            
        Returns:
            Dictionary with analytics data.
        """
        order_items_qs = OrderItem.objects.filter(
            product__seller=user
        ).select_related('order', 'product')
        
        orders_qs = Order.objects.filter(
            items__product__seller=user
        ).distinct()
        
        # Aggregate all metrics in optimized queries
        sales_data = order_items_qs.aggregate(
            total_sales=Sum('quantity'),
            total_revenue=Sum(F('price') * F('quantity'))
        )
        
        order_stats = orders_qs.aggregate(
            total_orders=Count('id'),
            pending_orders=Count('id', filter=Q(order_status='pending')),
            completed_orders=Count('id', filter=Q(order_status='completed'))
        )
        
        total_revenue = sales_data['total_revenue'] or 0
        total_orders = order_stats['total_orders'] or 0
        average_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        return {
            'total_sales': sales_data['total_sales'] or 0,
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'pending_orders': order_stats['pending_orders'] or 0,
            'completed_orders': order_stats['completed_orders'] or 0,
            'average_order_value': round(average_order_value, 2),
        }


class CustomerService:
    """Service for customer-related operations."""
    
    @staticmethod
    def get_customer_orders(user: User) -> QuerySet[Order]:
        """
        Get all orders for a customer with optimized queries.
        
        Args:
            user: Customer user instance.
            
        Returns:
            QuerySet of orders with related data.
        """
        return Order.objects.filter(
            user=user
        ).select_related('user').prefetch_related(
            'items', 'items__product'
        ).order_by('-created')
    
    @staticmethod
    def get_customer_notifications(user: User):
        """
        Get customer notifications.
        
        Args:
            user: Customer user instance.
            
        Returns:
            QuerySet or list of notifications.
        """
        if not hasattr(user, 'notifications'):
            return []
        
        try:
            return user.notifications.all().order_by('-created')
        except Exception:
            try:
                return user.notifications.all().order_by('-created_at')
            except Exception:
                return []

