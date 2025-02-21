import pytest
from reup.utils.exceptions import APIError, URLError
import requests
from unittest.mock import MagicMock
from reup.core.product_monitor import ProductMonitor

def test_api_errors(root, app, monkeypatch):
    """Test handling of API errors."""
    # Create monitor in test mode
    monitor = ProductMonitor(root, "https://www.bestbuy.ca/en-ca/product/12345", app, test_mode=True)
    
    # Mock necessary components
    monitor.log_message = MagicMock()
    monitor.log_error = MagicMock()
    monitor.update_status = MagicMock()
    monitor.interval_entry = MagicMock()
    monitor.interval_entry.get.return_value = "15"
    monitor.status_label = MagicMock()
    monitor.after = MagicMock()
    
    def mock_requests_get(*args, **kwargs):
        raise requests.exceptions.RequestException("API Error")
    
    monkeypatch.setattr('requests.get', mock_requests_get)
    
    # Test API error
    success, name, info = monitor.check_stock()
    assert not success
    assert name is None
    assert info is None
    assert "Error" in monitor.last_check_status

def test_invalid_inputs(root, app):
    """Test handling of invalid user inputs."""
    # Create monitor in test mode
    monitor = ProductMonitor(root, "https://www.bestbuy.ca/en-ca/product/12345", app, test_mode=True)
    
    # Mock necessary components
    monitor.interval_entry = MagicMock()
    monitor.log_message = MagicMock()
    monitor.status_label = MagicMock()
    monitor.after = MagicMock()
    
    # Test invalid interval
    monitor.interval_entry.get.return_value = "invalid"
    assert monitor.validate_interval() == 15  # Should return DEFAULT_INTERVAL
    
    # Test zero interval
    monitor.interval_entry.get.return_value = "0"
    assert monitor.validate_interval() == 5  # Should return MIN_INTERVAL
    
    # Test negative interval
    monitor.interval_entry.get.return_value = "-10"
    assert monitor.validate_interval() == 5  # Should return MIN_INTERVAL 