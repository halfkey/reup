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
from ..config.constants import USER_AGENT
from ..utils.logger import log_security_event

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def parse_url(url: str) -> str:
    """Extract product ID from Best Buy URL."""
    try:
        # Input validation
        if not url or not isinstance(url, str):
            log_security_event(
                "URL_VALIDATION", f"Invalid URL input: {type(url)}", "WARNING"
            )
            raise ValueError("Invalid URL")

        # Clean the URL first
        url = url.strip()

        # Validate URL format
        if not url.startswith(("http://", "https://")):
            log_security_event(
                "URL_VALIDATION", f"Invalid URL scheme: {url}", "WARNING"
            )
            raise ValueError("Invalid URL scheme")

        if "bestbuy.ca" not in url.lower():
            log_security_event(
                "URL_VALIDATION", f"Not a Best Buy CA URL: {url}", "WARNING"
            )
            raise ValueError("Not a Best Buy Canada URL")

        # Try different URL patterns
        patterns = [
            r"/(?:product|produit)/.*?/(\d+)/?$",  # Normal product URL
            r"/(?:product|produit)/(\d+)/?$",  # Short product URL
            r"[/=](\d{8,})/?$",  # Direct product ID
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                product_id = match.group(1)
                log_security_event(
                    "URL_PARSE", f"Successfully extracted product ID: {product_id}"
                )
                return product_id

        log_security_event(
            "URL_VALIDATION", f"Could not extract product ID from URL: {url}", "WARNING"
        )
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
        allowed_methods=["GET"],
    )

    # Add retry strategy to session
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Add security headers
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "DNT": "1",  # Do Not Track
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        }
    )

    return session


def check_stock(product_id: str) -> Tuple[bool, Optional[str], Dict]:
    """Check stock status for a product."""
    try:
        # Make request to Best Buy API
        response = requests.get(f"https://www.bestbuy.ca/en-ca/product/{product_id}")
        response.raise_for_status()

        # Parse response
        data = response.json()
        if not data.get("products"):
            return False, None, {"error": "No product data found"}

        product = data["products"][0]
        name = product.get("name")
        availability = product.get("availability", {})

        return (
            True,
            name,
            {
                "status": availability.get("onlineAvailability"),
                "stock": availability.get("onlineAvailabilityCount"),
            },
        )

    except Exception as e:
        logging.error(f"Error checking product {product_id}: {str(e)}")
        return False, None, {"error": str(e)}


def save_profile(filename: str, profile_data: Dict) -> bool:
    """Save profile data to file."""
    try:
        os.makedirs("profiles", exist_ok=True)
        with open(filename, "w") as f:
            json.dump(profile_data, f, indent=4)
        return True
    except Exception:
        return False


def load_profile(filename: str) -> Dict:
    """Load profile data from file."""
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except Exception:
        return None


def get_timestamp() -> str:
    """Get current timestamp in standard format."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
