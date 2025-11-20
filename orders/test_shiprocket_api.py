from orders.shiprocket import ShiprocketAPI

if __name__ == "__main__":
    api = ShiprocketAPI()
    print("Testing Shiprocket API credentials...")
    token = api.get_token()
    if token:
        print(f"SUCCESS: Token received: {token}")
    else:
        print("ERROR: Could not authenticate with Shiprocket API. Check credentials and network.")

    # Optionally, test headers
    headers = api.get_headers()
    print(f"Headers: {headers}")
