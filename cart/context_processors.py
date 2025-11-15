from .cart import Cart


def cart(request):
    cart_obj = Cart(request)
    cart_total = cart_obj.get_total_price()
    
    # Get coupon discount from session
    coupon_discount = request.session.get('coupon_discount', 0)
    
    return {
        'cart': cart_obj,
        'cart_total': cart_total,
        'coupon_discount': coupon_discount,
        'final_total': cart_total - float(coupon_discount) if coupon_discount else cart_total,
    }