import requests
import json
import time
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

_shiprocket_token = None
_shiprocket_token_expiry = 0

# --- Shiprocket token caching ---
def get_shiprocket_token():
    from django.conf import settings
    global _shiprocket_token, _shiprocket_token_expiry
    now = time.time()
    if _shiprocket_token and now < _shiprocket_token_expiry:
        return _shiprocket_token
    # Login to Shiprocket API
    email = getattr(settings, 'SHIPROCKET_API_EMAIL', None)
    password = getattr(settings, 'SHIPROCKET_API_PASSWORD', None)
    if not email or not password:
        return None
    login_url = 'https://apiv2.shiprocket.in/v1/external/auth/login'
    resp = requests.post(login_url, json={'email': email, 'password': password})
    if resp.status_code == 200 and resp.json().get('token'):
        _shiprocket_token = resp.json()['token']
        # Shiprocket tokens are valid for 24 hours, but we'll refresh every 23 hours
        _shiprocket_token_expiry = now + 23*3600
        return _shiprocket_token
    return None

@csrf_exempt
def check_pincode(request):
    if request.method == 'POST':
        from django.conf import settings
        data = json.loads(request.body)
        pincode = data.get('pincode')
        pickup_pincode = getattr(settings, 'SHIPROCKET_PICKUP_PINCODE', None)
        if not pickup_pincode:
            return JsonResponse({'message': 'Shiprocket pickup pincode not configured.'})
        token = get_shiprocket_token()
        if not token:
            return JsonResponse({'message': 'Could not authenticate with Shiprocket.'})
        url = f'https://apiv2.shiprocket.in/v1/external/courier/serviceability/'
        params = {
            'pickup_postcode': pickup_pincode,
            'delivery_postcode': pincode,
            'cod': 0,
            'weight': 0.5,  # in kg, adjust as needed
        }
        headers = {'Authorization': f'Bearer {token}'}
        r = requests.get(url, params=params, headers=headers)
        if r.status_code == 200:
            resp = r.json()
            if resp.get('status') == 200 and resp.get('data', {}).get('available_courier_companies'):
                return JsonResponse({'message': 'Delivery available!'})
            else:
                return JsonResponse({'message': 'Delivery not available to this pincode.'})
        else:
            return JsonResponse({'message': 'Error checking pincode.'})