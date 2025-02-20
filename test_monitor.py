import requests
import json
from datetime import datetime

def check_stock(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        product_id = url.split('/')[-1]
        api_url = f'https://www.bestbuy.ca/api/v2/json/product/{product_id}'
        
        response = requests.get(api_url, headers=headers)
        data = response.json()
        
        availability = data.get('availability', {})
        
        # Individual checks for better debugging
        checks = {
            'online_available': availability.get('isAvailableOnline', False),
            'online_status': availability.get('onlineAvailability') == "InStock",
            'has_stock': availability.get('onlineAvailabilityCount', 0) > 0,
            'can_add_to_cart': availability.get('buttonState') == "AddToCart"
        }
        
        # Overall availability check
        is_available = all(checks.values())
        
        return {
            'name': data.get('name', 'Product'),
            'is_available': is_available,
            'checks': checks,
            'raw_availability': availability
        }
        
    except Exception as e:
        return {
            'name': 'Error',
            'is_available': False,
            'error': str(e)
        }

def test_urls():
    urls = {
        'target_product': "https://www.bestbuy.ca/en-ca/product/nvidia-geforce-rtx-5090-32gb-gddr7-video-card/18931348",
        'known_instock': "https://www.bestbuy.ca/en-ca/product/asus-dual-nvidia-geforce-rtx-4060-v2-8gb-gddr6-video-card/18658505"
    }
    
    print(f"Testing URLs at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    for label, url in urls.items():
        print(f"\nTesting {label}: {url}")
        print("-" * 80)
        
        result = check_stock(url)
        
        print(f"Product Name: {result.get('name')}")
        print(f"Is Available: {result.get('is_available')}")
        
        if 'checks' in result:
            print("\nIndividual Checks:")
            for check, value in result['checks'].items():
                print(f"  {check}: {value}")
            
            print("\nRaw Availability Data:")
            print(json.dumps(result['raw_availability'], indent=2))
        
        if 'error' in result:
            print(f"\nError occurred: {result['error']}")
        
        print("-" * 80)

if __name__ == "__main__":
    test_urls() 