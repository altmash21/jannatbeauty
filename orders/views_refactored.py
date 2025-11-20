"""
Refactored orders views using service layer and type hints.
Expert-level code organization.
"""
from typing import Optional, Dict, Any
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.conf import settings
from utils.decorators import customer_required, seller_required, profile_required
from utils.logging_config import get_logger, log_view_execution
from .models import Order, OrderItem
from .services import OrderService
from cart.cart import Cart

logger = get_logger(__name__)


@profile_required
@seller_required
@log_view_execution(logger)
def seller_orders(request: HttpRequest) -> HttpResponse:
    """
    Display orders for a seller.
    
    Args:
        request: HTTP request object.
        
    Returns:
        HTTP response with seller orders.
    """
    orders = OrderService.get_seller_orders(request.user)
    
    return render(request, 'orders/seller_orders.html', {'orders': orders})


@profile_required
@customer_required
@log_view_execution(logger)
def checkout(request: HttpRequest) -> HttpResponse:
    """
    Checkout page and order creation.
    
    Args:
        request: HTTP request object.
        
    Returns:
        HTTP response with checkout page or order confirmation.
    """
    cart = Cart(request)
    
    # Check if cart is empty
    if len(cart) == 0:
        messages.error(request, 'Your cart is empty.')
        return redirect('cart:cart_detail')
    
    # Ensure cart items persist after login
    request.session['cart'] = cart.serialize()
    
    if request.method == 'POST':
        # Get shipping data
        shipping_data = {
            'first_name': request.POST.get('first_name', '').strip(),
            'last_name': request.POST.get('last_name', '').strip(),
            'email': request.POST.get('email', '').strip(),
            'address': request.POST.get('address', '').strip(),
            'city': request.POST.get('city', '').strip(),
            'state': request.POST.get('state', '').strip(),
            'zipcode': request.POST.get('zipcode', '').strip(),
        }
        
        # Validate required fields
        required_fields = ['first_name', 'email', 'address']
        missing = [field for field in required_fields if not shipping_data.get(field)]
        
        if missing:
            messages.error(
                request,
                f'Please fill in all required fields: {", ".join(missing)}'
            )
            return render(request, 'orders/checkout.html', {
                'cart': cart,
                'initial_data': shipping_data,
                'discount': request.session.get('coupon_discount', 0)
            })
        
        # Create order using service
        order, error = OrderService.create_order_from_cart(
            cart=cart,
            user=request.user if request.user.is_authenticated else None,
            shipping_data=shipping_data
        )
        
        if not order:
            messages.error(request, error or 'Failed to create order.')
            return redirect('cart:cart_detail')
        
        # Handle payment (Razorpay or direct)
        if settings.RAZORPAY_ENABLED and settings.RAZORPAY_KEY_ID:
            # Razorpay payment flow
            import razorpay
            client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
            amount = int(float(order.total_amount) * 100)  # Convert to paise
            data = {
                "amount": amount,
                "currency": "INR",
                "receipt": str(order.id),
                "payment_capture": 1
            }
            
            try:
                razorpay_order = client.order.create(data=data)
                razorpay_order_id = razorpay_order['id']
                
                return render(request, 'orders/checkout.html', {
                    'cart': cart,
                    'initial_data': shipping_data,
                    'razorpay_order_id': razorpay_order_id,
                    'razorpay_key_id': settings.RAZORPAY_KEY_ID,
                    'amount': amount,
                    'order_id': str(order.id),
                    'discount': request.session.get('coupon_discount', 0)
                })
            except Exception as e:
                logger.error(f"Razorpay order creation failed: {str(e)}", exc_info=True)
                messages.error(request, 'Payment gateway error. Please try again.')
                order.delete()  # Clean up failed order
                return redirect('cart:cart_detail')
        else:
            # Direct order (payment disabled)
            order.paid = True
            order.save()
            cart.clear()
            messages.success(request, f'Order {order.id} placed successfully!')
            return redirect('orders:confirmation', order_id=order.id)
    
    # GET request - show checkout form
    initial_data = {}
    if request.user.is_authenticated:
        profile = request.user.profile
        initial_data = {
            'first_name': request.user.first_name or '',
            'last_name': request.user.last_name or '',
            'email': request.user.email or '',
            'address': profile.address or '',
            'city': profile.city or '',
            'state': profile.state or '',
            'zipcode': profile.zipcode or '',
        }
    
    subtotal = cart.get_total_price()
    discount = request.session.get('coupon_discount', 0)
    cart_total = subtotal - discount
    
    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'initial_data': initial_data,
        'discount': discount,
        'cart_total': cart_total,
        'subtotal': subtotal
    })


def confirmation(request: HttpRequest, order_id: int) -> HttpResponse:
    """
    Order confirmation page.
    
    Args:
        request: HTTP request object.
        order_id: Order ID to display.
        
    Returns:
        HTTP response with order confirmation.
    """
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/confirmation.html', {'order': order})

