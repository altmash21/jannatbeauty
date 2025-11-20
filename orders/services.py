"""
Service layer for order business logic.
"""
from typing import Optional, Dict, List, Tuple
from django.db import transaction
from django.contrib.auth.models import User
from django.db.models import Sum, F
from .models import Order, OrderItem
from cart.cart import Cart
from store.models import Product


class OrderService:
    """Service for order operations."""
    
    @staticmethod
    def validate_cart_for_checkout(cart: Cart) -> Tuple[bool, Optional[str], Optional[List[Dict]]]:
        """
        Validate all cart items before checkout.
        
        Args:
            cart: Cart instance to validate.
            
        Returns:
            Tuple of (is_valid, error_message, invalid_items).
        """
        invalid_items = []
        
        for item in cart:
            product = item['product']
            quantity = item['quantity']
            
            # Refresh from database to get latest data
            try:
                product.refresh_from_db()
            except Product.DoesNotExist:
                invalid_items.append({
                    'product': product.name,
                    'reason': 'Product no longer exists'
                })
                continue
            
            # Check availability
            if not product.available or not product.approved:
                invalid_items.append({
                    'product': product.name,
                    'reason': 'Product is no longer available'
                })
                continue
            
            # Check stock
            if product.stock < quantity:
                invalid_items.append({
                    'product': product.name,
                    'reason': f'Insufficient stock. Only {product.stock} available.'
                })
                continue
        
        if invalid_items:
            return False, 'Some items in your cart are no longer available.', invalid_items
        
        return True, None, None
    
    @staticmethod
    @transaction.atomic
    def create_order_from_cart(
        cart: Cart,
        user: Optional[User],
        shipping_data: Dict[str, str]
    ) -> Tuple[Optional[Order], Optional[str]]:
        """
        Create order from cart with atomic transaction.
        
        Args:
            cart: Cart instance.
            user: User instance (optional for guest checkout).
            shipping_data: Dictionary with shipping information.
            
        Returns:
            Tuple of (order, error_message).
        """
        # Validate cart first
        is_valid, error, invalid_items = OrderService.validate_cart_for_checkout(cart)
        if not is_valid:
            return None, error
        
        try:
            # Create order
            order = Order.objects.create(
                user=user if user and user.is_authenticated else None,
                first_name=shipping_data.get('first_name', ''),
                last_name=shipping_data.get('last_name', ''),
                email=shipping_data.get('email', ''),
                address=shipping_data.get('address', ''),
                city=shipping_data.get('city', ''),
                state=shipping_data.get('state', ''),
                zipcode=shipping_data.get('zipcode', ''),
                total_amount=cart.get_total_price()
            )
            
            # Create order items and update stock
            for item in cart:
                product = item['product']
                quantity = item['quantity']
                
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=item['price'],
                    quantity=quantity
                )
                
                # Update stock atomically
                product.stock -= quantity
                product.save(update_fields=['stock'])
            
            return order, None
            
        except Exception as e:
            return None, f'Error creating order: {str(e)}'
    
    @staticmethod
    def get_seller_orders(user: User) -> List[Order]:
        """
        Get all orders for a seller with optimized queries.
        
        Args:
            user: Seller user instance.
            
        Returns:
            List of orders.
        """
        return list(Order.objects.filter(
            items__product__seller=user
        ).distinct().select_related('user').prefetch_related(
            'items', 'items__product'
        ).order_by('-created'))
    
    @staticmethod
    def get_order_items_for_seller(user: User) -> List[OrderItem]:
        """
        Get order items for a seller with optimized queries.
        
        Args:
            user: Seller user instance.
            
        Returns:
            List of order items.
        """
        return list(OrderItem.objects.filter(
            product__seller=user
        ).select_related('order', 'product', 'order__user').order_by('-order__created'))

