"""
Refactored cart views using service layer and type hints.
Expert-level code organization.
"""
from typing import Dict, Any
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.contrib import messages
from utils.decorators import customer_required
from utils.logging_config import get_logger, log_view_execution
from .cart import Cart
from .services import CartService

logger = get_logger(__name__)


@require_POST
@log_view_execution(logger)
def cart_add(request: HttpRequest, product_id: int) -> HttpResponse:
    """
    Add product to cart.
    
    Args:
        request: HTTP request object.
        product_id: Product ID to add.
        
    Returns:
        HTTP response (JSON for AJAX, redirect otherwise).
    """
    logger.debug(f"cart_add called with product_id={product_id}")
    
    cart = Cart(request)
    
    # Validate product using service
    is_valid, product, error = CartService.validate_product_for_cart(product_id)
    if not is_valid:
        return _handle_cart_response(request, cart, False, error)
    
    # Get and validate quantity
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        return _handle_cart_response(request, cart, False, 'Invalid quantity.')
    
    # Add to cart using service
    success, message = CartService.add_to_cart(cart, product, quantity)
    
    return _handle_cart_response(request, cart, success, message)


@require_POST
@log_view_execution(logger)
def cart_remove(request: HttpRequest, product_id: int) -> HttpResponse:
    """
    Remove product from cart.
    
    Args:
        request: HTTP request object.
        product_id: Product ID to remove.
        
    Returns:
        HTTP response (JSON for AJAX, redirect otherwise).
    """
    cart = Cart(request)
    
    try:
        from store.models import Product
        product = Product.objects.get(id=product_id)
        cart.remove(product)
        success = True
        message = f'{product.name} removed from cart!'
    except Product.DoesNotExist:
        success = False
        message = 'Product not found.'
    except Exception as e:
        logger.error(f"Error removing product from cart: {str(e)}", exc_info=True)
        success = False
        message = f'Error removing product: {str(e)}'
    
    return _handle_cart_response(request, cart, success, message)


@require_POST
@log_view_execution(logger)
def cart_update(request: HttpRequest, product_id: int) -> HttpResponse:
    """
    Update cart item quantity.
    
    Args:
        request: HTTP request object.
        product_id: Product ID to update (0 for bulk update).
        
    Returns:
        HTTP response (JSON for AJAX, redirect otherwise).
    """
    cart = Cart(request)
    success = True
    message = 'Cart updated!'
    
    # Bulk update if product_id == 0
    if product_id == 0:
        for key, value in request.POST.items():
            if key.startswith('quantity_'):
                try:
                    pid = int(key.split('_')[1])
                    quantity = int(value)
                    
                    # Validate product
                    is_valid, product, error = CartService.validate_product_for_cart(pid)
                    if not is_valid:
                        success = False
                        message = f'Error updating product {pid}: {error}'
                        continue
                    
                    # Update using service
                    item_success, item_message = CartService.update_cart_item(cart, product, quantity)
                    if not item_success:
                        success = False
                        message = f'Error updating product {pid}: {item_message}'
                        
                except (ValueError, TypeError) as e:
                    success = False
                    message = f'Error updating product: {str(e)}'
                except Exception as e:
                    logger.error(f"Error in bulk cart update: {str(e)}", exc_info=True)
                    success = False
                    message = f'Error updating product: {str(e)}'
    else:
        # Single product update
        is_valid, product, error = CartService.validate_product_for_cart(product_id)
        if not is_valid:
            return _handle_cart_response(request, cart, False, error)
        
        try:
            quantity = int(request.POST.get('quantity', 1))
        except (ValueError, TypeError):
            return _handle_cart_response(request, cart, False, 'Invalid quantity.')
        
        success, message = CartService.update_cart_item(cart, product, quantity)
    
    return _handle_cart_response(request, cart, success, message)


@customer_required
@log_view_execution(logger)
def cart_detail(request: HttpRequest) -> HttpResponse:
    """
    Display cart detail page.
    
    Args:
        request: HTTP request object.
        
    Returns:
        HTTP response with cart detail page.
    """
    cart = Cart(request)
    subtotal = cart.get_total_price()
    discount = request.session.get('coupon_discount', 0)
    total = subtotal - discount
    
    return render(request, 'cart/detail.html', {
        'cart': cart,
        'subtotal': subtotal,
        'discount': discount,
        'total': total
    })


def cart_count(request: HttpRequest) -> JsonResponse:
    """
    Return JSON with current cart item count.
    
    Args:
        request: HTTP request object.
        
    Returns:
        JSON response with cart count.
    """
    cart = Cart(request)
    return JsonResponse({'count': cart.get_total_quantity()})


@require_POST
@log_view_execution(logger)
def clear_cart(request: HttpRequest) -> HttpResponse:
    """
    Remove all items from cart.
    
    Args:
        request: HTTP request object.
        
    Returns:
        HTTP redirect response.
    """
    cart = Cart(request)
    cart.clear()
    messages.success(request, 'Cart cleared successfully.')
    return redirect('cart:cart_detail')


def _handle_cart_response(
    request: HttpRequest,
    cart: Cart,
    success: bool,
    message: str
) -> HttpResponse:
    """
    Helper function to handle cart responses (AJAX or regular).
    
    Args:
        request: HTTP request object.
        cart: Cart instance.
        success: Whether operation was successful.
        message: Response message.
        
    Returns:
        HTTP response (JSON for AJAX, redirect otherwise).
    """
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    
    if is_ajax:
        # Build JSON response
        cart_items = []
        for item in cart:
            cart_items.append({
                'product_id': item['product'].id,
                'name': item['product'].name,
                'price': float(item['price']),
                'quantity': item['quantity'],
                'total': float(item['total_price'])
            })
        
        return JsonResponse({
            'success': success,
            'cart_total_items': len(cart),
            'cart_total_price': float(cart.get_total_price()),
            'cart_items': cart_items,
            'message': message
        })
    else:
        # Regular HTTP response
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
        return redirect('cart:cart_detail')

