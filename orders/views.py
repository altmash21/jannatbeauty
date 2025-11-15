from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Order, OrderItem
from cart.cart import Cart
from store.models import Product
from .shiprocket import ShiprocketAPI

# Razorpay integration
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import hmac
import hashlib

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


@login_required
def checkout(request):
    if hasattr(request.user, 'profile') and request.user.profile.is_seller:
        messages.error(request, 'Sellers cannot purchase products.')
        return redirect('accounts:seller_dashboard')

    cart = Cart(request)
    if len(cart) == 0:
        messages.error(request, 'Your cart is empty.')
        return redirect('cart:cart_detail')

    # Ensure cart items persist after login
    request.session['cart'] = cart.serialize()

    razorpay_order_id = None
    amount = None
    order_id = None

    if request.method == 'POST':
        # Safely fetch posted form data
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        zipcode = request.POST.get('zipcode', '').strip()

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
                'discount': 0  # Add discount to context
            })

        # Create order
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            first_name=first_name,
            last_name=last_name,
            email=email,
            address=address,
            city=city,
            state=state,
            zipcode=zipcode,
            total_amount=cart.get_total_price()
        )
        order_id = str(order.id)

        # Create order items and update stock
        for item in cart:
            product = item['product']
            quantity = item['quantity']
            if product.stock < quantity:
                messages.error(request, f'Insufficient stock for {product.name}. Only {product.stock} available.')
                return redirect('cart:cart_detail')
            OrderItem.objects.create(
                order=order,
                product=product,
                price=item['price'],
                quantity=quantity
            )
            product.stock -= quantity
            product.save()

        # Check if Razorpay is enabled
        if settings.RAZORPAY_ENABLED:
            # Razorpay order creation
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            amount = int(float(order.total_amount) * 100)  # Razorpay expects paise
            data = {
                "amount": amount,
                "currency": "INR",
                "receipt": order_id,
                "payment_capture": 1
            }
            razorpay_order = client.order.create(data=data)
            razorpay_order_id = razorpay_order['id']

            # Do not clear cart yet; wait for payment verification
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
                'razorpay_order_id': razorpay_order_id,
                'razorpay_key_id': settings.RAZORPAY_KEY_ID,
                'amount': amount,
                'order_id': order_id,
                'discount': 0  # Add discount to context
            })
        else:
            # Payment disabled - mark order as paid and complete
            order.paid = True
            order.save()
            cart.clear()
            messages.success(request, f'Order {order.id} placed successfully!')
            return redirect('orders:confirmation', order_id=order.id)

    # Pre-fill form data for authenticated users (GET request)
    initial_data = {}
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

    subtotal = cart.get_total_price()
    discount = 0  # You can update this logic for real discounts
    cart_total = subtotal - discount
    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'initial_data': initial_data,
        'discount': discount,
        'cart_total': cart_total,
        'subtotal': subtotal
    })

    # --- Confirmation view should be outside checkout ---
    def confirmation(request, order_id):
        order = get_object_or_404(Order, id=order_id)
        return render(request, 'orders/confirmation.html', {'order': order})
        order_id = str(order.id)

        # Create order items and update stock
        for item in cart:
            product = item['product']
            quantity = item['quantity']
            if product.stock < quantity:
                messages.error(request, f'Insufficient stock for {product.name}. Only {product.stock} available.')
                return redirect('cart:cart_detail')
            OrderItem.objects.create(
                order=order,
                product=product,
                price=item['price'],
                quantity=quantity
            )
            product.stock -= quantity
            product.save()

        # Check if Razorpay is enabled
        if settings.RAZORPAY_ENABLED:
            # Razorpay order creation
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            amount = int(float(order.total_amount) * 100)  # Razorpay expects paise
            data = {
                "amount": amount,
                "currency": "INR",
                "receipt": order_id,
                
                "payment_capture": 1
            }
            razorpay_order = client.order.create(data=data)
            razorpay_order_id = razorpay_order['id']

            # Do not clear cart yet; wait for payment verification

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
                'razorpay_order_id': razorpay_order_id,
                'razorpay_key_id': settings.RAZORPAY_KEY_ID,
                'amount': amount,
                'order_id': order_id,
                'discount': 0  # Add discount to context
            })
        else:
            # Payment disabled - mark order as paid and complete
            order.paid = True
            order.save()
            cart.clear()
            messages.success(request, f'Order {order.id} placed successfully!')
            return redirect('orders:confirmation', order_id=order.id)
def confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/confirmation.html', {'order': order})

    # Pre-fill form data for authenticated users
    initial_data = {}
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

    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'initial_data': initial_data,
        'discount': 0  # Add discount to context, default to 0 for now
    })


# Razorpay payment verification view
@csrf_exempt
def razorpay_verify(request):
    if request.method == 'POST':
        payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        signature = request.POST.get('razorpay_signature')
        order_id = request.POST.get('order_id')

        # Verify signature
        generated_signature = hmac.new(
            bytes(settings.RAZORPAY_KEY_SECRET, 'utf-8'),
            bytes(razorpay_order_id + '|' + payment_id, 'utf-8'),
            hashlib.sha256
        ).hexdigest()
        if generated_signature == signature:
            # Mark order as paid
            order = get_object_or_404(Order, id=order_id)
            order.paid = True
            order.save()
            # Clear cart for this session
            cart = Cart(request)
            cart.clear()
            messages.success(request, f'Payment successful! Order {order.id} placed.')
            return redirect('orders:order_detail', order_id=order.id)
        else:
            messages.error(request, 'Payment verification failed. Please contact support.')
            return redirect('orders:checkout')
    return redirect('store:home')

def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Check if user has permission to view this order
    if request.user.is_authenticated and order.user != request.user:
        if not request.user.is_staff:
            messages.error(request, 'You do not have permission to view this order.')
            return redirect('store:home')
    
    return render(request, 'orders/detail.html', {'order': order})


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
    
    # Create Shiprocket order
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
