import pytest
from reup.utils.helpers import check_stock, parse_url
from reup.utils.exceptions import URLError, APIError, URLParseError
import requests
from reup.config.constants import API_URL

def test_url_parsing():
    """Test URL parsing functionality."""
    # Test valid URL
    url = "https://www.bestbuy.ca/en-ca/product/12345"
    assert parse_url(url) == "12345"
    
    # Test invalid URL - should raise URLParseError
    with pytest.raises(URLParseError) as exc_info:
        parse_url("invalid_url")
    assert str(exc_info.value) == "Could not extract product ID: Invalid URL scheme"
    
    # Test missing product ID
    with pytest.raises(URLParseError) as exc_info:
        parse_url("https://www.bestbuy.ca/en-ca/product/")
    assert str(exc_info.value) == "Could not extract product ID: No product ID found"

def test_stock_checking(mock_api, monkeypatch):
    """Test stock checking functionality."""
    # Create a proper mock Response class
    class MockResponse:
        def __init__(self, status_code, json_data, raise_error=False):
            self.status_code = status_code
            self._json_data = json_data
            self.text = str(json_data)
            self._raise_error = raise_error
            
        def json(self):
            return self._json_data
            
        def raise_for_status(self):
            if self._raise_error or self.status_code >= 400:
                raise requests.exceptions.HTTPError(f"{self.status_code} Error")
    
    # Test successful case
    success_response = MockResponse(
        status_code=200,
        json_data={
            'name': mock_api['products'][0]['name'],
            'availability': {
                'onlineAvailability': 'InStock',
                'onlineAvailabilityCount': 5
            }
        }
    )
    
    def mock_get_success(*args, **kwargs):
        return success_response
    
    monkeypatch.setattr('requests.get', mock_get_success)
    
    success, name, info = check_stock("12345")
    assert success
    assert name == mock_api['products'][0]['name']
    assert info['status'] == 'InStock'
    assert info['stock'] == 5
    
    # Test connection error case
    def mock_connection_error(*args, **kwargs):
        raise requests.exceptions.ConnectionError("Connection error")
    
    monkeypatch.setattr('requests.get', mock_connection_error)
    
    with pytest.raises(APIError) as exc:
        check_stock("12345")
    assert "Connection error" in str(exc.value)
    
    # Test HTTP error case
    error_response = MockResponse(
        status_code=404,
        json_data={'error': 'Not found'},
        raise_error=True
    )
    
    def mock_http_error(*args, **kwargs):
        return error_response
    
    monkeypatch.setattr('requests.get', mock_http_error)
    
    with pytest.raises(APIError) as exc:
        check_stock("12345")
    assert "404" in str(exc.value) 