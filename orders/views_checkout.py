"""
Order processing and management
Clean implementation of checkout and order confirmation
"""
import uuid
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from .models import Order, OrderItem
from .cashfree_service import CashfreeService
from cart.cart import Cart
from store.models import Product

logger = logging.getLogger(__name__)


def checkout(request):
    """
    Checkout page - validates cart and shows billing form
    """
    # Check if seller
    if hasattr(request.user, 'profile') and request.user.profile.is_seller:
        messages.error(request, 'Sellers cannot purchase products.')
        return redirect('accounts:seller_dashboard')
    
    # Get cart
    cart = Cart(request)
    if len(cart) == 0:
        messages.error(request, 'Your cart is empty.')
        return redirect('cart:cart_detail')
    
    # Calculate totals
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
    
    # Handle form submission
    if request.method == 'POST':
        return process_checkout(request, cart, coupon_discount)
    
    # Pre-fill form for authenticated users
    initial_data = {}
    saved_addresses = []
    if request.user.is_authenticated:
        user = request.user
        profile = user.profile
        initial_data = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'address': profile.address,
            'city': profile.city,
            'state': profile.state,
            'zipcode': profile.zipcode,
        }
        
        try:
            from accounts.models_address import Address
            saved_addresses = Address.objects.filter(user=user).order_by('-is_default', '-updated')
        except Exception:
            saved_addresses = []
    
    subtotal = cart.get_total_price()
    total_discount = compare_discount + float(coupon_discount)
    cart_total = max(1.00, subtotal - float(coupon_discount))
    
    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'initial_data': initial_data,
        'mrp_total': mrp_total,
        'compare_discount': compare_discount,
        'coupon_discount': coupon_discount,
        'discount': total_discount,
        'cart_total': cart_total,
        'subtotal': subtotal,
        'saved_addresses': saved_addresses,
    })


def process_checkout(request, cart, coupon_discount):
    """
    Process checkout form submission and handle payment method
    """
    logger.info("=== PROCESSING CHECKOUT ===")
    
    # Extract form data
    first_name = request.POST.get('first_name', '').strip()
    last_name = request.POST.get('last_name', '').strip()
    email = request.POST.get('email', '').strip()
    address = request.POST.get('address', '').strip()
    address2 = request.POST.get('address2', '').strip()
    city = request.POST.get('city', '').strip()
    state = request.POST.get('state', '').strip()
    zipcode = request.POST.get('zipcode', '').strip()
    country = request.POST.get('country', 'India').strip()
    phone = request.POST.get('phone', '').strip()
    payment_method = request.POST.get('payment', 'cod')
    
    logger.info(f"Payment method selected: {payment_method}")
    
    # Validate required fields
    if not all([first_name, email, address, city, state, zipcode, phone]):
        messages.error(request, 'Please fill in all required fields.')
        return redirect('orders:checkout')
    
    # Validate products
    for item in cart:
        product = item['product']
        quantity = item['quantity']
        product.refresh_from_db()
        
        if not product.available or not product.approved:
            messages.error(request, f'Product "{product.name}" is no longer available.')
            return redirect('cart:cart_detail')
        
        if product.stock < quantity:
            messages.error(request, f'Insufficient stock for {product.name}. Only {product.stock} available.')
            return redirect('cart:cart_detail')
    
    # Calculate final amount
    cart_total = cart.get_total_price()
    final_amount = max(1.00, cart_total - float(coupon_discount))
    
    # Route to payment method
    if payment_method == 'cashfree':
        return process_cashfree_payment(request, cart, final_amount, {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'address': address,
            'address2': address2,
            'city': city,
            'state': state,
            'zipcode': zipcode,
            'country': country,
            'phone': phone,
            'coupon_discount': coupon_discount
        })
    elif payment_method == 'cod':
        return process_cod_order(request, cart, final_amount, {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'address': address,
            'city': city,
            'state': state,
            'zipcode': zipcode,
            'phone': phone
        })
    else:
        messages.error(request, 'Invalid payment method selected.')
        return redirect('orders:checkout')


