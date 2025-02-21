# Store configurations
STORES = {
    'Best Buy': {
        'name': 'Best Buy',
        'search_url': 'https://www.bestbuy.ca/api/v2/json/search?query={}',
        'product_base_url': 'https://www.bestbuy.ca/en-ca/product/',
        'api_base_url': 'https://www.bestbuy.ca/api/v2/json/product/'
    }
}

# Intervals
DEFAULT_INTERVAL = 15
MIN_INTERVAL = 5

# Window size
WINDOW_SIZE = (1200, 800)

# Add this
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
REQUEST_HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}

# API endpoints
API_URL = "https://www.bestbuy.ca/api/v2/json/product" 