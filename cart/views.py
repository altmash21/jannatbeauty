from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from store.models import Product
from .cart import Cart
import logging

logger = logging.getLogger(__name__)


@require_POST
def cart_add(request, product_id):
    logger.debug(f"cart_add called with product_id={product_id}")
    logger.debug(f"Request POST data: {request.POST}")
    logger.debug(f"Request headers: {dict(request.headers)}")

    try:
        cart = Cart(request)
        product = get_object_or_404(Product, id=product_id)
        quantity = int(request.POST.get('quantity', 1))
        cart.add(product=product, quantity=quantity)
        success = True
        message = f'{product.name} added to cart!'
    except ValueError as e:
        success = False
        message = str(e)
    except Exception as e:
        success = False
        message = f"Unexpected error: {str(e)}"

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Build a safe JSON response with float prices
        cart_items = []
        for item in cart:
            cart_items.append({
                'product_id': item['product'].id,
                'name': item['product'].name,
                'price': float(item['price']),
                'quantity': item['quantity'],
                'total': float(item['total_price'])
            })
        response_data = {
            'success': success,
            'cart_total_items': len(cart),
            'cart_items': cart_items,
            'message': message
        }
        return JsonResponse(response_data)

    from django.contrib import messages
    if not success:
        messages.error(request, message)
    else:
        messages.success(request, message)

    return redirect('cart:cart_detail')


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_total_items': len(cart),
            'cart_total_price': float(cart.get_total_price()),
            'message': f'{product.name} removed from cart!'
        })

    return redirect('cart:cart_detail')


@require_POST
def cart_update(request, product_id):
    cart = Cart(request)
    from django.contrib import messages
    success = True
    message = 'Cart updated!'

    # Bulk update if product_id == 0
    if product_id == 0:
        for key, value in request.POST.items():
            if key.startswith('quantity_'):
                try:
                    pid = int(key.split('_')[1])
                    quantity = int(value)
                    product = get_object_or_404(Product, id=pid)
                    if quantity > 0:
                        cart.add(product=product, quantity=quantity, override_quantity=True)
                    else:
                        cart.remove(product)
                except Exception as e:
                    success = False
                    message = f'Error updating product {pid}: {str(e)}'
    else:
        product = get_object_or_404(Product, id=product_id)
        quantity = int(request.POST.get('quantity', 1))
        try:
            if quantity > 0:
                cart.add(product=product, quantity=quantity, override_quantity=True)
            else:
                cart.remove(product)
        except Exception as e:
            success = False
            message = f'Error updating product {product_id}: {str(e)}'

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': success,
            'cart_total_items': len(cart),
            'cart_total_price': float(cart.get_total_price()),
            'message': message
        })

    if not success:
        messages.error(request, message)
    else:
        messages.success(request, message)

    return redirect('cart:cart_detail')


def cart_detail(request):
    if hasattr(request.user, 'profile') and request.user.profile.is_seller:
        from django.contrib import messages
        messages.error(request, 'Sellers cannot access the cart.')
        return redirect('accounts:seller_dashboard')
    cart = Cart(request)
    subtotal = cart.get_total_price()
    discount = 0  # Update this if you add coupon logic
    total = subtotal - discount
    return render(request, 'cart/detail.html', {
        'cart': cart,
        'subtotal': subtotal,
        'discount': discount,
        'total': total
    })


def cart_count(request):
    """Return JSON with current cart item count for the header AJAX poll."""
    cart = Cart(request)
    from django.http import JsonResponse
    return JsonResponse({'count': cart.get_total_quantity()})


from django.views.decorators.http import require_POST

@require_POST
def clear_cart(request):
    """Remove all items from the cart and redirect to cart detail."""
    cart = Cart(request)
    cart.clear()
    return redirect('cart:cart_detail')
