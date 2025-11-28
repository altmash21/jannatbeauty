"""
Cashfree Payment Gateway Service
Handles all Cashfree payment operations following official documentation
"""
import logging
import requests
from django.conf import settings
from decimal import Decimal

logger = logging.getLogger(__name__)


class CashfreeService:
    """Service class for Cashfree Payment Gateway integration"""
    
    def __init__(self):
        self.app_id = getattr(settings, 'CASHFREE_APP_ID', '')
        self.secret_key = getattr(settings, 'CASHFREE_SECRET_KEY', '')
        self.env = getattr(settings, 'CASHFREE_ENV', 'TEST')
        
        # Set base URL based on environment
        if self.env == 'PROD':  # Changed from 'PRODUCTION' to 'PROD' for consistency
            self.base_url = 'https://api.cashfree.com/pg'
        else:
            self.base_url = 'https://sandbox.cashfree.com/pg'
    
    def get_headers(self):
        """Get standard headers for Cashfree API requests"""
        return {
            'x-api-version': '2023-08-01',
            'x-client-id': self.app_id,
            'x-client-secret': self.secret_key,
            'Content-Type': 'application/json'
        }
    
    def create_order(self, order_data):
        """
        Create a Cashfree order
        
        Args:
            order_data (dict): Order details including amount, customer info, etc.
            
        Returns:
            dict: Response containing payment_session_id and order details
        """
        url = f"{self.base_url}/orders"
        
        try:
            logger.info(f"Creating Cashfree order: {order_data.get('order_id')}")
            
            response = requests.post(
                url,
                headers=self.get_headers(),
                json=order_data,
                timeout=30
            )
            
            logger.info(f"Cashfree API response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Order created successfully: {result.get('cf_order_id')}")
                return {
                    'success': True,
                    'data': result
                }
            else:
                logger.error(f"Cashfree API error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': response.text
                }
                
        except requests.exceptions.Timeout:
            logger.error("Cashfree API timeout")
            return {
                'success': False,
                'error': 'Payment gateway timeout'
            }
        except Exception as e:
            logger.error(f"Error creating Cashfree order: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def fetch_order(self, order_id):
        """
        Fetch order details from Cashfree
        
        Args:
            order_id (str): Cashfree order ID
            
        Returns:
            dict: Order details including payment status
        """
        url = f"{self.base_url}/orders/{order_id}"
        
        try:
            logger.info(f"Fetching order status for: {order_id}")
            
            response = requests.get(
                url,
                headers=self.get_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Order fetched: {order_id}, status: {data.get('order_status')}")
                return {
                    'success': True,
                    'data': data
                }
            else:
                logger.error(f"Failed to fetch order: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': response.text
                }
                
        except Exception as e:
            logger.error(f"Error fetching order: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_payment(self, order_id):
        """
        Verify payment status - wrapper around fetch_order
        
        Args:
            order_id (str): Cashfree order ID
            
        Returns:
            str: Payment status (PAID, ACTIVE, PENDING, etc.)
        """
        result = self.fetch_order(order_id)
        
        if result['success']:
            order_data = result['data']
            order_status = order_data.get('order_status', 'UNKNOWN')
            logger.info(f"Payment verification for {order_id}: {order_status}")
            return order_status
        else:
            logger.error(f"Payment verification failed for {order_id}")
            return 'FAILED'
