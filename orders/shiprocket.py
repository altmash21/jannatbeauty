"""
Shiprocket API Integration
"""
import requests
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class ShiprocketAPI:
    """Shiprocket API client for shipping operations"""
    
    def __init__(self):
        self.api_url = settings.SHIPROCKET_API_URL
        self.email = settings.SHIPROCKET_API_EMAIL
        self.password = settings.SHIPROCKET_API_PASSWORD
    
    def get_token(self):
        """Get authentication token from Shiprocket using API credentials"""
        # Check cache first
        cached_token = cache.get('shiprocket_token')
        if cached_token:
            return cached_token
        
        url = f"{self.api_url}/auth/login"
        payload = {
            "email": self.email,
            "password": self.password
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            token = data.get('token')
            
            if token:
                # Cache token for 10 days (Shiprocket tokens expire in 10 days)
                cache.set('shiprocket_token', token, timeout=60*60*24*10)
                return token
            else:
                logger.error(f"Shiprocket authentication failed: No token in response")
                return None
        except Exception as e:
            logger.error(f"Shiprocket authentication failed: {str(e)}")
            return None
    
    def get_headers(self):
        """Get headers with authentication token"""
        token = self.get_token()
        if not token:
            return None
        
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
    
    def create_order(self, order):
        """
        Create order in Shiprocket
        
        Args:
            order: Django Order object
        
        Returns:
            dict: Shiprocket order response
        """
        headers = self.get_headers()
        if not headers:
            return {'success': False, 'error': 'Authentication failed'}
        
        # Prepare order items
        order_items = []
        for item in order.items.all():
            order_items.append({
                "name": item.product.name,
                "sku": str(item.product.id),
                "units": item.quantity,
                "selling_price": float(item.price),
                "discount": 0,
                "tax": 0,
                "hsn": ""
            })
        
        # Prepare order payload
        payload = {
            "order_id": str(order.id),
            "order_date": order.created.strftime('%Y-%m-%d %H:%M'),
            "pickup_location": "Primary",  # You can configure this
            "channel_id": "",
            "comment": "E-commerce order",
            "billing_customer_name": order.full_name,
            "billing_last_name": order.last_name or "",
            "billing_address": order.address,
            "billing_address_2": "",
            "billing_city": order.city,
            "billing_pincode": order.zipcode,
            "billing_state": order.state,
            "billing_country": "India",
            "billing_email": order.email,
            "billing_phone": order.user.profile.phone if order.user and hasattr(order.user, 'profile') else "",
            "shipping_is_billing": True,
            "shipping_customer_name": "",
            "shipping_last_name": "",
            "shipping_address": "",
            "shipping_address_2": "",
            "shipping_city": "",
            "shipping_pincode": "",
            "shipping_country": "",
            "shipping_state": "",
            "shipping_email": "",
            "shipping_phone": "",
            "order_items": order_items,
            "payment_method": "COD" if order.payment_method == 'cod' else "Prepaid",
            "shipping_charges": 0,
            "giftwrap_charges": 0,
            "transaction_charges": 0,
            "total_discount": 0,
            "sub_total": float(order.total_amount),
            "length": 10,
            "breadth": 10,
            "height": 10,
            "weight": 0.5
        }
        
        url = f"{self.api_url}/orders/create/adhoc"
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Shiprocket order creation failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def generate_awb(self, shiprocket_order_id, courier_id):
        """Generate AWB (Air Waybill) for shipment"""
        headers = self.get_headers()
        if not headers:
            return {'success': False, 'error': 'Authentication failed'}
        
        payload = {
            "shipment_id": shiprocket_order_id,
            "courier_id": courier_id
        }
        
        url = f"{self.api_url}/courier/assign/awb"
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"AWB generation failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_courier_serviceability(self, pickup_pincode, delivery_pincode, weight=0.5, cod=0):
        """Check courier serviceability and get available couriers"""
        headers = self.get_headers()
        if not headers:
            return {'success': False, 'error': 'Authentication failed'}
        
        url = f"{self.api_url}/courier/serviceability/"
        params = {
            'pickup_postcode': pickup_pincode,
            'delivery_postcode': delivery_pincode,
            'weight': weight,
            'cod': cod
        }
        
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Serviceability check failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def track_shipment(self, awb_code):
        """Track shipment by AWB code"""
        headers = self.get_headers()
        if not headers:
            return {'success': False, 'error': 'Authentication failed'}
        
        url = f"{self.api_url}/courier/track/awb/{awb_code}"
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Shipment tracking failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def cancel_shipment(self, awb_codes):
        """Cancel shipment"""
        headers = self.get_headers()
        if not headers:
            return {'success': False, 'error': 'Authentication failed'}
        
        payload = {
            "awbs": awb_codes if isinstance(awb_codes, list) else [awb_codes]
        }
        
        url = f"{self.api_url}/orders/cancel/shipment/awbs"
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Shipment cancellation failed: {str(e)}")
            return {'success': False, 'error': str(e)}
