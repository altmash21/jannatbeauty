import requests
from django.conf import settings
from django.core.cache import cache

def get_shiprocket_token():
    """
    Get Shiprocket authentication token. Cache it for 23 hours (tokens expire in 24 hours).
    """
    token = cache.get('shiprocket_token')
    if token:
        print(f"DEBUG: Using cached Shiprocket token: {token[:20]}...")
        return token
    
    print("DEBUG: Getting new Shiprocket token")
    # Authenticate and get new token
    url = "https://apiv2.shiprocket.in/v1/external/auth/login"
    payload = {
        "email": settings.SHIPROCKET_API_EMAIL,
        "password": settings.SHIPROCKET_API_PASSWORD
    }
    print(f"DEBUG: Authenticating with email: {settings.SHIPROCKET_API_EMAIL}")
    
    try:
        response = requests.post(url, json=payload)
        print(f"DEBUG: Auth response status: {response.status_code}")
        
        data = response.json()
        print(f"DEBUG: Auth response data: {data}")
        
        if response.status_code == 200 and 'token' in data:
            token = data['token']
            # Cache token for 23 hours
            cache.set('shiprocket_token', token, 60 * 60 * 23)
            print(f"DEBUG: New token cached: {token[:20]}...")
            return token
        else:
            print(f"DEBUG: Authentication failed: {data}")
    except Exception as e:
        print(f"Shiprocket authentication error: {e}")
    return None

def check_pincode_serviceability(pincode, payment_method):
    """
    Checks Shiprocket serviceability for a given pincode and payment method (prepaid/cod).
    Returns True if serviceable, False otherwise.
    """
    print(f"DEBUG: Checking serviceability for pincode {pincode}, payment_method: {payment_method}")
    
    if not settings.SHIPROCKET_ENABLED:
        print("DEBUG: Shiprocket is disabled, allowing order")
        return True  # Skip check if Shiprocket is disabled
    
    token = get_shiprocket_token()
    if not token:
        print("DEBUG: Could not get Shiprocket token, allowing order")
        return True  # Allow order if can't get token (fail open)
    
    print(f"DEBUG: Got Shiprocket token: {token[:20]}...")
    
    # Shiprocket API endpoint for serviceability
    url = "https://apiv2.shiprocket.in/v1/external/courier/serviceability"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "pickup_postcode": settings.SHIPROCKET_PICKUP_PINCODE,
        "delivery_postcode": str(pincode),
        "cod": 1 if payment_method == "cod" else 0,
        "weight": 0.5,  # Default weight, adjust as needed
        "order_type": "forward"
    }
    
    print(f"DEBUG: Shiprocket API payload: {payload}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"DEBUG: Shiprocket API response status: {response.status_code}")
        
        data = response.json()
        print(f"DEBUG: Shiprocket API response data: {data}")
        
        # Check if response is successful
        if response.status_code == 200:
            # Check if data exists and has available_courier_companies
            if data.get("data") and "available_courier_companies" in data["data"]:
                courier_companies = data["data"]["available_courier_companies"]
                print(f"DEBUG: Available courier companies: {len(courier_companies)}")
                return len(courier_companies) > 0
            else:
                print("DEBUG: No data or courier companies in response")
                return False
        else:
            print(f"DEBUG: API returned error status: {response.status_code}")
            return True  # Fail open on API errors
            
    except Exception as e:
        print(f"Shiprocket serviceability check error: {e}")
        return True  # Fail open - allow order if API fails
