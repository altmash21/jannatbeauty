# Cashfree integration
import requests
import json

# Import login_required before using it
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
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

        # Create order and order items atomically
        with transaction.atomic():
            # Calculate final amount properly
            # cart.get_total_price() already includes discounted prices
            # Only apply coupon discount, not both discounts
            cart_total = cart.get_total_price()
            final_amount = max(1.00, cart_total - float(coupon_discount))  # Ensure minimum ₹1 for Razorpay
            
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
                total_amount=final_amount
            )
            order_id = str(order.id)

            # Create order items and update stock (all validated)
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

        # Handle payment method
        if payment_method == 'cashfree' and getattr(settings, 'CASHFREE_ENABLED', False):
            # Cashfree order creation using HTTP API
            app_id = getattr(settings, 'CASHFREE_APP_ID', '')
            secret_key = getattr(settings, 'CASHFREE_SECRET_KEY', '')
            env = getattr(settings, 'CASHFREE_ENV', 'TEST')
            
            # Configure Cashfree API endpoint
            base_url = "https://sandbox.cashfree.com" if env == "TEST" else "https://api.cashfree.com"
            
            try:
                headers = {
                    "x-api-version": "2022-09-01",
                    "x-client-id": app_id,
                    "x-client-secret": secret_key,
                    "Content-Type": "application/json"
                }
                
                order_data = {
                    "order_id": str(order.id),
                    "order_amount": float(order.total_amount),
                    "order_currency": "INR",
                    "customer_details": {
                        "customer_id": str(order.user.id) if order.user else f"guest_{order.id}",
                        "customer_phone": order.user.profile.phone if order.user and hasattr(order.user, 'profile') else phone,
                        "customer_email": order.email
                    },
                    "order_meta": {
                        "return_url": request.build_absolute_uri('/orders/confirmation/' + str(order.id) + '/'),
                        "notify_url": request.build_absolute_uri('/orders/cashfree/verify/')
                    }
                }
                
                response = requests.post(
                    f"{base_url}/pg/orders",
                    headers=headers,
                    json=order_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    payment_link = result.get('payment_link')
                    if payment_link:
                        # Clear cart and redirect to Cashfree payment page
                        cart.clear()
                        order.payment_id = result.get('cf_order_id', str(order.id))
                        order.save()
                        return redirect(payment_link)
                    else:
                        messages.error(request, 'Payment link not received from Cashfree. Please try again.')
                        return redirect('cart:cart_detail')
                else:
                    messages.error(request, 'Payment gateway error. Please try again.')
                    return redirect('cart:cart_detail')
                    
            except Exception as e:
                messages.error(request, f'Payment processing error: {str(e)}')
                return redirect('cart:cart_detail')
        else:
            order.save()
            cart.clear()
            messages.success(request, f'Order {order.id} placed successfully!')
            return redirect('orders:confirmation', order_id=order.id)

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
@csrf_exempt
def cashfree_verify(request):
    import logging
    logger = logging.getLogger(__name__)
    
    if request.method == 'POST':
        try:
            import json
            import hmac
            import hashlib
            
            # Get raw body for signature verification
            raw_body = request.body
            data = json.loads(raw_body)
            
            # Production security: Verify webhook signature
            if getattr(settings, 'CASHFREE_ENV', 'TEST') == 'PROD':
                webhook_signature = request.headers.get('x-webhook-signature')
                webhook_timestamp = request.headers.get('x-webhook-timestamp')
                
                if not webhook_signature or not webhook_timestamp:
                    logger.error('Missing webhook signature or timestamp')
                    return JsonResponse({'status': 'error', 'message': 'Invalid webhook'})
                
                # Verify signature (implement based on Cashfree documentation)
                # expected_signature = hmac.new(
                #     settings.CASHFREE_SECRET_KEY.encode(),
                #     (webhook_timestamp + raw_body.decode()).encode(),
                #     hashlib.sha256
                # ).hexdigest()
                
                # if not hmac.compare_digest(webhook_signature, expected_signature):
                #     logger.error('Invalid webhook signature')
                #     return JsonResponse({'status': 'error', 'message': 'Invalid signature'})
            
            # Extract payment details from Cashfree webhook
            order_id = data.get('order_id')
            payment_status = data.get('payment_status')
            
            logger.info(f'Cashfree webhook received for order {order_id}: {payment_status}')
            
            if order_id and payment_status == 'SUCCESS':
                # Mark order as paid
                order = get_object_or_404(Order, id=order_id)
                order.paid = True
                order.save()
                
                logger.info(f'Order {order_id} marked as paid successfully')
                return JsonResponse({'status': 'success'})
            else:
                logger.warning(f'Payment not successful for order {order_id}: {payment_status}')
                return JsonResponse({'status': 'failed', 'message': 'Payment not successful'})
                
        except Exception as e:
            logger.error(f"Cashfree webhook error: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'invalid_method'})


def confirmation(request, order_id):
    """Order confirmation page"""
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/confirmation.html', {'order': order})


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
