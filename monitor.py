import requests
import time
from datetime import datetime
import json
from plyer import notification  # For desktop notifications

def check_stock(url):
    # Headers to mimic a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Extract product ID from URL
        product_id = url.split('/')[-1]
        
        # Best Buy API endpoint for stock checking
        api_url = f'https://www.bestbuy.ca/api/v2/json/product/{product_id}'
        
        response = requests.get(api_url, headers=headers)
        data = response.json()
        
        # Debug logging
        print("\nAPI Response:")
        print(f"Status Code: {response.status_code}")
        print(f"Product Name: {data.get('name')}")
        print(f"Availability Data: {json.dumps(data.get('availability', {}), indent=2)}")
        
        availability = data.get('availability', {})
        
        # More accurate availability checking based on Best Buy's API structure
        is_available = (
            availability.get('isAvailableOnline', False)
            and availability.get('onlineAvailability') == "InStock"
            and availability.get('onlineAvailabilityCount', 0) > 0
            and availability.get('buttonState') == "AddToCart"
        )
        
        return is_available, data.get('name', 'Product')
        
    except Exception as e:
        print(f"Error checking stock: {e}")
        return False, None

def send_notification(product_name):
    notification.notify(
        title='Product In Stock!',
        message=f'{product_name} is now available at Best Buy!',
        app_icon=None,
        timeout=10,
    )

def main():
    # Switch back to original target URL
    url = "https://www.bestbuy.ca/en-ca/product/nvidia-geforce-rtx-5090-32gb-gddr7-video-card/18931348"
    check_interval = 60  # Back to 60 second interval for production use
    
    print("Starting restock monitor...")
    print(f"Monitoring: {url}")
    print(f"Checking every {check_interval} seconds")
    
    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        is_available, product_name = check_stock(url)
        
        if is_available:
            print(f"[{now}] {product_name} IS IN STOCK!")
            send_notification(product_name)
        else:
            print(f"[{now}] Not in stock")
        
        time.sleep(check_interval)

if __name__ == "__main__":
    main() 