import pytest
from reup.core.product_monitor import ProductMonitor
from reup.utils.exceptions import StockCheckError, APIError
from unittest.mock import MagicMock
import requests
from unittest.mock import patch
from reup.utils.helpers import check_stock


def test_product_monitor_init(root, app, mock_tk):
    """Test ProductMonitor initialization."""
    url = "https://www.bestbuy.ca/en-ca/product/12345"
    monitor = ProductMonitor(root, url, app)

    assert monitor.url == url
    assert monitor.paused == False
    assert monitor.scheduled_check is None
    assert hasattr(monitor, "log_display")
    assert hasattr(monitor, "interval_entry")


def test_validate_interval(root, app, mock_tk):
    """Test interval validation."""
    # Create monitor in test mode
    monitor = ProductMonitor(
        root, "https://www.bestbuy.ca/en-ca/product/12345", app, test_mode=True
    )

    # Mock the interval entry and log_message
    monitor.interval_entry = MagicMock()
    monitor.log_message = MagicMock()

    # Test valid interval
    monitor.interval_entry.get.return_value = "15"
    assert monitor.validate_interval() == 15

    # Test interval too low
    monitor.interval_entry.get.return_value = "2"
    assert monitor.validate_interval() == 10  # Updated to match new MIN_INTERVAL


@pytest.mark.timeout(5)
def test_check_stock(mock_api, monkeypatch):
    """Test stock checking functionality."""
    with patch("requests.get") as mock_get:
        # Mock the response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "products": [
                {
                    "name": "Test Product",
                    "availability": {
                        "isAvailableOnline": True,
                        "onlineAvailability": "InStock",
                        "onlineAvailabilityCount": 5,
                    },
                }
            ]
        }
        mock_get.return_value = mock_response

        success, name, info = check_stock("12345")
        assert success, "Stock check should succeed"
        assert name == "Test Product"
        assert info["status"] == "InStock"
        assert info["stock"] == 5


def test_error_handling(root, app, monkeypatch):
    """Test error handling in monitor."""
    monitor = ProductMonitor(root, "invalid_url", app, test_mode=True)

    # Mock components
    monitor.log_message = MagicMock()
    monitor.log_error = MagicMock()
    monitor.update_status = MagicMock()

    # Mock parse_url to raise URLParseError
    def mock_parse_url(url):
        from reup.utils.exceptions import URLParseError

        error_msg = "Could not extract product ID: Invalid URL scheme"  # Match the actual error message
        print(f"Error in check_stock: {error_msg}")
        raise URLParseError(error_msg)

    monkeypatch.setattr("reup.utils.helpers.parse_url", mock_parse_url)

    # Test error handling
    success, name, info = monitor.check_stock()
    assert not success
    assert name is None
    assert info == {"error": "Failed to check product"}
    # Verify the error was logged by the monitor with the exact error message
    monitor.log_error.assert_called_once_with(
        "Could not extract product ID: Invalid URL scheme"
    )


def test_check_stock_api_error():
    """Test handling of API errors."""
    with patch("requests.get", side_effect=APIError(500, "API Error")):
        success, name, info = check_stock("12345")
        assert not success
        assert name is None
        assert info == {"error": "API Error (500): API Error"}


def test_check_stock_invalid_response():
    """Test handling of invalid response."""
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.side_effect = AttributeError(
            "'MockResponse' object has no attribute 'raise_for_status'"
        )
        mock_get.return_value = mock_response

        success, name, info = check_stock("12345")
        assert not success
        assert name is None
        assert info == {
            "error": "'MockResponse' object has no attribute 'raise_for_status'"
        }


def test_monitor_lifecycle(root, mock_api, monkeypatch):
    """Test the full monitoring lifecycle."""
    monitor = ProductMonitor(
        root, "https://www.bestbuy.ca/en-ca/product/12345", mock_api, test_mode=True
    )

    # Mock UI components
    monitor.start_button = MagicMock()
    monitor.pause_button = MagicMock()
    monitor.status_label = MagicMock()
    monitor.interval_entry = MagicMock()
    monitor.interval_entry.get.return_value = "15"

    # Mock after method
    monitor.after = MagicMock()
    monitor.after_cancel = MagicMock()

    # Mock check_stock
    monitor.check_stock = MagicMock(return_value=(True, "Test Product", {}))

    # Start monitoring
    monitor.start_monitoring()
    assert not monitor.paused
    monitor.start_button.config.assert_called_with(
        text="⏹ Stop", command=monitor.stop_monitoring
    )


def test_stock_notifications(root, mock_api, monkeypatch):
    """Test stock availability notifications."""
    mock_app = MagicMock()
    monitor = ProductMonitor(
        root, "https://www.bestbuy.ca/en-ca/product/12345", mock_app, test_mode=True
    )

    # Mock notification system
    mock_notify = MagicMock()
    monkeypatch.setattr("plyer.notification.notify", mock_notify)

    # Test notification when stock becomes available
    monitor.notify_stock_available("Test Product", 5)
    mock_notify.assert_called_once()
    assert "Test Product" in mock_notify.call_args[1]["message"]


@pytest.mark.parametrize(
    "interval,expected",
    [
        ("15", 15),
        ("2", 10),  # Should return MIN_INTERVAL (10)
        ("invalid", 15),  # Should return DEFAULT_INTERVAL
        ("0", 10),  # Should return MIN_INTERVAL
        ("100", 100),
    ],
)
def test_interval_validation(root, mock_api, interval, expected):
    """Test interval validation with various inputs."""
    mock_app = MagicMock()
    monitor = ProductMonitor(
        root, "https://www.bestbuy.ca/en-ca/product/12345", mock_app, test_mode=True
    )

    monitor.interval_entry = MagicMock()
    monitor.interval_entry.get.return_value = interval

    assert monitor.validate_interval() == expected
