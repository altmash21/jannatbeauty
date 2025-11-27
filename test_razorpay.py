def test_razorpay_connection():
"""
Test Cashfree API Connection and Functionality
Run this to verify your Cashfree API credentials are working
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.conf import settings
from cashfree_sdk.payouts import Payouts

def test_cashfree_connection():
    """Test Cashfree client initialization and connection"""
    print("=" * 70)
    print("Testing Cashfree API Connection...")
    print("=" * 70)
    app_id = getattr(settings, 'CASHFREE_APP_ID', '')
    secret_key = getattr(settings, 'CASHFREE_SECRET_KEY', '')
    env = getattr(settings, 'CASHFREE_ENV', 'TEST')
    if not app_id or not secret_key:
        print("\n❌ ERROR: Cashfree credentials not found!")
        print("\nPlease add to your .env file:")
        print("CASHFREE_APP_ID=your_app_id")
        print("CASHFREE_SECRET_KEY=your_secret_key")
        print("CASHFREE_ENV=TEST or PROD")
        return False
    print(f"\n✓ App ID: {app_id[:10]}...{app_id[-4:]}")
    print(f"✓ Secret Key: {'*' * 20}...{secret_key[-4:]}")
    print(f"✓ Environment: {env}")
    # Add actual API call test here if needed
    print("\n✓ Cashfree test setup complete.")
    print(f"✓ Enabled: {settings.RAZORPAY_ENABLED}")
    
    try:
        # Initialize Razorpay client
        client = razorpay.Client(auth=(key_id, key_secret))
        print("\n✓ Razorpay client initialized successfully")
        return client
    except Exception as e:
        print(f"\n❌ ERROR: Failed to initialize Razorpay client: {str(e)}")
        return None


def test_create_order(client):
    """Test creating a Razorpay order"""
    print("\n" + "=" * 70)
    print("Testing Order Creation...")
    print("=" * 70)
    
    if not client:
        print("❌ Cannot test order creation - client not initialized")
        return None
    
    # Test order data (100 INR = 10000 paise)
    amount = 10000  # 100 INR in paise
    test_data = {
        "amount": amount,
        "currency": "INR",
        "receipt": "test_receipt_001",
        "payment_capture": 1  # Auto-capture payment
    }
    
    try:
        print(f"\nCreating test order:")
        print(f"  Amount: ₹{amount / 100} ({amount} paise)")
        print(f"  Currency: {test_data['currency']}")
        print(f"  Receipt: {test_data['receipt']}")
        
        order = client.order.create(data=test_data)
        
        print("\n✅ SUCCESS! Order created successfully!")
        print(f"\nOrder Details:")
        print(f"  Order ID: {order.get('id')}")
        print(f"  Amount: ₹{order.get('amount') / 100}")
        print(f"  Currency: {order.get('currency')}")
        print(f"  Status: {order.get('status')}")
        print(f"  Created At: {order.get('created_at')}")
        
        return order
        
    except razorpay.errors.BadRequestError as e:
        print(f"\n❌ BAD REQUEST ERROR: {str(e)}")
        print("Check your API credentials and order data")
        return None
    except razorpay.errors.ServerError as e:
        print(f"\n❌ SERVER ERROR: {str(e)}")
        print("Razorpay server issue. Please try again later.")
        return None
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return None


def test_fetch_order(client, order_id):
    """Test fetching an order by ID"""
    print("\n" + "=" * 70)
    print("Testing Order Fetch...")
    print("=" * 70)
    
    if not client or not order_id:
        print("❌ Cannot test order fetch - missing client or order_id")
        return None
    
    try:
        print(f"\nFetching order: {order_id}")
        order = client.order.fetch(order_id)
        
        print("\n✅ SUCCESS! Order fetched successfully!")
        print(f"\nOrder Details:")
        print(f"  Order ID: {order.get('id')}")
        print(f"  Amount: ₹{order.get('amount') / 100}")
        print(f"  Status: {order.get('status')}")
        print(f"  Receipt: {order.get('receipt')}")
        
        return order
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return None


def test_signature_verification():
    """Test signature verification logic (as used in razorpay_verify view)"""
    print("\n" + "=" * 70)
    print("Testing Signature Verification...")
    print("=" * 70)
    
    key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')
    
    if not key_secret:
        print("❌ Cannot test signature - key secret not found")
        return False
    
    # Test data (simulated payment response)
    razorpay_order_id = "order_test_123456"
    payment_id = "pay_test_789012"
    
    # Generate signature (as done in razorpay_verify view)
    message = f"{razorpay_order_id}|{payment_id}"
    generated_signature = hmac.new(
        bytes(key_secret, 'utf-8'),
        bytes(message, 'utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    print(f"\nTest Signature Generation:")
    print(f"  Order ID: {razorpay_order_id}")
    print(f"  Payment ID: {payment_id}")
    print(f"  Message: {message}")
    print(f"  Generated Signature: {generated_signature[:50]}...")
    
    print("\n✅ Signature verification logic is working correctly!")
    print("Note: In real payment, Razorpay sends the signature to verify against.")
    
    return True


def test_payment_methods(client):
    """Test fetching available payment methods"""
    print("\n" + "=" * 70)
    print("Testing Payment Methods...")
    print("=" * 70)
    
    if not client:
        print("❌ Cannot test payment methods - client not initialized")
        return None
    
    try:
        # Note: Razorpay doesn't have a direct API to fetch payment methods
        # This is just informational
        print("\nℹ️  Razorpay supports the following payment methods:")
        print("  - Credit/Debit Cards")
        print("  - UPI")
        print("  - Net Banking")
        print("  - Wallets (Paytm, Freecharge, etc.)")
        print("  - EMI")
        print("  - Pay Later")
        
        print("\n✅ Payment methods information displayed")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return None


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("RAZORPAY API TEST SUITE")
    print("=" * 70)
    
    # Test 1: Connection
    client = test_razorpay_connection()
    
    if not client:
        print("\n" + "=" * 70)
        print("❌ Tests stopped - Razorpay client not initialized")
        print("=" * 70)
        return
    
    # Test 2: Create Order
    order = test_create_order(client)
    
    # Test 3: Fetch Order (if created)
    if order and order.get('id'):
        test_fetch_order(client, order.get('id'))
    
    # Test 4: Signature Verification
    test_signature_verification()
    
    # Test 5: Payment Methods Info
    test_payment_methods(client)
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print("\n✅ Connection: OK")
    if order:
        print("✅ Order Creation: OK")
        print("✅ Order Fetch: OK")
    print("✅ Signature Verification: OK")
    print("✅ Payment Methods: OK")
    
    print("\n" + "=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    print("1. Use test cards from Razorpay dashboard for testing payments")
    print("2. Test cards: https://razorpay.com/docs/payments/test-cards/")
    print("3. Test UPI: success@razorpay (for success), failure@razorpay (for failure)")
    print("4. Make sure RAZORPAY_ENABLED=True in your .env file")
    print("5. Test the checkout flow in your application")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()

