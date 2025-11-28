from django.http import JsonResponse
# Cashfree integration
import requests
import json
from decimal import Decimal
from django.conf import settings

# Import login_required before using it
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

def verify_payment_status(cf_order_id):
    """Verify payment status with Cashfree API"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        app_id = getattr(settings, 'CASHFREE_APP_ID')
        secret_key = getattr(settings, 'CASHFREE_SECRET_KEY')
        env = getattr(settings, 'CASHFREE_ENV', 'TEST')
        
        if env == 'PRODUCTION':
            base_url = 'https://api.cashfree.com'
        else:
            base_url = 'https://sandbox.cashfree.com'
        
        url = f"{base_url}/pg/orders/{cf_order_id}"
        
        headers = {
            'x-api-version': '2023-08-01',
            'x-client-id': app_id,
            'x-client-secret': secret_key,
            'Content-Type': 'application/json'
        }
        
        logger.info(f'Verifying payment status for order {cf_order_id} at {url}')
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f'=== CASHFREE API FULL RESPONSE FOR {cf_order_id} ===')
            logger.info(f'Full response data: {json.dumps(data, indent=2)}')
            
            order_status = data.get('order_status', 'FAILED')
            payment_status = data.get('payment_status', 'FAILED')  # Sometimes it's payment_status instead
            logger.info(f'Extracted order_status: "{order_status}"')
            logger.info(f'Extracted payment_status: "{payment_status}"')
            
            # Return the more specific status if available
            if payment_status in ['SUCCESS', 'PAID']:
                logger.info(f'Returning PAID based on payment_status: {payment_status}')
                return 'PAID'
            elif order_status in ['PAID', 'SUCCESS']:
                logger.info(f'Returning PAID based on order_status: {order_status}')
                return 'PAID'
            else:
                final_status = order_status or payment_status or 'FAILED'
                logger.info(f'Returning final status: {final_status}')
                return final_status
        else:
            logger.error(f'Failed to verify payment: {response.status_code} - {response.text}')
            return 'FAILED'
    except Exception as e:
        logger.error(f'Error verifying payment status: {str(e)}')
        return 'FAILED'

# Seller: Cancel entire order
@login_required
@require_POST
def cancel_order(request, order_id):
    """Seller cancels the entire order (sets status to 'cancelled' for order and all items)"""
    if not hasattr(request.user, 'profile') or not request.user.profile.is_seller:
        messages.error(request, 'Access denied. Only sellers can cancel orders.')
        return redirect('accounts:seller_dashboard')

    order = get_object_or_404(Order, id=order_id)
    # Verify seller owns products in this order
    seller_products = Product.objects.filter(seller=request.user)
    if not order.items.filter(product__in=seller_products).exists():
        messages.error(request, 'You do not have permission to cancel this order.')
        return redirect('orders:seller_orders')

    # Set status to cancelled for order and all items
    order.order_status = 'cancelled'
    order.save()
    order.items.update(status='cancelled')
    messages.success(request, f'Order {order.id} cancelled successfully.')
    return redirect('orders:seller_orders')
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from .models import Order, OrderItem
from cart.cart import Cart
from store.models import Product
from .shiprocket import ShiprocketAPI


from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

# Seller: View all orders for their products

@login_required
def seller_orders(request):
    if not hasattr(request.user, 'profile') or not request.user.profile.is_seller:
        messages.error(request, 'Access denied. Only sellers can view this page.')
        return redirect('accounts:seller_dashboard')

    # Get all products for this seller
    seller_products = Product.objects.filter(seller=request.user)
    # Get all order items for these products
    order_items = OrderItem.objects.filter(product__in=seller_products).select_related('order', 'product')

    # Group by order
    orders = {}
    for item in order_items:
        order = item.order
        if order.id not in orders:
            orders[order.id] = {
                'order': order,
                'items': []
            }
        orders[order.id]['items'].append(item)

    return render(request, 'orders/seller_orders.html', {'orders': orders.values()})

# Seller: Update order status for their product
@login_required
def update_order_status(request, order_id, item_id):
    if not hasattr(request.user, 'profile') or not request.user.profile.is_seller:
        messages.error(request, 'Access denied. Only sellers can update order status.')
        return redirect('accounts:seller_dashboard')

    order_item = get_object_or_404(OrderItem, id=item_id, product__seller=request.user)
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in ['pending', 'processing', 'shipped', 'delivered', 'cancelled']:
            order_item.status = status
            order_item.save()
            # Recalculate parent order's overall status based on item statuses.
            # Re-fetch the Order from the DB to avoid stale related-object state
            from .models import Order
            order = Order.objects.get(id=order_item.order_id)
            # Rules:
            # - If all items are 'cancelled' -> order.order_status = 'cancelled'
            # - Otherwise pick the highest-progress status among items: pending < processing < shipped < delivered
            status_rank = {'pending': 0, 'processing': 1, 'shipped': 2, 'delivered': 3}
            item_statuses = list(order.items.values_list('status', flat=True))

            if item_statuses and all(s == 'cancelled' for s in item_statuses):
                order.order_status = 'cancelled'
            else:
                # pick max rank (ignore cancelled for progression)
                ranks = [status_rank.get(s, 0) for s in item_statuses if s != 'cancelled']
                if ranks:
                    max_rank = max(ranks)
                    # reverse lookup
                    for k, v in status_rank.items():
                        if v == max_rank:
                            order.order_status = k
                            break
                else:
                    # fallback
                    order.order_status = 'pending'

            order.save()
            messages.success(request, f'Order status updated to {status}.')
        else:
            messages.error(request, 'Invalid status.')
    return redirect('orders:seller_orders')


def checkout(request):
    import logging
    logger = logging.getLogger(__name__)
    if hasattr(request.user, 'profile') and request.user.profile.is_seller:
        messages.error(request, 'Sellers cannot purchase products.')
        return redirect('accounts:seller_dashboard')

    cart = Cart(request)
    if len(cart) == 0:
        messages.error(request, 'Your cart is empty.')
        return redirect('cart:cart_detail')

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

    # Ensure cart items persist after login
    request.session['cart'] = cart.serialize()

    order_id = None

    if request.method == 'POST':
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info('=== CHECKOUT POST REQUEST STARTED ===')
        logger.info(f'POST data: {dict(request.POST)}')
        
        # Safely fetch posted form data
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
        payment_method = request.POST.get('payment', 'cod')  # Default to COD instead of razorpay
        save_address = request.POST.get('save_address')
        
        # Debug: Log the received payment method
        logger.info(f'=== PAYMENT METHOD DEBUGGING ===')
        logger.info(f'Raw payment value from form: "{request.POST.get("payment")}"')
        logger.info(f'Processed payment_method: "{payment_method}"')
        logger.info(f'Available form fields: {list(request.POST.keys())}')
        logger.info(f'Cashfree enabled: {getattr(settings, "CASHFREE_ENABLED", False)}')


        # Save address to Address model if requested and user is authenticated
        if save_address and request.user.is_authenticated:
            from accounts.models_address import Address
            Address.objects.create(
                user=request.user,
                full_name=first_name + (f" {last_name}" if last_name else ""),
                phone=phone,
                address_line1=address,
                address_line2=address2,
                city=city,
                state=state,
                postal_code=zipcode,
                country=country,
            )

        # Basic validation - ensure required fields are present
        missing = []
        for field_name, value in (('first_name', first_name), ('email', email), ('address', address)):
            if not value:
                missing.append(field_name)

        if missing:
            messages.error(request, 'Please fill in all required fields: ' + ', '.join(missing))
            initial_data = {
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'address': address,
                'city': city,
                'state': state,
                'zipcode': zipcode,
            }
            return render(request, 'orders/checkout.html', {
                'cart': cart,
                'initial_data': initial_data,
                'compare_discount': compare_discount,
                'coupon_discount': coupon_discount,
                'discount': compare_discount + float(coupon_discount),
                'subtotal': cart.get_total_price()
            })

        # Shiprocket pincode serviceability check (after all fields are extracted and validated)
        if zipcode:
            from .shiprocket_api import check_pincode_serviceability
            
            is_cod = payment_method == 'cod' or payment_method == 'cashOnDelivery'
            payment_type = 'cod' if is_cod else 'prepaid'
            print(f"DEBUG: is_cod: {is_cod}, payment_type: {payment_type}")
            
            serviceable = check_pincode_serviceability(zipcode, payment_type)
            print(f"DEBUG: Serviceability result: {serviceable}")
            
            if not serviceable:
                messages.error(request, f'Shipping is not available for pincode {zipcode} with the selected payment method.')
                initial_data = {
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'address': address,
                    'city': city,
                    'state': state,
                    'zipcode': zipcode,
                }
                return render(request, 'orders/checkout.html', {
                    'cart': cart,
                    'initial_data': initial_data,
                    'compare_discount': compare_discount,
                    'coupon_discount': coupon_discount,
                    'discount': compare_discount + float(coupon_discount),
                    'subtotal': cart.get_total_price()
                })

        # Validate all products before creating order
        for item in cart:
            product = item['product']
            quantity = item['quantity']
            # Refresh product from database to get latest stock
            product.refresh_from_db()
            if not product.available or not product.approved:
                messages.error(request, f'Product "{product.name}" is no longer available. (Available: {product.available}, Approved: {product.approved})')
                return redirect('cart:cart_detail')
            if product.stock < quantity:
                messages.error(request, f'Insufficient stock for {product.name}. Only {product.stock} available.')
                return redirect('cart:cart_detail')

        # Calculate final amount
        cart_total = cart.get_total_price()
        final_amount = max(1.00, cart_total - float(coupon_discount))  # Ensure minimum ₹1

        # Handle payment method
        logger.info(f'Processing payment method: {payment_method}')
        logger.info(f'Available payment methods: cashfree (enabled: {getattr(settings, "CASHFREE_ENABLED", False)}), cod')
        
        if payment_method == 'cashfree' and getattr(settings, 'CASHFREE_ENABLED', False):
            logger.info('Processing Cashfree payment')
            
            # Get Cashfree configuration
            app_id = getattr(settings, 'CASHFREE_APP_ID', '')
            secret_key = getattr(settings, 'CASHFREE_SECRET_KEY', '')
            env = getattr(settings, 'CASHFREE_ENV', 'TEST')
            
            if not app_id or not secret_key:
                logger.error('Cashfree credentials not configured')
                messages.error(request, 'Payment gateway configuration error. Please try again later.')
                return redirect('cart:cart_detail')
            
            # Determine API endpoint
            if env == 'TEST':
                base_url = 'https://sandbox.cashfree.com'
            else:
                base_url = 'https://api.cashfree.com'
            
            logger.info(f'Using Cashfree environment: {env}, URL: {base_url}')
            
            try:
                # Generate a unique order ID for Cashfree
                import uuid
                cashfree_order_id = f"{uuid.uuid4()}"
                
                # Prepare order data for Cashfree (WITHOUT creating order yet)
                order_data = {
                    'order_id': cashfree_order_id,
                    'order_amount': float(final_amount),
                    'order_currency': 'INR',
                    'customer_details': {
                        'customer_id': str(request.user.id) if request.user.is_authenticated else f'guest_{uuid.uuid4()}',
                        'customer_phone': phone,
                        'customer_email': email,
                        'customer_name': f'{first_name} {last_name}'
                    },
                    'order_meta': {
                        # Always include order_id in return_url for reliable return processing
                        'return_url': request.build_absolute_uri(f'/orders/cashfree/return/?order_id={cashfree_order_id}'),
                        'notify_url': request.build_absolute_uri('/orders/cashfree/verify/')
                    }
                }
                
                # API headers
                headers = {
                    'x-api-version': '2023-08-01',
                    'x-client-id': app_id,
                    'x-client-secret': secret_key,
                    'Content-Type': 'application/json'
                }
                
                logger.info(f'Creating Cashfree session for payment of ₹{final_amount}')
                
                # Make API call to Cashfree
                response = requests.post(
                    f'{base_url}/pg/orders',
                    headers=headers,
                    json=order_data,
                    timeout=30
                )
                
                logger.info(f'Cashfree API response status: {response.status_code}')
                logger.info(f'Cashfree API response text: {response.text}')
                
                if response.status_code == 200:
                    result = response.json()
                    payment_session_id = result.get('payment_session_id')
                    cf_order_id = result.get('cf_order_id')
                    
                    if payment_session_id:
                        # Store cart data and user info in session (order will be created after payment)
                        request.session['cashfree_payment_session_id'] = payment_session_id
                        request.session['cashfree_order_id'] = cashfree_order_id
                        request.session['pending_order_data'] = {
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
                            'payment_method': payment_method,
                            'total_amount': str(final_amount),
                            'cart_items': cart.serialize(),
                            'coupon_discount': str(coupon_discount)
                        }
                        request.session.modified = True
                        
                        logger.info(f'Created Cashfree payment session, redirecting to payment page')
                        
                        # For Cashfree, DO NOT clear cart yet - clear only after successful payment
                        # Cart will be cleared in cashfree_return view on success
                        
                        # Redirect to payment page
                        return redirect('orders:cashfree_payment', order_id=cashfree_order_id)
                    else:
                        logger.error('No payment_session_id received from Cashfree')
                        messages.error(request, 'Unable to process payment. Please try again.')
                        return redirect('cart:cart_detail')
                else:
                    error_data = response.text
                    logger.error(f'Cashfree API error {response.status_code}: {error_data}')
                    messages.error(request, 'Payment gateway temporarily unavailable. Please try again later.')
                    return redirect('cart:cart_detail')
                    
            except requests.exceptions.Timeout:
                logger.error('Cashfree API timeout')
                messages.error(request, 'Payment gateway timeout. Please try again.')
                return redirect('cart:cart_detail')
            except requests.exceptions.RequestException as e:
                logger.error(f'Cashfree API request error: {str(e)}')
                messages.error(request, 'Payment gateway error. Please try again later.')
                return redirect('cart:cart_detail')
            except Exception as e:
                logger.error(f'Unexpected Cashfree error: {str(e)}')
                messages.error(request, 'Payment processing error. Please try again.')
                return redirect('cart:cart_detail')
        
        # COD or other payment methods - create order immediately
        elif payment_method in ['cod', 'cashOnDelivery']:
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    address=address,
                    city=city,
                    state=state,
                    zipcode=zipcode,
                    payment_method=payment_method,
                    total_amount=final_amount,
                    paid=True  # COD orders are marked as paid but not yet confirmed
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
                    # Update stock
                    product.stock -= quantity
                    product.save(update_fields=['stock'])
            
            cart.clear()
            messages.success(request, f'Order {order.id} placed successfully!')
            return redirect('orders:confirmation', order_id=order.id)
        
        # Handle other payment methods (fallback)
        else:
            logger.error(f'Unhandled payment method: {payment_method}, enabled: {getattr(settings, "CASHFREE_ENABLED", False)}')
            messages.error(request, f'Invalid payment method selected: {payment_method}. Please try again.')
            return redirect('cart:cart_detail')

    # GET request - render checkout form
    # Pre-fill form data for authenticated users
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
        # Fetch all saved addresses for dropdown
        try:
            from accounts.models_address import Address
            saved_addresses = Address.objects.filter(user=user).order_by('-is_default', '-updated')
        except Exception:
            saved_addresses = []

    subtotal = cart.get_total_price()
    total_discount = compare_discount + float(coupon_discount)
    cart_total = max(1.00, subtotal - float(coupon_discount))  # Final amount (actual price minus coupon), minimum ₹1
    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'initial_data': initial_data,
        'mrp_total': mrp_total,  # Price shown as "Price (X items)"
        'compare_discount': compare_discount,
        'coupon_discount': coupon_discount,
        'discount': total_discount,
        'cart_total': cart_total,
        'subtotal': subtotal,
        'saved_addresses': saved_addresses,
    })


# Cashfree payment verification view

def cashfree_payment(request, order_id):
    """Display Cashfree payment page with JS SDK"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Get payment session from session
        payment_session_id = request.session.get('cashfree_payment_session_id')
        pending_order_data = request.session.get('pending_order_data')
        
        if not payment_session_id:
            logger.error(f'No payment session found for order {order_id}')
            messages.error(request, 'Payment session expired. Please try again.')
            return redirect('cart:cart_detail')
        
        if not pending_order_data:
            logger.error(f'No pending order data found for {order_id}')
            messages.error(request, 'Order data expired. Please try again.')
            return redirect('cart:cart_detail')
        
        # Create a temporary order object for template display
        class TempOrder:
            def __init__(self, data):
                self.id = data.get('temp_id', 'pending')
                self.total_amount = data.get('total_amount', 0)
        
        order = TempOrder(pending_order_data)
        
        # Get environment (lowercase for SDK)
        env = getattr(settings, 'CASHFREE_ENV', 'TEST')
        env_lowercase = env.lower() if env == 'PRODUCTION' else 'sandbox'
        
        context = {
            'order': order,
            'payment_session_id': payment_session_id,
            'cashfree_env': env_lowercase,
            'return_url': request.build_absolute_uri('/orders/cashfree/return/'),
        }
        
        return render(request, 'orders/cashfree_payment.html', context)
        
    except Exception as e:
        logger.error(f'Error loading Cashfree payment page: {str(e)}')
        messages.error(request, 'Payment page error. Please try again.')
        return redirect('cart:cart_detail')


