from django.views.decorators.http import require_GET

# Real-time cart totals for AJAX
@require_GET
def cart_detail_json(request):
    cart = Cart(request)
    
    # Validate and recalculate coupon if applied
    if 'coupon_id' in request.session:
        from coupons.models import Coupon
        try:
            coupon = Coupon.objects.get(id=request.session['coupon_id'])
            cart_total = cart.get_total_price()
            
            # Check if cart is empty or coupon is no longer valid
            if cart_total == 0 or not coupon.is_valid() or cart_total < coupon.min_purchase_amount:
                # Remove coupon
                del request.session['coupon_id']
                del request.session['coupon_code']
                del request.session['coupon_discount']
            else:
                # Recalculate discount
                new_discount = coupon.calculate_discount(cart_total)
                request.session['coupon_discount'] = float(new_discount)
        except Coupon.DoesNotExist:
            # Coupon deleted, remove from session
            if 'coupon_id' in request.session:
                del request.session['coupon_id']
                del request.session['coupon_code']
                del request.session['coupon_discount']
    
    # Calculate MRP total (compare price) and discount
    mrp_total = 0
    compare_discount = 0
    for item in cart:
        product = item['product']
        quantity = item['quantity']
        if hasattr(product, 'compare_price') and product.compare_price and product.compare_price > 0:
            mrp_total += float(product.compare_price) * quantity
            if product.compare_price > product.price:
                compare_discount += float(product.compare_price - product.price) * quantity
        else:
            mrp_total += float(product.price) * quantity
    coupon_discount = request.session.get('coupon_discount', 0)
    subtotal = cart.get_total_price()
    total_discount = compare_discount + float(coupon_discount)
    total = max(0, subtotal - float(coupon_discount))
    
    # Calculate discount percentages
    compare_discount_percent = 0
    coupon_discount_percent = 0
    total_discount_percent = 0
    
    if mrp_total > 0:
        compare_discount_percent = (compare_discount / mrp_total) * 100
        total_discount_percent = (total_discount / mrp_total) * 100
    
    if subtotal > 0 and coupon_discount > 0:
        coupon_discount_percent = (float(coupon_discount) / subtotal) * 100
    
    return JsonResponse({
        'mrp_total': mrp_total,
        'subtotal': subtotal,
        'compare_discount': compare_discount,
        'compare_discount_percent': compare_discount_percent,
        'coupon_discount': coupon_discount,
        'coupon_discount_percent': coupon_discount_percent,
        'discount': total_discount,
        'total_discount_percent': total_discount_percent,
        'total': total,
        'cart_count': len(cart)
    })
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.conf import settings
from store.models import Product
from .cart import Cart
import logging
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


@require_POST
def cart_add(request, product_id):
    logger.debug(f"cart_add called with product_id={product_id}")
    logger.debug(f"Request POST data: {request.POST}")
    logger.debug(f"Request headers: {dict(request.headers)}")

    # Check if this is a "Buy Now" request
    buy_now = request.POST.get('buy_now', '0') == '1'
    
    try:
        cart = Cart(request)
        product = get_object_or_404(Product, id=product_id, available=True, approved=True)
        quantity = int(request.POST.get('quantity', 1))
        if quantity <= 0:
            raise ValueError('Quantity must be greater than zero.')
        cart.add(product=product, quantity=quantity)
        
        # Recalculate coupon discount if coupon is applied
        if 'coupon_id' in request.session:
            from coupons.models import Coupon
            try:
                coupon = Coupon.objects.get(id=request.session['coupon_id'])
                cart_total = cart.get_total_price()
                
                if coupon.is_valid() and cart_total >= coupon.min_purchase_amount:
                    # Recalculate discount
                    new_discount = coupon.calculate_discount(cart_total)
                    request.session['coupon_discount'] = float(new_discount)
            except Coupon.DoesNotExist:
                # Coupon deleted, remove from session
                if 'coupon_id' in request.session:
                    del request.session['coupon_id']
                    del request.session['coupon_code']
                    del request.session['coupon_discount']
        
        success = True
        message = f'{product.name} added to cart!'
    except ValueError as e:
        success = False
        message = str(e)
    except Exception as e:
        success = False
        message = f"Unexpected error: {str(e)}"

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # AJAX request - return JSON response
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
            'cart_total_items': cart.get_total_quantity(),
            'cart_items': cart_items,
            'message': message
        }
        
        # If Buy Now, include redirect URL
        if buy_now and success:
            response_data['redirect_url'] = '/cart/'
            
        return JsonResponse(response_data)

    from django.contrib import messages
    if not success:
        messages.error(request, message)
    else:
        messages.success(request, message)

    # For regular form submissions
    if buy_now:
        # Buy Now - always redirect to cart
        return redirect('cart:cart_detail')
    else:
        # Add to Cart - redirect back to referring page or cart
        redirect_url = request.META.get('HTTP_REFERER', '/cart/')
        return redirect(redirect_url)


