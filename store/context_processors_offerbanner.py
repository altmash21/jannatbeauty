from coupons.models import Coupon
from .models import OfferBanner
from django.utils import timezone

def offer_banner(request):
    now = timezone.now()
    # Try to get a coupon marked for banner
    coupon = Coupon.objects.filter(
        active=True, 
        show_on_banner=True, 
        valid_from__lte=now, 
        valid_to__gte=now
    ).order_by('-created_at').first()
    
    if coupon:
        return {
            'offer_banner': {'coupon': coupon, 'text': None, 'has_content': True}
        }
    
    # Fallback to OfferBanner - check expiry if set
    banner = OfferBanner.objects.filter(active=True).order_by('-created').first()
    if banner:
        # If expiry is set, check if it's still valid
        if banner.expires_at and banner.expires_at < now:
            banner = None
    
    if banner:
        return {
            'offer_banner': {'coupon': None, 'text': banner.text, 'has_content': True}
        }
    
    # Always return a default banner
    return {
        'offer_banner': {'coupon': None, 'text': 'Welcome to Jannat Library! Enjoy exclusive offers on our products.', 'has_content': True}
    }