def process_cashfree_payment(request, cart, final_amount, customer_data):
    """
    Process Cashfree online payment
    Step 1: Create Cashfree order and redirect directly to payment gateway
    """
    logger.info("=== PROCESSING CASHFREE PAYMENT ===")
    
    # Initialize Cashfree service
    cashfree = CashfreeService()
    
    # Generate unique order ID
    order_id = f"order_{uuid.uuid4().hex[:16]}"
    
    # Prepare order data as per Cashfree documentation
    order_data = {
        'order_id': order_id,
        'order_amount': float(final_amount),
        'order_currency': 'INR',
        'customer_details': {
            'customer_id': str(request.user.id) if request.user.is_authenticated else f'guest_{uuid.uuid4().hex[:8]}',
            'customer_phone': customer_data['phone'],
            'customer_email': customer_data['email'],
            'customer_name': f"{customer_data['first_name']} {customer_data['last_name']}"
        },
        'order_meta': {
            'return_url': request.build_absolute_uri(f'/orders/cashfree/return/?order_id={order_id}'),
            'notify_url': request.build_absolute_uri('/orders/cashfree/webhook/')
        }
    }
    
    # Create order via Cashfree API
    result = cashfree.create_order(order_data)
    
    if not result['success']:
        logger.error(f"Failed to create Cashfree order: {result.get('error')}")
        messages.error(request, 'Payment gateway error. Please try again.')
        return redirect('orders:checkout')
    
    # Extract payment session ID
    cf_data = result['data']
    payment_session_id = cf_data.get('payment_session_id')
    cf_order_id = cf_data.get('cf_order_id')
    
    if not payment_session_id:
        logger.error("No payment_session_id in Cashfree response")
        messages.error(request, 'Payment initialization failed. Please try again.')
        return redirect('orders:checkout')
    
    # Store order data in session for later processing
    request.session['pending_order'] = {
        'cashfree_order_id': order_id,
        'cf_order_id': cf_order_id,
        'amount': str(final_amount),
        'customer': customer_data,
        'cart_items': cart.serialize()
    }
    request.session.modified = True
    
    logger.info(f"Cashfree order created: {order_id}, session_id: {payment_session_id}")
    
    # Calculate totals for checkout page
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
    
    coupon_discount = customer_data.get('coupon_discount', 0)
    total_discount = compare_discount + float(coupon_discount)
    
    # Create return URL for Cashfree
    return_url = request.build_absolute_uri(f'/orders/cashfree/return/?order_id={order_id}')
    
    # Render checkout page with Cashfree integration for direct payment
    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'initial_data': customer_data,
        'mrp_total': mrp_total,
        'compare_discount': compare_discount,
        'coupon_discount': coupon_discount,
        'discount': total_discount,
        'cart_total': final_amount,
        'subtotal': cart.get_total_price(),
        'payment_session_id': payment_session_id,
        'cashfree_env': 'sandbox' if cashfree.env == 'TEST' else 'production',
        'order_id': order_id,
        'amount': final_amount,
        'return_url': return_url,
        'redirect_to_cashfree': True
    })


def process_cod_order(request, cart, final_amount, customer_data):
    """
    Process Cash on Delivery order
    """
    logger.info("=== PROCESSING COD ORDER ===")
    
    try:
        with transaction.atomic():
            # Create order
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                first_name=customer_data['first_name'],
                last_name=customer_data['last_name'],
                email=customer_data['email'],
                address=customer_data['address'],
                city=customer_data['city'],
                state=customer_data['state'],
                zipcode=customer_data['zipcode'],
                payment_method='cod',
                total_amount=final_amount,
                paid=False,
                order_status='pending'
            )
            
            # Create order items
            for item in cart:
                product = item['product']
                quantity = item['quantity']
                
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=item['price'],
                    quantity=quantity
                )
                
                # Update stock
                product.stock -= quantity
                product.save(update_fields=['stock'])
            
            # Clear cart
            cart.clear()
            
            logger.info(f"COD order created: {order.id}")
            messages.success(request, f'Order {order.order_number} placed successfully!')
            return redirect('orders:confirmation', order_id=order.id)
            
    except Exception as e:
        logger.error(f"Error creating COD order: {str(e)}")
        messages.error(request, 'Error creating order. Please try again.')
        return redirect('orders:checkout')


