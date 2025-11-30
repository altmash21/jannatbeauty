"""
Cashfree Payment Gateway Service
Handles API interactions with Cashfree
UPDATED: Better error handling and status verification
"""
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class CashfreeService:
    """Service class for Cashfree payment gateway integration"""
    
    def __init__(self):
        """Initialize Cashfree service with credentials from settings"""
        self.app_id = getattr(settings, 'CASHFREE_APP_ID', '')
        self.secret_key = getattr(settings, 'CASHFREE_SECRET_KEY', '')
        self.env = getattr(settings, 'CASHFREE_ENV', 'TEST')  # TEST or PROD
        
        # Set base URL based on environment
        if self.env == 'PROD':
            self.base_url = 'https://api.cashfree.com'
        else:
            self.base_url = 'https://sandbox.cashfree.com'
        
        # Set headers for API requests
        self.headers = {
            'x-client-id': self.app_id,
            'x-client-secret': self.secret_key,
            'x-api-version': '2023-08-01',
            'Content-Type': 'application/json'
        }
        
        logger.info(f"Cashfree service initialized in {self.env} mode")
    
    def create_order(self, order_data):
        """
        Create order on Cashfree
        
        Args:
            order_data (dict): Order information including:
                - order_id: Unique order identifier
                - order_amount: Amount to be paid
                - order_currency: Currency code (INR)
                - customer_details: Customer information
                - order_meta: Metadata including return_url
        
        Returns:
            dict: Response containing success status and data/error
        """
        url = f"{self.base_url}/pg/orders"
        
        try:
            logger.info(f"Creating Cashfree order: {order_data.get('order_id')}")
            
            response = requests.post(
                url,
                json=order_data,
                headers=self.headers,
                timeout=10
            )
            
            logger.info(f"Cashfree response status: {response.status_code}")
            logger.info(f"Cashfree response body: {response.text}")
            
            if response.status_code in [200, 201]:
                data = response.json()
                return {
                    'success': True,
                    'data': data
                }
            else:
                error_msg = response.text
                logger.error(f"Cashfree order creation failed: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except requests.exceptions.Timeout:
            logger.error("Cashfree API timeout")
            return {
                'success': False,
                'error': 'Request timeout. Please try again.'
            }
        except Exception as e:
            logger.error(f"Exception during order creation: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_payment(self, order_id):
        """
        Verify payment status with Cashfree
        
        Args:
            order_id (str): The order ID to verify
        
        Returns:
            str: Order status (PAID, ACTIVE, FAILED, CANCELLED, USER_DROPPED, EXPIRED, etc.)
        """
        url = f"{self.base_url}/pg/orders/{order_id}"
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=10
            )
            
            logger.info(f"Cashfree verify response status: {response.status_code}")
            logger.info(f"Cashfree verify response body: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                
                # The correct field is 'order_status' not 'payment_status'
                order_status = data.get('order_status', 'UNKNOWN')
                
                # Log payment details if available
                if 'payments' in data and data['payments']:
                    payment_info = data['payments']
                    logger.info(f"Payment details: {payment_info}")
                    
                    # Get the latest payment status
                    if isinstance(payment_info, dict):
                        payment_status = payment_info.get('payment_status')
                        logger.info(f"Payment status from payments object: {payment_status}")
                
                logger.info(f"Order {order_id} status: {order_status}")
                return order_status
            
            elif response.status_code == 404:
                logger.error(f"Order {order_id} not found in Cashfree")
                return 'NOT_FOUND'
            
            else:
                logger.error(f"Cashfree verify failed: {response.status_code} - {response.text}")
                return 'ERROR'
                
        except requests.exceptions.Timeout:
            logger.error(f"Cashfree verify timeout for order {order_id}")
            return 'TIMEOUT'
        
        except Exception as e:
            logger.error(f"Exception during payment verification: {str(e)}", exc_info=True)
            return 'ERROR'
    
    def get_payment_details(self, order_id, cf_payment_id):
        """
        Get detailed payment information
        
        Args:
            order_id (str): Order ID
            cf_payment_id (str): Cashfree payment ID
        
        Returns:
            dict: Payment details or error
        """
        url = f"{self.base_url}/pg/orders/{order_id}/payments/{cf_payment_id}"
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': response.text
                }
                
        except Exception as e:
            logger.error(f"Error fetching payment details: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def refund_payment(self, order_id, refund_amount, refund_id=None, refund_note=None):
        """
        Initiate refund for an order
        
        Args:
            order_id (str): Order ID to refund
            refund_amount (float): Amount to refund
            refund_id (str, optional): Unique refund identifier
            refund_note (str, optional): Note for refund
        
        Returns:
            dict: Refund response
        """
        import uuid
        
        url = f"{self.base_url}/pg/orders/{order_id}/refunds"
        
        refund_data = {
            'refund_amount': float(refund_amount),
            'refund_id': refund_id or f"refund_{uuid.uuid4().hex[:16]}",
            'refund_note': refund_note or 'Refund requested'
        }
        
        try:
            response = requests.post(
                url,
                json=refund_data,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': response.text
                }
                
        except Exception as e:
            logger.error(f"Error initiating refund: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }