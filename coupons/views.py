from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Coupon
from cart.cart import Cart
import random
import string
from django.views.decorators.csrf import csrf_exempt
import json

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
            
            # Check if phone already used (optional - remove if you want to allow multiple uses)
            existing_coupon = Coupon.objects.filter(
                code__icontains=phone[-4:],  # Check last 4 digits of phone
                active=True
            ).first()
            
            if existing_coupon:
                return JsonResponse({
                    'success': True,
                    'coupon_code': existing_coupon.code,
                    'message': f'Welcome back {name}! Use your existing coupon code.'
                })
            
            # Generate unique coupon code
            code = f"WELCOME{phone[-4:]}{''.join(random.choices(string.ascii_uppercase, k=2))}"
            
            # Create coupon
            coupon = Coupon.objects.create(
                code=code,
                discount_type='percentage',
                discount=10,
                min_purchase_amount=100,  # Minimum ₹100 purchase
                usage_limit=1,
                active=True,
            )
            
            return JsonResponse({
                'success': True,
                'coupon_code': coupon.code,
                'message': f'Congratulations {name}! You got 10% off coupon: {coupon.code}'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid data format.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Something went wrong. Please try again.'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})