@require_POST
def cart_remove(request, product_id):
    logger.info(f"Cart remove called with product_id={product_id} (type: {type(product_id).__name__})")
    cart = Cart(request)
    logger.info(f"Cart contents before removal: {cart.cart}")
    logger.info(f"Cart keys: {list(cart.cart.keys())}")
    logger.info(f"Cart keys types: {[type(k).__name__ for k in cart.cart.keys()]}")
    
    try:
        product = get_object_or_404(Product, id=product_id)
        logger.info(f"Product.id={product.id} (type: {type(product.id).__name__})")
        logger.info(f"Looking for key: '{str(product.id)}'")
        logger.info(f"Key exists in cart: {str(product.id) in cart.cart}")
        
        cart.remove(product)
        logger.info(f"Product {product_id} removed from cart.")
        
        # Create a fresh Cart instance to get updated data from session
        cart = Cart(request)
        logger.info(f"Cart contents after removal (fresh instance): {cart.cart}")
        logger.info(f"Cart length after removal: {len(cart)}")
        
        # If cart is now empty, explicitly clear the session key
        if len(cart) == 0 or not cart.cart:
            logger.info("Cart is empty, clearing session")
            if settings.CART_SESSION_ID in request.session:
                del request.session[settings.CART_SESSION_ID]
            request.session.modified = True
        else:
            # Force session save
            request.session.modified = True
        
        # Recalculate coupon discount if coupon is applied
        if 'coupon_id' in request.session:
            from coupons.models import Coupon
            try:
                coupon = Coupon.objects.get(id=request.session['coupon_id'])
                cart_total = cart.get_total_price()
                
                # Check if cart is empty or coupon is no longer valid
                if cart_total == 0 or not coupon.is_valid() or cart_total < coupon.min_purchase_amount:
                    # Remove coupon
                    del request.session['coupon_id']
                    del request.session['coupon_code']
                    del request.session['coupon_discount']
                else:
                    # Recalculate discount
                    new_discount = coupon.calculate_discount(cart_total)
                    request.session['coupon_discount'] = float(new_discount)
            except Coupon.DoesNotExist:
                # Coupon deleted, remove from session
                if 'coupon_id' in request.session:
                    del request.session['coupon_id']
                    del request.session['coupon_code']
                    del request.session['coupon_discount']
        
        success = True
        message = f'{product.name} removed from cart!'
    except Exception as e:
        logger.error(f"Error removing product: {e}")
        success = False
        message = f'Error removing product: {str(e)}'

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Recalculate cart length after all operations
        cart_length = len(cart)
        logger.info(f"Returning JSON response with cart_length={cart_length}")
        logger.info(f"Session cart: {request.session.get(settings.CART_SESSION_ID)}")
        logger.info(f"Session keys: {list(request.session.keys())}")
        
        # Force save session to ensure persistence
        request.session.save()
        
        return JsonResponse({
            'success': success,
            'cart_total_items': cart_length,
            'cart_count': cart_length,
            'cart_total_price': float(cart.get_total_price()),
            'message': message
        })
    
    from django.contrib import messages
    if not success:
        messages.error(request, message)
    else:
        messages.success(request, message)

    return redirect('cart:cart_detail')


