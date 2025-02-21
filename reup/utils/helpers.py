import os
import json
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from typing import Dict, Tuple, Any, Optional
from ..utils.exceptions import APIError, URLParseError
import re
from urllib.error import URLError
from bs4 import BeautifulSoup
import time
import logging
from ..api.bestbuy import BestBuyAPI
from ..config.constants import USER_AGENT, API_URL
from ..utils.logger import log_security_event
from urllib.parse import urlparse

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def parse_url(url: str) -> str:
    """Extract product ID from Best Buy URL.
    
    Args:
        url: The Best Buy product URL
        
    Returns:
        str: The extracted product ID
        
    Raises:
        URLParseError: If URL is invalid or product ID cannot be extracted
    """
    try:
        parsed = urlparse(url)
        if not parsed.scheme:
            raise URLParseError("Could not extract product ID: Invalid URL scheme")
            
        # Extract product ID from path
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) < 3 or path_parts[-2] != 'product':
            raise URLParseError("Could not extract product ID: No product ID found")
            
        product_id = path_parts[-1]
        if not product_id:
            raise URLParseError("Could not extract product ID: No product ID found")
            
        log_security_event("URL_PARSE", f"Successfully extracted product ID: {product_id}")
        return product_id
        
    except URLParseError:
        raise
    except Exception as e:
        log_security_event("URL_ERROR", f"Error parsing URL {url}: {str(e)}")
        raise URLParseError(f"Could not extract product ID: {str(e)}")

def create_session() -> requests.Session:
    """Create a requests session with retry logic and security headers."""
    session = requests.Session()
    
    # Configure retry strategy
    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[408, 429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    
    # Add retry strategy to session
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    # Add security headers
    session.headers.update({
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'DNT': '1',  # Do Not Track
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1'
    })
    
    return session

def check_stock(product_id: str, headers: Optional[Dict] = None) -> Tuple[bool, str, Dict]:
    """Check stock status for a product."""
    try:
        url = f"{API_URL}/{product_id}/availability"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        return True, data['name'], {
            'status': data['availability']['onlineAvailability'],
            'stock': data['availability'].get('onlineAvailabilityCount', 0)
        }
    except requests.exceptions.RequestException as e:
        logging.error(f"Error checking product {product_id}: {str(e)}")
        raise APIError(str(e))

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