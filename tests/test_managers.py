import pytest
from stock_monitor.managers.profile_manager import ProfileManager
from stock_monitor.managers.search_manager import SearchManager
from stock_monitor.utils.exceptions import ProfileLoadError, ProfileSaveError
from unittest.mock import MagicMock
import requests

def test_profile_manager():
    """Test profile management functionality."""
    manager = ProfileManager()
    
    # Test profile save/load
    test_data = {
        'products': [
            {'url': 'https://www.bestbuy.ca/en-ca/product/12345'}
        ],
        'interval': 15
    }
    
    # Save profile
    manager.save_profile('test_profile', test_data)
    
    # Load profile
    loaded_data = manager.load_profile('test_profile')
    assert loaded_data['products'] == test_data['products']
    assert loaded_data['interval'] == test_data['interval']

def test_search_manager(mock_api, monkeypatch):
    """Test product search functionality."""
    manager = SearchManager()
    
    # Mock the API response
    def mock_get(*args, **kwargs):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = lambda: mock_api
        return mock_response
    
    monkeypatch.setattr('requests.get', mock_get)
    
    # Test search
    results = manager.search_products('Best Buy', 'test query')
    assert len(results) > 0
    assert results[0]['name'] == mock_api['products'][0]['name']
    assert results[0]['price'] == float(mock_api['products'][0]['regularPrice'])

def test_search_manager_operations(mock_api, monkeypatch):
    """Test search manager operations."""
    search_manager = SearchManager()
    
    # Mock requests
    def mock_get(*args, **kwargs):
        return type('Response', (), {
            'status_code': 200,
            'json': lambda: {
                'products': mock_api['products'],
                'total': 1,
                'currentPage': 1,
                'totalPages': 1
            }
        })()
    monkeypatch.setattr('requests.get', mock_get)
    
    # Test basic search with correct store name
    results = search_manager.search_products('Best Buy', 'test')
    assert len(results) == 1
    assert results[0]['name'] == mock_api['products'][0]['name']
    
    # Test error handling
    def mock_error(*args, **kwargs):
        raise requests.exceptions.RequestException("Search error")
    monkeypatch.setattr('requests.get', mock_error)
    
    with pytest.raises(APIError) as exc:
        search_manager.search_products('bestbuy', 'test')
    assert "Search error" in str(exc.value) 