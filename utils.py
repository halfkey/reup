import os
import json
from datetime import datetime
import requests
from typing import Dict, Tuple, Any

def check_stock(url: str, headers: Dict[str, str]) -> Tuple[bool, str, Dict[str, Any]]:
    """Check stock status for a given product URL."""
    try:
        product_id = url.split('/')[-1]
        api_url = f'https://www.bestbuy.ca/api/v2/json/product/{product_id}'
        
        response = requests.get(api_url, headers=headers)
        if response.status_code != 200:
            return False, None, None
            
        data = response.json()
        availability = data.get('availability', {})
        product_name = data.get('name', 'Product')
        stock_count = availability.get('onlineAvailabilityCount', 0)
        
        is_available = (
            availability.get('isAvailableOnline', False)
            and availability.get('onlineAvailability') == "InStock"
            and stock_count > 0
            and availability.get('buttonState') == "AddToCart"
        )
        
        status_details = {
            'name': product_name,
            'stock': stock_count,
            'status': availability.get('onlineAvailability', 'Unknown'),
            'purchasable': 'Yes' if availability.get('buttonState') == "AddToCart" else 'No'
        }
        
        return is_available, product_name, status_details
        
    except Exception as e:
        print(f"Error checking stock: {e}")
        return False, None, None

def save_profile(filename: str, profile_data: Dict) -> bool:
    """Save profile data to file."""
    try:
        os.makedirs('profiles', exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(profile_data, f, indent=4)
        return True
    except Exception:
        return False

def load_profile(filename: str) -> Dict:
    """Load profile data from file."""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception:
        return None

def get_timestamp() -> str:
    """Get current timestamp in standard format."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S") 