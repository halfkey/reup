import pytest
from reup.core.product_monitor import ProductMonitor
from reup.utils.exceptions import StockCheckError
from unittest.mock import MagicMock
import requests

def test_product_monitor_init(root, app, mock_tk):
    """Test ProductMonitor initialization."""
    url = "https://www.bestbuy.ca/en-ca/product/12345"
    monitor = ProductMonitor(root, url, app)
    
    assert monitor.url == url
    assert monitor.paused == False
    assert monitor.scheduled_check is None
    assert hasattr(monitor, 'log_display')
    assert hasattr(monitor, 'interval_entry')

def test_validate_interval(root, app, mock_tk):
    """Test interval validation."""
    # Create monitor in test mode
    monitor = ProductMonitor(root, "https://www.bestbuy.ca/en-ca/product/12345", app, test_mode=True)
    
    # Mock the interval entry and log_message
    monitor.interval_entry = MagicMock()
    monitor.log_message = MagicMock()
    
    # Test valid interval
    monitor.interval_entry.get.return_value = "15"
    assert monitor.validate_interval() == 15
    
    # Test interval too low
    monitor.interval_entry.get.return_value = "2"
    assert monitor.validate_interval() == 5  # Should return MIN_INTERVAL

@pytest.mark.timeout(5)
def test_check_stock(root, app, mock_api, monkeypatch, caplog):
    """Test stock checking functionality."""
    caplog.set_level("INFO")
    print("\nTest starting...")
    
    # Create monitor without full GUI initialization
    from reup.core.product_monitor import ProductMonitor
    
    # Mock the entire app
    mock_app = MagicMock()
    mock_app.log_message = MagicMock()
    mock_app.style = MagicMock()
    mock_app.notebook = MagicMock()
    
    print("Creating monitor...")
    monitor = ProductMonitor(root, "https://www.bestbuy.ca/en-ca/product/12345", mock_app, test_mode=True)
    print("Monitor created")
    
    # Mock the required attributes that would normally be set by setup_ui
    monitor.log_display = MagicMock()
    monitor.status_label = MagicMock()
    monitor.interval_entry = MagicMock()
    monitor.interval_entry.get.return_value = "15"
    monitor.update_status = MagicMock()
    monitor.last_check_status = None
    
    # Create mock functions
    def mock_parse_url(url):
        print(f"mock_parse_url called with: {url}")
        return "12345"
    
    # Mock response object
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code
            
        def json(self):
            return self.json_data
            
    def mock_requests_get(*args, **kwargs):
        print(f"mock_requests_get called with: args={args}, kwargs={kwargs}")
        return MockResponse(mock_api['products'][0], 200)
    
    def mock_check_stock(product_id):
        print(f"mock_check_stock called with: {product_id}")
        result = (True, mock_api['products'][0]['name'], {
            'name': mock_api['products'][0]['name'],
            'stock': mock_api['products'][0]['availability']['onlineAvailabilityCount'],
            'status': mock_api['products'][0]['availability']['onlineAvailability'],
            'purchasable': 'Yes'
        })
        print(f"mock_check_stock returning: {result}")
        return result
    
    # Mock all potential problematic methods
    print("Setting up mocks...")
    monkeypatch.setattr('logging.info', lambda x: print(f"log: {x}"))
    monkeypatch.setattr('logging.error', lambda x: print(f"error: {x}"))
    monkeypatch.setattr('reup.utils.helpers.parse_url', mock_parse_url)
    monkeypatch.setattr('requests.get', mock_requests_get)  # Mock requests.get
    
    # Important: Mock at the correct import location
    import reup.utils.helpers
    monkeypatch.setattr(reup.utils.helpers, 'check_stock', mock_check_stock)
    print("Mocks set up")
    
    # Test successful stock check
    print("Starting stock check...")
    try:
        success, name, info = monitor.check_stock()
        print(f"Stock check completed with: success={success}, name={name}, info={info}")
    except Exception as e:
        print(f"Exception during check_stock: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    print("Running assertions...")
    assert success
    assert name == mock_api['products'][0]['name']
    assert info['status'] == mock_api['products'][0]['availability']['onlineAvailability']
    print("Test completed successfully")

def test_error_handling(root, app, monkeypatch):
    """Test error handling in monitor."""
    # Create monitor in test mode
    monitor = ProductMonitor(root, "invalid_url", app, test_mode=True)
    
    # Mock necessary components
    monitor.log_message = MagicMock()
    monitor.log_error = MagicMock()
    monitor.update_status = MagicMock()
    
    # Mock parse_url to raise an error
    def mock_parse_url(url):
        raise ValueError("Invalid URL")
    
    monkeypatch.setattr('reup.utils.helpers.parse_url', mock_parse_url)
    
    # Test invalid URL
    success, name, info = monitor.check_stock()
    assert not success
    assert name is None
    assert info is None
    assert "Error" in monitor.last_check_status

def test_check_stock_api_error(root, mock_api, monkeypatch):
    """Test handling of API errors."""
    mock_app = MagicMock()
    monitor = ProductMonitor(root, "https://www.bestbuy.ca/en-ca/product/12345", mock_app, test_mode=True)
    
    def mock_requests_get(*args, **kwargs):
        raise requests.exceptions.RequestException("API Error")
    
    monkeypatch.setattr('requests.get', mock_requests_get)
    
    success, name, info = monitor.check_stock()
    assert not success
    assert name is None
    assert info is None

def test_check_stock_invalid_response(root, mock_api, monkeypatch):
    """Test handling of invalid API responses."""
    mock_app = MagicMock()
    monitor = ProductMonitor(root, "https://www.bestbuy.ca/en-ca/product/12345", mock_app, test_mode=True)
    
    class MockResponse:
        def __init__(self):
            self.status_code = 200
        def json(self):
            return {"invalid": "response"}
    
    monkeypatch.setattr('requests.get', lambda *args, **kwargs: MockResponse())
    
    success, name, info = monitor.check_stock()
    assert not success
    assert "Error" in monitor.last_check_status

def test_monitor_lifecycle(root, mock_api, monkeypatch):
    """Test the full monitoring lifecycle."""
    mock_app = MagicMock()
    mock_app.notebook = MagicMock()
    mock_app.monitor_tabs = {}
    
    monitor = ProductMonitor(root, "https://www.bestbuy.ca/en-ca/product/12345", mock_app, test_mode=True)
    
    # Mock necessary components
    monitor.interval_entry = MagicMock()
    monitor.interval_entry.get.return_value = "15"
    monitor.status_label = MagicMock()
    monitor.pause_button = MagicMock()
    monitor.log_message = MagicMock()
    monitor.update_status = MagicMock()
    monitor.after = MagicMock()  # Mock the after method
    monitor.after.return_value = "after_id"  # Return a dummy after_id
    monitor.after_cancel = MagicMock()
    
    # Mock check_stock to avoid API calls
    def mock_check_stock(*args):
        return True, "Test Product", {"status": "InStock", "stock": 5}
    monitor.check_stock = mock_check_stock
    
    # Start monitoring
    monitor.start_monitoring()
    assert not monitor.paused
    assert monitor.scheduled_check == "after_id"  # Check the after_id
    monitor.after.assert_called_with(15000, monitor.monitor_product)  # Check interval
    
    # Pause monitoring
    monitor.toggle_pause()
    assert monitor.paused
    monitor.pause_button.config.assert_called_with(text="▶️ Resume")
    monitor.status_label.config.assert_called_with(text="Status: Paused")
    
    # Resume monitoring
    monitor.toggle_pause()
    assert not monitor.paused
    monitor.pause_button.config.assert_called_with(text="⏸️ Pause")
    monitor.status_label.config.assert_called_with(text="Status: Running")
    
    # Stop monitoring
    monitor.stop_monitoring()
    assert monitor.scheduled_check is None
    monitor.after_cancel.assert_called_with("after_id")

def test_stock_notifications(root, mock_api, monkeypatch):
    """Test stock availability notifications."""
    mock_app = MagicMock()
    monitor = ProductMonitor(root, "https://www.bestbuy.ca/en-ca/product/12345", mock_app, test_mode=True)
    
    # Mock notification system
    mock_notify = MagicMock()
    monkeypatch.setattr('plyer.notification.notify', mock_notify)
    
    # Test notification when stock becomes available
    monitor.notify_stock_available("Test Product", 5)
    mock_notify.assert_called_once()
    assert "Test Product" in mock_notify.call_args[1]['message'] 

@pytest.mark.parametrize("interval,expected", [
    ("15", 15),
    ("2", 5),  # Should return MIN_INTERVAL
    ("invalid", 15),  # Should return DEFAULT_INTERVAL
    ("0", 5),  # Should return MIN_INTERVAL
    ("100", 100)
])
def test_interval_validation(root, mock_api, interval, expected):
    """Test interval validation with various inputs."""
    mock_app = MagicMock()
    monitor = ProductMonitor(root, "https://www.bestbuy.ca/en-ca/product/12345", mock_app, test_mode=True)
    
    monitor.interval_entry = MagicMock()
    monitor.interval_entry.get.return_value = interval
    
    assert monitor.validate_interval() == expected 