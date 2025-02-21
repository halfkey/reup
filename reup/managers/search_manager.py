from typing import Dict, List, Optional
import requests
from ..utils.exceptions import APIError
from ..config.constants import STORES
import logging

class SearchManager:
    """Handles product search operations across different stores."""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def search_products(self, store: str, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for products in the specified store.
        Returns a list of product dictionaries.
        """
        if store not in STORES:
            raise ValueError(f"Unsupported store: {store}")
        
        store_config = STORES[store]
        search_method = getattr(self, f"search_{store.lower().replace(' ', '_')}")
        return search_method(query, limit)
    
    def search_best_buy(self, query: str, limit: int = 10) -> List[Dict]:
        """Search Best Buy's API for products."""
        try:
            search_url = STORES['Best Buy']['search_url'].format(query)
            response = requests.get(search_url, headers=self.headers)
            
            if response.status_code != 200:
                raise APIError(response.status_code, "Failed to search Best Buy")
            
            data = response.json()
            products = data.get('products', [])
            
            results = []
            for product in products[:limit]:
                results.append({
                    'name': product.get('name', 'Unknown Product'),
                    'price': float(product.get('regularPrice', 0)),
                    'url': f"{STORES['Best Buy']['product_base_url']}{product.get('sku')}",
                    'image_url': product.get('thumbnailImage'),
                    'store': 'Best Buy',
                    'id': product.get('sku')
                })
            
            return results
            
        except Exception as e:
            logging.error(f"Search error: {str(e)}")
            raise APIError(500, f"Best Buy search error: {str(e)}")
    
    def format_search_results(self, results: List[Dict]) -> List[Dict]:
        """Format search results for display."""
        formatted = []
        for result in results:
            formatted.append({
                'display_name': result['name'][:80] + '...' if len(result['name']) > 80 else result['name'],
                'price': f"${result['price']:.2f}" if result['price'] else 'N/A',
                'id': result['id'],
                'url': result['url'],
                'store': result['store']
            })
        return formatted 