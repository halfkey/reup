# Configuration constants
DEFAULT_INTERVAL = 15
MIN_INTERVAL = 5

# Store configurations
STORES = {
    'Best Buy': {
        'name': 'Best Buy',
        'search_url': 'https://www.bestbuy.ca/api/v2/json/search?query={}',
        'product_base_url': 'https://www.bestbuy.ca/en-ca/product/',
        'api_base_url': 'https://www.bestbuy.ca/api/v2/json/product/'
    }
}

# Modern window size
WINDOW_SIZE = (1200, 800)

# UI Style configurations
STYLES = {
    'Custom.TButton': {'padding': 10},
    'Custom.TFrame': {'background': '#f0f0f0'},
    'Custom.TLabelframe': {'background': '#f0f0f0'},
    'Custom.TLabelframe.Label': {
        'background': '#f0f0f0',
        'font': ('Arial', 10, 'bold')
    },
    'Treeview': {
        'font': ('Arial', 10),
        'rowheight': 30
    },
    'Treeview.Heading': {
        'font': ('Arial', 10, 'bold')
    }
}

# Column configurations
PRODUCT_COLUMNS = {
    'URL': {'width': 600, 'text': 'Product URL'},
    'Status': {'width': 150, 'text': 'Status'},
    'Action': {'width': 50, 'text': ''},
    'Cart': {'width': 100, 'text': ''}
} 