def cashfree_return(request):
    """
    Handle Cashfree return URL after payment
    Step 3: Verify payment and create order
    """
    logger.info("=== CASHFREE RETURN HANDLER ===")
    logger.info(f"GET params: {request.GET.dict()}")
    
    order_id = request.GET.get('order_id')
    
    if not order_id:
        logger.error("No order_id in return URL")
        messages.error(request, 'Invalid payment return.')
        return redirect('orders:payment_failed')
    
    # Get pending order data from session
    pending_order = request.session.get('pending_order')
    
    if not pending_order:
        logger.error("No pending order data in session")
        messages.error(request, 'Session expired. Please try again.')
        return redirect('orders:payment_failed')
    
    # Verify payment with Cashfree
    cashfree = CashfreeService()
    order_status = cashfree.verify_payment(order_id)
    
    logger.info(f"Payment status for {order_id}: {order_status}")
    
    if order_status == 'PAID':
        # Payment successful - create order
        return create_confirmed_order(request, pending_order, order_id)
    elif order_status in ['ACTIVE', 'PENDING']:
        # Payment still processing - show processing page
        return render(request, 'orders/cashfree_processing.html', {
            'order_id': order_id
        })
    else:
        # Payment failed
        logger.warning(f"Payment failed: {order_status}")
        messages.error(request, 'Payment was not successful. Please try again.')
        return redirect('orders:payment_failed')


def create_confirmed_order(request, pending_order, cashfree_order_id):
    """
    Create confirmed order after successful payment
    """
    logger.info(f"=== CREATING CONFIRMED ORDER: {cashfree_order_id} ===")
    
    try:
        with transaction.atomic():
            customer = pending_order['customer']
            
            # Create order
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                first_name=customer['first_name'],
                last_name=customer['last_name'],
                email=customer['email'],
                address=customer['address'],
                city=customer['city'],
                state=customer['state'],
                zipcode=customer['zipcode'],
                payment_method='cashfree',
                payment_id=cashfree_order_id,
                total_amount=pending_order['amount'],
                paid=True,
                order_status='confirmed'
            )
            
            # Create order items
            cart_items = pending_order['cart_items']
            for product_id, item_data in cart_items.items():
                try:
                    product = Product.objects.get(id=product_id)
                    
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        price=item_data['price'],
                        quantity=item_data['quantity']
                    )
                    
                    # Update stock
                    product.stock -= item_data['quantity']
                    product.save(update_fields=['stock'])
                    
                except Product.DoesNotExist:
                    logger.error(f"Product {product_id} not found")
                    continue
            
            # Clear session data
            if 'pending_order' in request.session:
                del request.session['pending_order']
            if 'cart' in request.session:
                del request.session['cart']
            request.session.modified = True
            
            logger.info(f"Order created successfully: {order.id}")
            messages.success(request, f'Payment successful! Order {order.order_number} confirmed.')
            return redirect('orders:confirmation', order_id=order.id)
            
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}", exc_info=True)
        messages.error(request, 'Error processing your order. Please contact support.')
        return redirect('orders:payment_failed')


@csrf_exempt
def cashfree_webhook(request):
    """
    Handle Cashfree webhook notifications with signature verification
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
    
    try:
        import json
        import hashlib
        import hmac
        
        # Get raw body for signature verification
        raw_body = request.body
        data = json.loads(raw_body)
        
        # Verify webhook signature for security (production requirement)
        received_signature = request.headers.get('x-webhook-signature', '')
        if received_signature and hasattr(settings, 'CASHFREE_SECRET_KEY'):
            # Generate expected signature
            secret_key = getattr(settings, 'CASHFREE_SECRET_KEY', '')
            expected_signature = hmac.new(
                secret_key.encode('utf-8'),
                raw_body,
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(received_signature, expected_signature):
                logger.warning(f"Webhook signature verification failed for data: {data}")
                return JsonResponse({'status': 'error', 'message': 'Invalid signature'}, status=403)
        
        logger.info(f"Cashfree webhook received: {data}")
        
        order_id = data.get('order', {}).get('order_id')
        order_status = data.get('order', {}).get('order_status')
        
        if order_id and order_status:
            logger.info(f"Webhook: Order {order_id}, Status: {order_status}")
            
            # Update order status in database if needed
            try:
                order = Order.objects.get(cashfree_order_id=order_id)
                if order_status == 'PAID':
                    order.status = 'paid'
                    order.save()
                    logger.info(f"Updated order {order.id} status to paid")
            except Order.DoesNotExist:
                logger.warning(f"Order with cashfree_order_id {order_id} not found")
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def cashfree_status(request):
    """
    AJAX endpoint to check payment status (for polling)
    """
    order_id = request.GET.get('order_id')
    
    if not order_id:
        return JsonResponse({'status': 'ERROR', 'message': 'No order_id provided'})
    
    cashfree = CashfreeService()
    status = cashfree.verify_payment(order_id)
    
    return JsonResponse({'status': status})


def confirmation(request, order_id):
    """Order confirmation page"""
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/confirmation.html', {'order': order})


def payment_failed(request):
    """Payment failed page"""
    return render(request, 'orders/payment_failed.html')
