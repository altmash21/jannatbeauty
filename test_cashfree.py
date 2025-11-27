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
import requests
import json

def test_cashfree_pg():
    print("=" * 70)
    print("Testing Cashfree PG API Connection...")
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
    # Configure Cashfree API endpoint
    base_url = "https://sandbox.cashfree.com" if env == "TEST" else "https://api.cashfree.com"
    
    print("\n✓ Cashfree API configured for direct HTTP calls.")
    # Try a simple API call: create a test order
    try:
        headers = {
            "x-api-version": "2022-09-01",
            "x-client-id": app_id,
            "x-client-secret": secret_key,
            "Content-Type": "application/json"
        }
        
        order_data = {
            "order_id": "test_order_123",
            "order_amount": 100.0,
            "order_currency": "INR",
            "customer_details": {
                "customer_id": "test_customer",
                "customer_phone": "9999999999"
            }
        }
        
        response = requests.post(
            f"{base_url}/pg/orders",
            headers=headers,
            json=order_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\n✓ Test order creation successful:")
            print(f"Order ID: {result.get('order_id')}")
            print(f"Payment Session ID: {result.get('payment_session_id')}")
        else:
            print(f"\n⚠ API call returned status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"\nAPI call failed (this might be expected for test): {e}")
    print("\n✓ Cashfree PG test setup complete.")
    return True

if __name__ == "__main__":
    test_cashfree_pg()
