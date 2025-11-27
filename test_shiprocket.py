"""
Test Shiprocket API Connection
Run this to verify your Shiprocket API credentials are working
"""
import requests

# Your API credentials from settings (NOT your login credentials)
SHIPROCKET_API_EMAIL = 'mylearning2609@gmail.com'
SHIPROCKET_API_PASSWORD = 'mwKvV$w8s4Y0SXFH'
SHIPROCKET_API_URL = 'https://apiv2.shiprocket.in/v1/external'

def test_shiprocket_login():
    """Test Shiprocket authentication with API credentials"""
    print("Testing Shiprocket API Connection...")
    print(f"API Email: {SHIPROCKET_API_EMAIL}")
    print(f"API URL: {SHIPROCKET_API_URL}")
    
    if SHIPROCKET_API_EMAIL == 'YOUR_API_EMAIL':
        print("\n❌ ERROR: Please set your Shiprocket API credentials!")
        print("\nTo get your API credentials:")
        print("1. Log in to https://app.shiprocket.in")
        print("2. Go to Settings → API")
        print("3. Find your API Email and Password (different from login)")
        print("4. Update settings.py with these credentials")
        return False
    
    url = f"{SHIPROCKET_API_URL}/auth/login"
    payload = {
        "email": SHIPROCKET_API_EMAIL,
        "password": SHIPROCKET_API_PASSWORD
    }
    
    try:
        print(f"\nSending request to: {url}")
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('token'):
                print("\n✅ SUCCESS! Shiprocket API authentication successful!")
                print(f"Token received: {data['token'][:50]}...")
                return True
            else:
                print("\n❌ FAILED! No token in response")
                print(f"Response: {response.text}")
                return False
        else:
            print(f"\n❌ FAILED! Status code: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False

if __name__ == '__main__':
    test_shiprocket_login()