@require_POST
def cart_update(request, product_id):
    cart = Cart(request)
    from django.contrib import messages
    success = True
    message = 'Cart updated!'
    item_total_price = None
    # Bulk update if product_id == 0
    if product_id == 0:
        for key, value in request.POST.items():
            if key.startswith('quantity_'):
                try:
                    pid = int(key.split('_')[1])
                    quantity = int(value)
                    if quantity < 0:
                        raise ValueError('Quantity cannot be negative.')
                    product = get_object_or_404(Product, id=pid, available=True, approved=True)
                    if quantity > 0:
                        cart.add(product=product, quantity=quantity, override_quantity=True)
                    else:
                        cart.remove(product)
                except (ValueError, TypeError) as e:
                    success = False
                    message = f'Error updating product {pid}: {str(e)}'
                except Exception as e:
                    success = False
                    message = f'Error updating product {pid}: {str(e)}'
    else:
        try:
            product = get_object_or_404(Product, id=product_id, available=True, approved=True)
            quantity = int(request.POST.get('quantity', 1))
            if quantity < 0:
                raise ValueError('Quantity cannot be negative.')
            if quantity > 0:
                cart.add(product=product, quantity=quantity, override_quantity=True)
            else:
                cart.remove(product)
            # Find updated item total price
            for item in cart:
                if item['product'].id == product_id:
                    item_total_price = item['total_price']
                    break
        except (ValueError, TypeError) as e:
            success = False
            message = f'Error updating product {product_id}: {str(e)}'
        except Exception as e:
            success = False
            message = f'Error updating product {product_id}: {str(e)}'
    
    # Recalculate coupon discount if coupon is applied
    if success and 'coupon_id' in request.session:
        from coupons.models import Coupon
        try:
            coupon = Coupon.objects.get(id=request.session['coupon_id'])
            cart_total = cart.get_total_price()
            
            # Check if cart is empty or coupon is no longer valid
            if cart_total == 0 or not coupon.is_valid() or cart_total < coupon.min_purchase_amount:
                # Remove coupon
                del request.session['coupon_id']
                del request.session['coupon_code']
                del request.session['coupon_discount']
                message = 'Cart updated! Coupon removed (no longer valid for current cart)'
            else:
                # Recalculate discount
                new_discount = coupon.calculate_discount(cart_total)
                request.session['coupon_discount'] = float(new_discount)
        except Coupon.DoesNotExist:
            # Coupon deleted, remove from session
            if 'coupon_id' in request.session:
                del request.session['coupon_id']
                del request.session['coupon_code']
                del request.session['coupon_discount']

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Calculate cart summary fields for AJAX response
        mrp_total = 0
        compare_discount = 0
        for item in cart:
            product = item['product']
            quantity = item['quantity']
            if hasattr(product, 'compare_price') and product.compare_price and product.compare_price > 0:
                mrp_total += float(product.compare_price) * quantity
                if product.compare_price > product.price:
                    compare_discount += float(product.compare_price - product.price) * quantity
            else:
                mrp_total += float(product.price) * quantity
        coupon_discount = request.session.get('coupon_discount', 0)
        subtotal = cart.get_total_price()
        total_discount = compare_discount + float(coupon_discount)
        total = max(0, subtotal - float(coupon_discount))
        
        # Calculate discount percentages
        compare_discount_percent = 0
        coupon_discount_percent = 0
        total_discount_percent = 0
        
        if mrp_total > 0:
            compare_discount_percent = (compare_discount / mrp_total) * 100
            total_discount_percent = (total_discount / mrp_total) * 100
        
        if subtotal > 0 and coupon_discount > 0:
            coupon_discount_percent = (float(coupon_discount) / subtotal) * 100
        
        return JsonResponse({
            'success': success,
            'cart_total_items': len(cart),
            'cart_total_price': float(cart.get_total_price()),
            'item_total_price': float(item_total_price) if item_total_price is not None else None,
            'mrp_total': mrp_total,
            'compare_discount': compare_discount,
            'compare_discount_percent': compare_discount_percent,
            'coupon_discount': coupon_discount,
            'coupon_discount_percent': coupon_discount_percent,
            'discount': total_discount,
            'total_discount_percent': total_discount_percent,
            'total': total,
            'cart_count': len(cart),
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
    
    # Validate and recalculate coupon if applied
    if 'coupon_id' in request.session:
        from coupons.models import Coupon
        try:
            coupon = Coupon.objects.get(id=request.session['coupon_id'])
            cart_total = cart.get_total_price()
            
            # Check if cart is empty or coupon is no longer valid
            if cart_total == 0 or not coupon.is_valid() or cart_total < coupon.min_purchase_amount:
                # Remove coupon
                del request.session['coupon_id']
                del request.session['coupon_code']
                del request.session['coupon_discount']
                from django.contrib import messages
                messages.warning(request, 'Your coupon has been removed as it is no longer valid for your cart.')
            else:
                # Recalculate discount
                new_discount = coupon.calculate_discount(cart_total)
                request.session['coupon_discount'] = float(new_discount)
        except Coupon.DoesNotExist:
            # Coupon deleted, remove from session
            if 'coupon_id' in request.session:
                del request.session['coupon_id']
                del request.session['coupon_code']
                del request.session['coupon_discount']
    
    # Calculate MRP total (compare price) and discount
    mrp_total = 0
    compare_discount = 0
    for item in cart:
        product = item['product']
        quantity = item['quantity']
        if hasattr(product, 'compare_price') and product.compare_price and product.compare_price > 0:
            mrp_total += float(product.compare_price) * quantity
            if product.compare_price > product.price:
                compare_discount += float(product.compare_price - product.price) * quantity
        else:
            # If no compare price, use regular price as MRP
            mrp_total += float(product.price) * quantity
    
    # Coupon discount (if any)
    coupon_discount = request.session.get('coupon_discount', 0)
    
    # Actual selling price (subtotal)
    subtotal = cart.get_total_price()
    
    # Total discount
    total_discount = compare_discount + float(coupon_discount)
    
    # Final amount (actual price after all discounts)
    total = max(0, subtotal - float(coupon_discount))
    
    # Calculate discount percentages
    compare_discount_percent = 0
    coupon_discount_percent = 0
    total_discount_percent = 0
    
    if mrp_total > 0:
        compare_discount_percent = (compare_discount / mrp_total) * 100
        total_discount_percent = (total_discount / mrp_total) * 100
    
    if subtotal > 0 and coupon_discount > 0:
        coupon_discount_percent = (float(coupon_discount) / subtotal) * 100
    
    return render(request, 'cart/detail.html', {
        'cart': cart,
        'mrp_total': mrp_total,  # Price shown as "Price (X items)"
        'subtotal': subtotal,
        'compare_discount': compare_discount,
        'compare_discount_percent': compare_discount_percent,
        'coupon_discount': coupon_discount,
        'coupon_discount_percent': coupon_discount_percent,
        'discount': total_discount,  # Total discount on MRP
        'total_discount_percent': total_discount_percent,
        'total': total  # Final amount to pay
    })


def cart_count(request):
    """Return JSON with current cart item count for the header AJAX poll."""
    cart = Cart(request)
    from django.http import JsonResponse
    return JsonResponse({'count': cart.get_total_quantity()})


@require_POST
def clear_cart(request):
    """Remove all items from the cart and redirect to cart detail."""
    cart = Cart(request)
    cart.clear()
    return redirect('cart:cart_detail')
