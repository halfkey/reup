from typing import Dict, Tuple, Optional
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import json
import re
from ..utils.exceptions import APIError
from time import time
import time
from ..utils.logger import log_security_event


class BestBuyAPI:
    """API interface for BestBuy store."""

    BASE_URL = "https://www.bestbuy.ca"
    PRODUCT_URL = f"{BASE_URL}/en-ca/product"
    RATE_LIMIT = 1.0  # Minimum seconds between requests

    def __init__(self):
        self.session = self._create_session()
        self.last_request_time = 0
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[408, 429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _respect_rate_limit(self):
        """Ensure minimum time between requests."""
        current_time = time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.RATE_LIMIT:
            sleep_time = self.RATE_LIMIT - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time()

    def _validate_product_id(self, product_id: str) -> bool:
        """Validate product ID format."""
        if not product_id or not isinstance(product_id, str):
            raise APIError(400, "Invalid product ID")

        # Best Buy product IDs are typically 7-10 digits
        if not re.match(r"^\d{7,10}$", product_id):
            raise APIError(400, "Invalid product ID format")

        return True

    def check_stock(self, product_id: str) -> Tuple[bool, str, Dict]:
        """Check stock status for a BestBuy product."""
        try:
            self._validate_product_id(product_id)
            self._respect_rate_limit()

            url = f"{self.PRODUCT_URL}/{product_id}"

            # Log the request attempt
            log_security_event(
                "API_REQUEST", f"Checking stock for product {product_id}"
            )

            response = self.session.get(url, headers=self.headers, timeout=20)
            response.raise_for_status()

            return self._parse_product_page(response.text, product_id)

        except requests.Timeout:
            log_security_event(
                "API_ERROR", f"Timeout checking product {product_id}", "WARNING"
            )
            raise APIError(408, "Request timed out - retrying...")
        except requests.RequestException as e:
            log_security_event(
                "API_ERROR",
                f"Request failed for product {product_id}: {str(e)}",
                "ERROR",
            )
            raise APIError(getattr(e.response, "status_code", 500), str(e))
        except Exception as e:
            log_security_event(
                "API_ERROR",
                f"Unexpected error for product {product_id}: {str(e)}",
                "ERROR",
            )
            raise APIError(500, f"Failed to check stock: {str(e)}")

    def _parse_product_page(self, html: str, product_id: str) -> Tuple[bool, str, Dict]:
        """Parse BestBuy product page HTML."""
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Get product name from title tag
            title_tag = soup.find("title")
            if title_tag:
                page_title = title_tag.text.replace(" | Best Buy Canada", "").strip()
            else:
                page_title = None

            # Get product data from script tag
            product_data = {}
            scripts = soup.find_all("script")  # Try all script tags
            for script in scripts:
                if not script.string:
                    continue
                try:
                    if "window.__INITIAL_STATE__" in script.string:
                        # Extract the JSON data
                        json_str = (
                            script.string.split("window.__INITIAL_STATE__ = ")[1].split(
                                "};"
                            )[0]
                            + "}"
                        )
                        data = json.loads(json_str)
                        if isinstance(data, dict):
                            product_data = data
                            break
                except (json.JSONDecodeError, IndexError):
                    continue

            # Try to find price in HTML
            price = "N/A"
            price_element = soup.find("span", {"class": "price_FHDfG large_3aP7Z"})
            if price_element:
                price_text = price_element.text.strip()
                # Remove currency symbol and convert to number
                try:
                    price = float(price_text.replace("$", "").replace(",", "").strip())
                    price = f"{price:.2f}"
                except ValueError:
                    pass

            # Get availability info
            availability = None
            if product_data and "availability" in product_data:
                availability = product_data["availability"]

            # Determine stock status - simplified to just In Stock or Out of Stock
            status = "Out of Stock"  # Default status
            stock = 0
            purchasable = "No"

            if availability:
                # Check both shipping and pickup availability
                shipping = availability.get("shipping", {})
                pickup = availability.get("pickup", {})

                # If either shipping or pickup is available, item is in stock
                if (shipping and shipping.get("status", "").lower() == "available") or (
                    pickup and pickup.get("status", "").lower() == "available"
                ):
                    status = "In Stock"
                    purchasable = "Yes"
                    stock = 1

            # Get product name
            name = (
                page_title
                or product_data.get("product", {}).get("name")
                or "Unknown Product"
            )

            return (
                True,
                name,
                {
                    "name": name,
                    "status": status,
                    "stock": stock,
                    "purchasable": purchasable,
                    "price": price,
                    "currency": "CAD",
                    "url": f"{self.PRODUCT_URL}/{product_id}",
                },
            )

        except Exception as e:
            raise APIError(500, f"Failed to parse product page: {str(e)}")

    def _extract_title_from_meta(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product title from meta tags."""
        # Try meta title
        meta_title = soup.find("meta", {"property": "og:title"})
        if meta_title:
            title = meta_title.get("content", "").replace(" | Best Buy Canada", "")
            if title:
                return title

        # Try meta description
        meta_desc = soup.find("meta", {"name": "description"})
        if meta_desc:
            desc = meta_desc.get("content", "")
            if desc:
                # Often the product name is at the start of the description
                return desc.split(" - ")[0]

        return None

    def __del__(self):
        """Cleanup session on deletion."""
        try:
            self.session.close()
        except:
            pass
