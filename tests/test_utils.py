import pytest
from stock_monitor.utils.helpers import check_stock, parse_url
from stock_monitor.utils.exceptions import URLError, APIError, URLParseError
import requests

def test_url_parsing():
    """Test URL parsing functionality."""
    # Test valid URL
    url = "https://www.bestbuy.ca/en-ca/product/12345"
    assert parse_url(url) == "12345"
    
    # Test invalid URL - should raise URLParseError
    with pytest.raises(URLParseError) as exc_info:
        parse_url("invalid_url")
    assert "Invalid URL format" == str(exc_info.value)
    
    # Test malformed URL - should also raise URLParseError
    with pytest.raises(URLParseError) as exc_info:
        parse_url("https://www.bestbuy.ca/en-ca/products/12345")
    assert "Could not find product ID" == str(exc_info.value)

def test_stock_checking(mock_api, monkeypatch):
    """Test stock checking functionality."""
    def mock_get(*args, **kwargs):
        return type('Response', (), {
            'status_code': 200,
            'json': lambda *args: mock_api['products'][0]  # Return single product
        })()
    
    monkeypatch.setattr('requests.get', mock_get)
    
    success, name, info = check_stock("12345")
    assert success
    assert name == mock_api['products'][0]['name']
    assert info['status'] == mock_api['products'][0]['availability']['onlineAvailability']

def test_stock_checking_errors(monkeypatch):
    """Test stock checking error handling."""
    def mock_error(*args, **kwargs):
        raise requests.exceptions.RequestException("Connection error")
    
    monkeypatch.setattr('requests.get', mock_error)
    
    with pytest.raises(APIError) as exc:
        check_stock("12345")
    assert "Connection error" in str(exc.value) 