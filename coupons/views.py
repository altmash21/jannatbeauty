from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Coupon
from cart.cart import Cart
import random
import string
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
import json

# Import Lead model
try:
    from store.models import Lead
except ImportError:
    Lead = None

@login_required
def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('coupon_code', '').strip().upper()
        
        if not code:
            messages.error(request, 'Please enter a coupon code.')
            return redirect('cart:cart_detail')
        
        try:
            coupon = Coupon.objects.get(code=code)
            
            if not coupon.is_valid():
                messages.error(request, 'This coupon is invalid or has expired.')
                return redirect('cart:cart_detail')
            
            cart = Cart(request)
            cart_total = cart.get_total_price()
            
            if cart_total < coupon.min_purchase_amount:
                messages.error(request, f'Minimum purchase amount of ₹{coupon.min_purchase_amount} required for this coupon.')
                return redirect('cart:cart_detail')
            
            discount = coupon.calculate_discount(cart_total)
            
            # Store coupon in session
            request.session['coupon_id'] = coupon.id
            request.session['coupon_code'] = coupon.code
            request.session['coupon_discount'] = float(discount)
            
            messages.success(request, f'Coupon "{coupon.code}" applied! You saved ₹{discount:.2f}')
            
        except Coupon.DoesNotExist:
            messages.error(request, 'Invalid coupon code.')
        
        return redirect('cart:cart_detail')
    
    return redirect('cart:cart_detail')

@login_required
def remove_coupon(request):
    if 'coupon_id' in request.session:
        del request.session['coupon_id']
        del request.session['coupon_code']
        del request.session['coupon_discount']
        messages.success(request, 'Coupon removed.')
    
    return redirect('cart:cart_detail')

@csrf_exempt
def get_discount_popup(request):
    """Handle discount popup form submission"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            phone = data.get('phone', '').strip()
            
            if not name or not phone:
                return JsonResponse({
                    'success': False, 
                    'message': 'Please provide both name and phone number.'
                })
            
            # Validate phone number (10 digits)
            if not phone.isdigit() or len(phone) != 10:
                return JsonResponse({
                    'success': False,
                    'message': 'Please provide a valid 10-digit phone number.'
                })
            
            # Use a single shared coupon code for all visitors
            # Check if the shared coupon already exists
            shared_coupon_code = "WELCOME10"
            coupon = None
            
            try:
                # Try to get existing shared coupon
                coupon = Coupon.objects.get(code=shared_coupon_code, active=True)
                # Check if it's still valid
                if not coupon.is_valid():
                    # If expired, create a new one with same code (after deactivating old one)
                    coupon.active = False
                    coupon.save()
                    coupon = None
            except Coupon.DoesNotExist:
                pass  # Coupon doesn't exist, create new one
            
            # Create new shared coupon if it doesn't exist or is expired
            if not coupon:
                # Set coupon validity (30 days from now)
                now = timezone.now()
                valid_from = now
                valid_to = now + timedelta(days=30)
                
                # Create the shared coupon
                coupon = Coupon.objects.create(
                    code=shared_coupon_code,
                    discount_type='percentage',
                    discount_value=10,  # 10% discount
                    min_purchase_amount=100,  # Minimum ₹100 purchase
                    usage_limit=None,  # Unlimited uses (shared coupon)
                    valid_from=valid_from,
                    valid_to=valid_to,
                    active=True,
                )
            
            code = coupon.code
            
            # Save lead information
            email_sent = False
            if Lead:
                lead = Lead.objects.create(
                    name=name,
                    mobile=phone,
                    coupon_code=code,
                    email_sent=False
                )
                
                # Send email to admin
                try:
                    # Get admin email - try ADMIN_EMAIL setting first, then ADMINS setting, then DEFAULT_FROM_EMAIL
                    admin_email = getattr(settings, 'ADMIN_EMAIL', None)
                    if not admin_email:
                        # Try ADMINS setting (list of tuples: [('Name', 'email@example.com'), ...])
                        admins = getattr(settings, 'ADMINS', [])
                        if admins:
                            admin_email = admins[0][1]  # Get email from first admin tuple
                        else:
                            admin_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'admin@jannatlibrary.com')
                    
                    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@jannatlibrary.com')
                    
                    subject = f'New Discount Popup Lead - {name}'
                    message = f'''A new visitor has claimed a 10% discount coupon!

Name: {name}
Phone: {phone}
Coupon Code: {code}
Valid Until: {valid_to.strftime('%Y-%m-%d %H:%M:%S')}
Minimum Purchase: ₹100

This coupon gives 10% discount on orders above ₹100.

View all leads in admin panel:
{request.build_absolute_uri('/admin/store/lead/')}

Best regards,
Jannat Library System
'''
                    
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=from_email,
                        recipient_list=[admin_email],
                        fail_silently=False,
                    )
                    
                    email_sent = True
                    # Update lead email_sent status
                    lead.email_sent = True
                    lead.save(update_fields=['email_sent'])
                    
                except Exception as email_error:
                    # Log error but don't fail the request
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f'Failed to send admin email for lead {name}: {str(email_error)}')
            
            return JsonResponse({
                'success': True,
                'coupon_code': coupon.code,
                'message': f'Congratulations {name}! Your 10% discount coupon: {coupon.code} is ready. Use it at checkout!'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid data format.'
            })
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error in get_discount_popup: {str(e)}')
            return JsonResponse({
                'success': False,
                'message': f'Something went wrong. Please try again. Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})