@csrf_exempt
def cashfree_verify(request):
    """Handle Cashfree payment webhook verification - CREATE ORDER ONLY ON SUCCESS"""
    import logging
    import json
    import hmac
    import hashlib
    
    logger = logging.getLogger(__name__)
    
    if request.method != 'POST':
        logger.warning('Invalid method for Cashfree webhook')
        return JsonResponse({'status': 'error', 'message': 'Invalid method'})
    
    try:
        # Get raw request body
        raw_body = request.body
        
        # Parse JSON data
        try:
            data = json.loads(raw_body)
        except json.JSONDecodeError:
            logger.error('Invalid JSON in Cashfree webhook')
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'})
        
        logger.info(f'Cashfree webhook received: {data}')
        
        # Production webhook signature verification
        if getattr(settings, 'CASHFREE_ENV', 'TEST') == 'PROD':
            webhook_signature = request.headers.get('x-webhook-signature')
            webhook_timestamp = request.headers.get('x-webhook-timestamp')
            
            if not webhook_signature or not webhook_timestamp:
                logger.error('Missing webhook signature or timestamp in production')
                return JsonResponse({'status': 'error', 'message': 'Invalid webhook'})
            
            # Verify webhook signature
            try:
                expected_signature = hmac.new(
                    settings.CASHFREE_SECRET_KEY.encode(),
                    (webhook_timestamp + raw_body.decode()).encode(),
                    hashlib.sha256
                ).hexdigest()
                
                if not hmac.compare_digest(webhook_signature, expected_signature):
                    logger.error('Invalid webhook signature verification')
                    return JsonResponse({'status': 'error', 'message': 'Invalid signature'})
                    
            except Exception as e:
                logger.error(f'Error verifying webhook signature: {str(e)}')
                return JsonResponse({'status': 'error', 'message': 'Signature verification failed'})
        
        # Extract payment details
        cf_order_id = data.get('order_id')  # Cashfree order ID
        payment_status = data.get('payment_status')
        
        if not cf_order_id:
            logger.error('Missing order_id in webhook data')
            return JsonResponse({'status': 'error', 'message': 'Missing order ID'})
        
        logger.info(f'Processing webhook for Cashfree order {cf_order_id} with status {payment_status}')
        
        # Only create order on successful payment
        if payment_status == 'SUCCESS':
            # Log successful payment but don't create order here
            # Order will be created in return view to avoid race conditions
            logger.info(f'Payment successful for Cashfree order {cf_order_id} - order will be created on return')
            return JsonResponse({'status': 'success', 'message': 'Payment successful'})
            
        elif payment_status == 'FAILED' or payment_status == 'CANCELLED':
            logger.warning(f'Payment {payment_status} for Cashfree order {cf_order_id} - NO order will be created')
            return JsonResponse({'status': 'payment_failed', 'message': f'Payment {payment_status}'})
            
        else:
            logger.warning(f'Unknown payment status for Cashfree order {cf_order_id}: {payment_status}')
            return JsonResponse({'status': 'unknown', 'message': f'Unknown status: {payment_status}'})
            
    except Exception as e:
        logger.error(f'Cashfree webhook processing error: {str(e)}')
        return JsonResponse({'status': 'error', 'message': 'Internal server error'})


