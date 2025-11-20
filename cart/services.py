"""
Service layer for cart business logic.
"""
from typing import Optional, Dict, Tuple, Any
from django.core.cache import cache
from store.models import Product
from .cart import Cart


class CartService:
    """Service for cart operations."""
    
    @staticmethod
    def validate_product_for_cart(product_id: int) -> Tuple[bool, Optional[Product], Optional[str]]:
        """
        Validate if a product can be added to cart.
        
        Args:
            product_id: Product ID to validate.
            
        Returns:
            Tuple of (is_valid, product, error_message).
        """
        try:
            product = Product.objects.select_related('category', 'seller').get(
                id=product_id,
                available=True,
                approved=True
            )
            
            # Check seller approval
            if hasattr(product.seller, 'seller_profile'):
                if product.seller.seller_profile.approval_status != 'approved':
                    return False, None, 'Product from unapproved seller.'
            
            return True, product, None
        except Product.DoesNotExist:
            return False, None, 'Product not found or unavailable.'
        except Exception as e:
            return False, None, f'Error validating product: {str(e)}'
    
    @staticmethod
    def validate_quantity(quantity: int) -> Tuple[bool, Optional[str]]:
        """
        Validate quantity value.
        
        Args:
            quantity: Quantity to validate.
            
        Returns:
            Tuple of (is_valid, error_message).
        """
        if quantity <= 0:
            return False, 'Quantity must be greater than zero.'
        if quantity > 1000:  # Reasonable upper limit
            return False, 'Quantity exceeds maximum allowed (1000).'
        return True, None
    
    @staticmethod
    def add_to_cart(cart: Cart, product: Product, quantity: int) -> Tuple[bool, str]:
        """
        Add product to cart with validation.
        
        Args:
            cart: Cart instance.
            product: Product to add.
            quantity: Quantity to add.
            
        Returns:
            Tuple of (success, message).
        """
        # Validate quantity
        is_valid, error = CartService.validate_quantity(quantity)
        if not is_valid:
            return False, error
        
        # Check stock
        if product.stock > 0 and quantity > product.stock:
            return False, f'Insufficient stock. Only {product.stock} available.'
        
        try:
            cart.add(product=product, quantity=quantity)
            return True, f'{product.name} added to cart!'
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, f'Unexpected error: {str(e)}'
    
    @staticmethod
    def update_cart_item(cart: Cart, product: Product, quantity: int) -> Tuple[bool, str]:
        """
        Update cart item quantity.
        
        Args:
            cart: Cart instance.
            product: Product to update.
            quantity: New quantity.
            
        Returns:
            Tuple of (success, message).
        """
        if quantity < 0:
            return False, 'Quantity cannot be negative.'
        
        if quantity == 0:
            cart.remove(product)
            return True, f'{product.name} removed from cart!'
        
        # Validate quantity
        is_valid, error = CartService.validate_quantity(quantity)
        if not is_valid:
            return False, error
        
        # Check stock
        if product.stock > 0 and quantity > product.stock:
            return False, f'Insufficient stock. Only {product.stock} available.'
        
        try:
            cart.add(product=product, quantity=quantity, override_quantity=True)
            return True, 'Cart updated!'
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, f'Error updating cart: {str(e)}'

