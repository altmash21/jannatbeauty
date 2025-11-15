from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Coupon
from cart.cart import Cart

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
