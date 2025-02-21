# Move contents from test_utils.py to test_helper_utils.py 

import pytest
from unittest.mock import MagicMock, patch
from reup.utils.helpers import parse_url, check_stock
from reup.utils.exceptions import URLError, APIError, URLParseError

def test_url_parsing():
    """Test URL parsing functionality."""
    # Test valid URL
    assert parse_url("https://www.bestbuy.ca/en-ca/product/12345") == "12345"
    
    # Test invalid URL format
    with pytest.raises(URLParseError):
        parse_url("invalid_url")
    
    # Test URL without product ID
    with pytest.raises(URLParseError):
        parse_url("https://www.bestbuy.ca/en-ca/products/12345")

def test_stock_checking():
    """Test stock checking functionality."""
    with patch('requests.get') as mock_get:
        # Mock the response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            'products': [{
                'name': 'Test Product',
                'availability': {
                    'isAvailableOnline': True,
                    'onlineAvailability': 'InStock',
                    'onlineAvailabilityCount': 5
                }
            }]
        }
        mock_get.return_value = mock_response
        
        # Get the expected values from the mock response
        expected_name = mock_response.json()['products'][0]['name']
        expected_availability = mock_response.json()['products'][0]['availability']
        
        success, name, info = check_stock("12345")
        assert success
        assert name == expected_name
        assert info == {
            'status': expected_availability['onlineAvailability'],
            'stock': expected_availability['onlineAvailabilityCount']
        }

def test_stock_checking_errors():
    """Test error handling in stock checking."""
    with patch('requests.get', side_effect=Exception("Failed to check product")):
        success, name, info = check_stock("12345")
        assert not success
        assert name is None
        assert info == {'error': 'Failed to check product'} 