def cashfree_return(request):
    """Handle Cashfree return URL after payment (user is redirected back)"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info('=== CASHFREE RETURN HANDLER STARTED ===')
    logger.info(f'Request method: {request.method}')
    logger.info(f'Request path: {request.path}')
    logger.info(f'User authenticated: {request.user.is_authenticated}')
    
    try:
        # Log all query params for debugging
        logger.info(f'Cashfree return GET params: {request.GET.dict()}')
        logger.info(f'Session keys: {list(request.session.keys())}')

        # Try all possible parameter names
        cf_order_id = (
            request.GET.get('order_id') or
            request.GET.get('cf_order_id') or
            request.GET.get('orderReference') or
            request.GET.get('orderreference') or
            request.GET.get('reference')
        )

        if not cf_order_id:
            logger.error('=== ORDER ID NOT FOUND IN RETURN URL ===')
            logger.error(f'Available GET params: {request.GET.dict()}')
            logger.error('Redirecting to cart due to missing order ID')
            messages.error(request, 'Invalid payment return - no order ID found.')
            return redirect('cart:cart_detail')

        logger.info(f'User returned from Cashfree payment for order {cf_order_id}')
        
        # Log session data for debugging
        logger.info(f"Session pending_order_data exists: {'pending_order_data' in request.session}")
        if 'pending_order_data' in request.session:
            pending_data = request.session['pending_order_data']
            logger.info(f"Pending order data keys: {list(pending_data.keys()) if pending_data else 'None'}")
        
        # Verify payment status with Cashfree API
        logger.info(f'=== VERIFYING PAYMENT STATUS FOR ORDER: {cf_order_id} ===')
        payment_status = verify_payment_status(cf_order_id)
        logger.info(f'Payment verification result: "{payment_status}"')
        logger.info(f'Checking if "{payment_status}" is in ["PAID", "SUCCESS"]')
        
        # Accept both "PAID" and "SUCCESS" as successful payment statuses
        if payment_status in ['PAID', 'SUCCESS']:
            logger.info('=== PAYMENT STATUS IS SUCCESSFUL, CREATING ORDER ===')
            # Payment successful - create the order now
            pending_data = request.session.get('pending_order_data')
            logger.info(f'Pending order data found: {pending_data is not None}')
            if pending_data:
                logger.info(f'Pending data keys: {list(pending_data.keys())}')
                logger.info(f'Cart items count: {len(pending_data.get("cart_items", {}))}')
            
            if not pending_data:
                logger.error('=== PENDING ORDER DATA EXPIRED OR MISSING ===')
                messages.error(request, 'Order data expired. Please try again.')
                return redirect('cart:cart_detail')
            
            try:
                with transaction.atomic():
                    # Create the order
                    order = Order.objects.create(
                        user=request.user if request.user.is_authenticated else None,
                        payment_id=cf_order_id,
                        payment_method='cashfree',
                        paid=True,
                        order_status='confirmed',
                        email=pending_data.get('email', ''),
                        first_name=pending_data.get('first_name', ''),
                        last_name=pending_data.get('last_name', ''),
                        phone_number=pending_data.get('phone', ''),
                        address=pending_data.get('address', ''),
                        city=pending_data.get('city', ''),
                        state=pending_data.get('state', ''),
                        country=pending_data.get('country', 'India'),
                        postal_code=pending_data.get('zipcode', ''),
                        total_amount=pending_data.get('total_amount', 0)
                    )
                    
                    # Create order items from stored cart data
                    cart_items = pending_data.get('cart_items', {})
                    logger.info(f'Creating order items from cart data: {cart_items}')
                    
                    for product_id, item_data in cart_items.items():
                        try:
                            product = Product.objects.get(id=product_id)
                            OrderItem.objects.create(
                                order=order,
                                product=product,
                                price=Decimal(str(item_data['price'])),
                                quantity=item_data['quantity']
                            )
                            # Reduce stock
                            product.stock -= item_data['quantity']
                            product.save()
                            logger.info(f'Created order item: {product.name} x {item_data["quantity"]}')
                        except Product.DoesNotExist:
                            logger.error(f'Product {product_id} not found when creating order')
                            continue
                        except Exception as e:
                            logger.error(f'Error creating order item for product {product_id}: {str(e)}')
                            continue
                    
                    # Clear cart and session data
                    if 'cart' in request.session:
                        del request.session['cart']
                    if 'pending_order_data' in request.session:
                        del request.session['pending_order_data']
                    if 'cashfree_payment_session_id' in request.session:
                        del request.session['cashfree_payment_session_id']
                    if 'cashfree_order_id' in request.session:
                        del request.session['cashfree_order_id']
                    
                    logger.info(f'Order {order.id} created successfully with {order.items.count()} items')
                    messages.success(request, f'Payment successful! Order {order.id} confirmed.')
                    return redirect('orders:confirmation', order_id=order.id)
                    
            except Exception as e:
                logger.error(f'=== ERROR CREATING ORDER AFTER PAYMENT ===')
                logger.error(f'Exception: {type(e).__name__}: {str(e)}')
                import traceback
                logger.error(f'Traceback: {traceback.format_exc()}')
                messages.error(request, 'Error processing your order. Please contact support.')
                logger.error('Redirecting to store:home due to order creation error')
                return redirect('store:home')
                
        elif payment_status in ['FAILED', 'CANCELLED']:
            # Payment failed - redirect to failure page and keep cart intact
            logger.warning(f'=== PAYMENT FAILED FOR ORDER {cf_order_id}, STATUS: {payment_status} ===')
            return redirect('orders:payment_failed')
        else:
            # Payment is still pending/processing, show processing page and poll
            logger.info(f'=== PAYMENT PENDING/PROCESSING FOR ORDER {cf_order_id}, STATUS: {payment_status} ===')
            logger.info('Showing processing page for status polling')
            return render(request, 'orders/cashfree_processing.html', {'order_id': cf_order_id})
    except Exception as e:
        logger.error(f'=== MAIN EXCEPTION IN CASHFREE_RETURN ===')
        logger.error(f'Exception: {type(e).__name__}: {str(e)}')
        import traceback
        logger.error(f'Traceback: {traceback.format_exc()}')
        messages.error(request, 'An error occurred processing your payment.')
        logger.error('Redirecting to cart:cart_detail due to main exception')
        return redirect('cart:cart_detail')

def cashfree_status(request):
    """AJAX endpoint to poll payment status for Cashfree order"""
    import logging
    logger = logging.getLogger(__name__)
    order_id = request.GET.get('order_id')
    if not order_id:
        return JsonResponse({'status': 'error', 'message': 'Missing order_id'})
    status = verify_payment_status(order_id)
    logger.info(f'[AJAX] Polled payment status for {order_id}: {status}')
    return JsonResponse({'status': status})


def confirmation(request, order_id):
    """Order confirmation page"""
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/confirmation.html', {'order': order})


def payment_failed(request):
    """Payment failed page - cart items are preserved"""
    return render(request, 'orders/payment_failed.html')


def order_detail(request, order_id=None):
    # Allow both UUID and order_number
    order = None
    if order_id:
        try:
            order = Order.objects.get(id=order_id)
        except (Order.DoesNotExist, ValueError):
            try:
                order = Order.objects.get(order_number=order_id)
            except Order.DoesNotExist:
                order = None
    if not order:
        messages.error(request, 'Order not found.')
        return redirect('orders:track_order')

    # If user is authenticated, allow if owner or staff
    if request.user.is_authenticated:
        if order.user and order.user != request.user and not request.user.is_staff:
            messages.error(request, 'You do not have permission to view this order.')
            return redirect('store:home')
    else:
        # For guests, require email match via session or GET param
        guest_email = request.session.get('guest_email') or request.GET.get('email')
        if order.user is not None:
            messages.error(request, 'Please log in to view this order.')
            return redirect('accounts:login')
        if not guest_email or guest_email.lower() != order.email.lower():
            messages.error(request, 'Email does not match for this order.')
            return redirect('orders:track_order')
    return render(request, 'orders/detail.html', {'order': order})

# Public order tracking page for guests
from django import forms
class TrackOrderForm(forms.Form):
    order_number = forms.CharField(label='Order Number', max_length=20)
    email = forms.EmailField(label='Email')

def track_order(request):
    if request.method == 'POST':
        form = TrackOrderForm(request.POST)
        if form.is_valid():
            order_number = form.cleaned_data['order_number']
            email = form.cleaned_data['email']
            try:
                order = Order.objects.get(order_number=order_number, email__iexact=email)
                # Store guest email in session for detail view
                request.session['guest_email'] = email
                return redirect('orders:order_detail', order_id=order.order_number)
            except Order.DoesNotExist:
                form.add_error(None, 'Order not found or email does not match.')
    else:
        form = TrackOrderForm()
    return render(request, 'orders/track_order.html', {'form': form})

# Shiprocket Integration Views

@login_required
def create_shiprocket_order(request, order_id):
    """Create order in Shiprocket for shipment"""
    if not hasattr(request.user, 'profile') or not request.user.profile.is_seller:
        messages.error(request, 'Access denied. Only sellers can create shipments.')
        return redirect('accounts:seller_dashboard')
    
    # Check if Shiprocket is enabled
    if not getattr(settings, 'SHIPROCKET_ENABLED', False):
        messages.warning(request, 'Shiprocket integration is currently disabled.')
        return redirect('orders:seller_orders')
    
    order = get_object_or_404(Order, id=order_id)
    
    # Verify seller owns products in this order
    seller_products = Product.objects.filter(seller=request.user)
    if not order.items.filter(product__in=seller_products).exists():
        messages.error(request, 'You do not have permission to ship this order.')
        return redirect('orders:seller_orders')
    
    if order.shiprocket_order_id:
        messages.warning(request, 'Shiprocket order already created for this order.')
        return redirect('orders:seller_orders')
    
    # Do not mark as paid for COD orders; Shiprocket will receive correct payment method
    shiprocket = ShiprocketAPI()
    result = shiprocket.create_order(order)
    
    if result.get('order_id'):
        order.shiprocket_order_id = result.get('order_id')
        order.shiprocket_shipment_id = result.get('shipment_id')
        
        # Try to get AWB code if available in response
        if result.get('awb_code'):
            order.awb_code = result.get('awb_code')
        
        # Get courier name if available
        if result.get('courier_name'):
            order.courier_name = result.get('courier_name')
        
        # Update order status to processing
        order.order_status = 'processing'
        order.save()
        
        messages.success(request, f'Shiprocket order created successfully! Order ID: {result.get("order_id")}')
        
        # If AWB not in response, try to get recommended courier
        if not order.awb_code:
            messages.info(request, 'Shipment created. AWB will be assigned when courier picks up the package.')
    else:
        messages.error(request, f'Failed to create Shiprocket order: {result.get("error", "Unknown error")}')
    
    return redirect('orders:seller_orders')


@login_required
def track_shipment(request, order_id):
    """Track shipment status"""
    order = get_object_or_404(Order, id=order_id)
    
    # Check permission
    if request.user.is_authenticated:
        if order.user != request.user:
            # Check if seller
            if hasattr(request.user, 'profile') and request.user.profile.is_seller:
                seller_products = Product.objects.filter(seller=request.user)
                if not order.items.filter(product__in=seller_products).exists():
                    messages.error(request, 'Access denied.')
                    return redirect('store:home')
            else:
                messages.error(request, 'Access denied.')
                return redirect('store:home')
    
    if not order.awb_code:
        messages.error(request, 'No tracking information available for this order.')
        return redirect('orders:order_detail', order_id=order.id)
    
    # Track shipment
    shiprocket = ShiprocketAPI()
    tracking_data = shiprocket.track_shipment(order.awb_code)
    
    context = {
        'order': order,
        'tracking_data': tracking_data
    }
    
    return render(request, 'orders/tracking.html', context)


# Shiprocket Webhook Handler
@csrf_exempt
def shiprocket_webhook(request):
    """Handle Shiprocket webhook notifications for order status updates"""
    if request.method != 'POST':
        return redirect('store:home')
    
    try:
        import json
        data = json.loads(request.body)
        
        # Extract webhook data
        awb_code = data.get('awb')
        shipment_status = data.get('current_status', '').lower()
        
        if not awb_code:
            return redirect('store:home')
        
        # Find order by AWB code
        try:
            order = Order.objects.get(awb_code=awb_code)
        except Order.DoesNotExist:
            return redirect('store:home')
        
        # Map Shiprocket status to our order status
        status_mapping = {
            'pickup scheduled': 'processing',
            'shipped': 'shipped',
            'in transit': 'shipped',
            'out for delivery': 'shipped',
            'delivered': 'delivered',
            'cancelled': 'cancelled',
            'rto': 'cancelled',
        }
        
        new_status = status_mapping.get(shipment_status)
        
        if new_status and order.order_status != new_status:
            order.order_status = new_status
            order.save()
            
            # Update all order items status as well
            order.items.all().update(status=new_status)
        
        from django.http import JsonResponse
        return JsonResponse({'status': 'success'})
    
    except Exception as e:
        from django.http import JsonResponse
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
