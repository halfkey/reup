import os
import json
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from typing import Dict, Tuple, Any
from ..utils.exceptions import APIError, URLParseError
import re
from urllib.error import URLError
from bs4 import BeautifulSoup
import time
import logging
from ..api.bestbuy import BestBuyAPI
from ..config.constants import USER_AGENT
from ..utils.logger import log_security_event

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def parse_url(url: str) -> str:
    """Extract product ID from Best Buy URL."""
    try:
        # Input validation
        if not url or not isinstance(url, str):
            log_security_event("URL_VALIDATION", f"Invalid URL input: {type(url)}", "WARNING")
            raise ValueError("Invalid URL")
            
        # Clean the URL first
        url = url.strip()
        
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            log_security_event("URL_VALIDATION", f"Invalid URL scheme: {url}", "WARNING")
            raise ValueError("Invalid URL scheme")
            
        if 'bestbuy.ca' not in url.lower():
            log_security_event("URL_VALIDATION", f"Not a Best Buy CA URL: {url}", "WARNING")
            raise ValueError("Not a Best Buy Canada URL")
        
        # Try different URL patterns
        patterns = [
            r'/(?:product|produit)/.*?/(\d+)/?$',  # Normal product URL
            r'/(?:product|produit)/(\d+)/?$',      # Short product URL
            r'[/=](\d{8,})/?$',                    # Direct product ID
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                product_id = match.group(1)
                log_security_event("URL_PARSE", f"Successfully extracted product ID: {product_id}")
                return product_id
                
        log_security_event("URL_VALIDATION", f"Could not extract product ID from URL: {url}", "WARNING")
        raise ValueError(f"Could not find product ID in URL: {url}")
        
    except Exception as e:
        log_security_event("URL_ERROR", f"Error parsing URL {url}: {str(e)}", "ERROR")
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

def check_stock(product_id: str) -> tuple[bool, str, dict]:
    """
    Check stock status for a product using HTML parsing only.
    Returns (success, name, result) where:
    - success: bool indicating if check was successful
    - name: str product name
    - result: dict containing stock info {'stock': str, 'price': float, 'status': str}
    """
    try:
        session = create_session()
        
        url = f"https://www.bestbuy.ca/en-ca/product/{product_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html'
        }
        
        response = session.get(url, headers=headers, timeout=(5, 10))
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get product name
        name = soup.find('h1').text.strip() if soup.find('h1') else 'Unknown Product'
        
        # Get price - Best Buy specific price finding
        price = 0.0
        try:
            # Try to find the main price container
            price_container = soup.find('div', class_='price_FHDfG')
            if price_container:
                # Look for the large price text
                price_text = price_container.find('span', {'data-automation': 'product-price'})
                if price_text:
                    price_str = price_text.text.strip().replace('$', '').replace(',', '')
                    price = float(price_str)
                    logger.debug(f"Found price from main price container: ${price}")
            
            # Fallback: Try to find price in meta tags
            if price == 0.0:
                price_meta = soup.find('meta', {'property': 'product:price:amount'})
                if price_meta:
                    price = float(price_meta.get('content', '0.0'))
                    logger.debug(f"Found price from meta tag: ${price}")
        except (ValueError, AttributeError) as e:
            logger.warning(f"Error parsing price: {str(e)}")
            price = 0.0
        
        # Check for definitive out-of-stock indicators
        out_of_stock_indicators = [
            'sold out',
            'coming soon',
            'not available online',
            'check stores'
        ]
        
        # Check for definitive in-stock indicators
        in_stock_indicators = [
            'add to cart',
            'ship it'
        ]
        
        page_text = soup.text.lower()
        
        # Look for the add to cart button specifically
        add_to_cart_btn = soup.find('button', {'data-button-state': 'ADD_TO_CART'})
        add_to_cart_enabled = add_to_cart_btn and not add_to_cart_btn.get('disabled')
        
        # Determine stock status
        is_out_of_stock = any(indicator in page_text for indicator in out_of_stock_indicators)
        is_in_stock = (
            any(indicator in page_text for indicator in in_stock_indicators) or 
            add_to_cart_enabled
        )
        
        # Make final determination
        if is_in_stock and not is_out_of_stock:
            status = 'Available'
            stock = '1'
        else:
            status = 'Out of Stock'
            stock = '0'
            
        # Log findings
        logger.info(f"Stock check for {product_id}:")
        logger.info(f"- Name: {name}")
        logger.info(f"- Price: ${price}")
        logger.info(f"- Add to cart button enabled: {add_to_cart_enabled}")
        logger.info(f"- Out of stock indicators found: {is_out_of_stock}")
        logger.info(f"- In stock indicators found: {is_in_stock}")
        logger.info(f"- Final status: {status}")
        
        result = {
            'price': price,
            'stock': stock,
            'status': status,
            'purchasable': 'Yes' if stock == '1' else 'No'
        }
        
        return True, name, result
        
    except requests.Timeout:
        logger.error(f"Timeout checking product {product_id}")
        return False, None, {"error": "Request timed out"}
    except requests.RequestException as e:
        logger.error(f"Error checking product {product_id}: {str(e)}")
        return False, None, {"error": "Failed to check product"}
    except Exception as e:
        logger.error(f"Unexpected error checking product {product_id}: {str(e)}")
        return False, None, {"error": "Internal error"}
    finally:
        if 'session' in locals():
            session.close()

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