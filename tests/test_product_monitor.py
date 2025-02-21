import pytest
from unittest.mock import MagicMock, patch
import tkinter as tk
from tkinter import ttk
from stock_monitor.core.product_monitor import ProductMonitor
from stock_monitor.utils.exceptions import APIError, URLError
from stock_monitor.config.constants import MIN_INTERVAL
from stock_monitor.utils.helpers import get_timestamp
from stock_monitor.core.base_monitor import BaseMonitor

# ===== Fixtures =====
@pytest.fixture
def mock_tk():
    """Mock Tk and ttk to avoid actual window creation"""
    with patch('tkinter.Tk') as mock_tk, \
         patch('tkinter.ttk.Notebook') as mock_notebook, \
         patch('tkinter.ttk.Frame') as mock_frame:
        yield {
            'tk': mock_tk,
            'notebook': mock_notebook,
            'frame': mock_frame
        }

@pytest.fixture
def mock_parent():
    """Create a mock parent with required attributes."""
    parent = MagicMock()
    parent.style = MagicMock()
    parent.log_message = MagicMock()
    return parent

@pytest.fixture
def monitor(mock_tk, mock_parent):
    """Create a monitor instance with mocked components."""
    url = "https://www.bestbuy.ca/en-ca/product/12345"
    with patch('stock_monitor.core.product_monitor.ProductMonitor.setup_ui'):
        monitor = ProductMonitor(mock_tk['notebook'], url, mock_parent)
        # Add tkinter-specific mocks
        monitor.tk = mock_tk['tk']
        monitor.notebook = MagicMock()
        monitor.notebook.tabs = MagicMock(return_value=["tab1"])
        monitor.notebook.select = MagicMock(return_value="tab1")
        monitor.notebook.tab = MagicMock()
        
        # Mock other components
        monitor.interval_entry = MagicMock(get=MagicMock(return_value="15"))
        monitor.status_label = MagicMock()
        monitor.log_display = MagicMock()
        monitor.main_app = mock_parent
        monitor._w = "test_widget"
        return monitor

# ===== Test Classes =====
class TestBasicFunctionality:
    """Tests for basic initialization and core functionality"""
    def test_initialization(self, monitor, mock_tk, mock_parent):
        """Test basic initialization and edge cases."""
        url = "https://www.bestbuy.ca/en-ca/product/12345"
        assert monitor.url == url
        assert monitor.parent == mock_parent
        assert monitor.scheduled_check is None
        assert monitor.paused is False
        assert monitor.status == {
            'last_check': None,
            'last_status': None,
            'error_count': 0
        }
        assert isinstance(monitor.notebook, MagicMock)

    def test_check_stock(self, monitor):
        """Test stock checking functionality."""
        with patch('stock_monitor.core.product_monitor.ProductMonitor.check_stock') as mock_check:
            # Test successful check
            mock_check.return_value = (True, "Test Product", {
                'name': 'Test Product',
                'stock': 5,
                'status': 'InStock',
                'purchasable': 'Yes'
            })
            success, name, info = monitor.check_stock()
            assert success is True
            assert name == "Test Product"
            assert info['stock'] == 5
            
            # Test API error
            mock_check.return_value = (False, None, None)
            mock_check.side_effect = None
            success, name, info = monitor.check_stock()
            assert success is False
            assert name is None
            assert info is None

    def test_validate_interval(self, monitor):
        """Test interval validation including edge cases."""
        # Test valid interval
        monitor.interval_entry.get.return_value = "15"
        assert monitor.validate_interval() == 15

        # Test invalid intervals
        invalid_intervals = ["", "  ", "15.5", "-15", "abc", "0", "-1"]
        for interval in invalid_intervals:
            monitor.interval_entry.get.return_value = interval
            with pytest.raises(ValueError):
                monitor.validate_interval()

class TestUIInteractions:
    """Tests for UI updates and user interactions"""
    def test_setup_ui(self, monitor):
        """Test UI component setup."""
        monitor.tk = MagicMock()
        with patch('tkinter.ttk.LabelFrame'), \
             patch('tkinter.ttk.Frame'), \
             patch('tkinter.ttk.Button'), \
             patch('tkinter.ttk.Entry'), \
             patch('tkinter.ttk.Label'), \
             patch('tkinter.Text'):
            monitor.setup_ui()
            assert hasattr(monitor, 'control_frame')
            assert hasattr(monitor, 'log_frame')

    def test_update_status_label(self, monitor):
        """Test status label updates including edge cases."""
        monitor.status_label = MagicMock()
        monitor.notebook = MagicMock()
        monitor.notebook.tabs = MagicMock(return_value=["tab1"])
        monitor.notebook.select = MagicMock(return_value="test_widget")
        monitor.notebook.tab = MagicMock(return_value="Old Text")
        monitor._w = "test_widget"
        
        # Test normal status update
        status_details = {
            'status': 'InStock',
            'stock': 5,
            'purchasable': 'Yes'
        }
        monitor.update_status_label(status_details)
        monitor.status_label.config.assert_called_with(
            text="Status: InStock (5 units)"
        )
        assert monitor.notebook.tab.called

        # Test invalid data
        invalid_data = [None, {}, {'status': None, 'stock': 'invalid'}]
        for data in invalid_data:
            monitor.update_status_label(data)
            monitor.status_label.config.assert_called_with(
                text="Status: Unknown (0 units)"
            )

    def test_notification(self, monitor):
        """Test stock availability notifications."""
        monitor.log_message = MagicMock()
        
        with patch('plyer.notification.notify') as mock_notify:
            # Test successful notification
            monitor.notify_stock_available("Test Product", 5)
            mock_notify.assert_called_with(
                title='Product In Stock!',
                message='Test Product is now available!\n5 units in stock',
                timeout=10
            )
            
            # Test notification failure
            mock_notify.side_effect = Exception("OS notification failed")
            monitor.notify_stock_available("Test Product", 5)
            monitor.log_message.assert_called_with(
                "⚠️ Could not send notification: OS notification failed"
            )

    def test_log_message(self, monitor):
        """Test logging functionality."""
        timestamp = "2024-02-20 12:00:00"
        with patch('stock_monitor.core.base_monitor.get_timestamp', return_value=timestamp):
            test_message = "Test message"
            expected_log = f"{timestamp} {test_message}\n"
            monitor.log_message(test_message)
            monitor.log_display.insert.assert_called_once_with("1.0", expected_log)
            monitor.log_display.see.assert_called_once_with("1.0")
            monitor.parent.log_message.assert_called_once_with(test_message)

class TestLifecycle:
    """Tests for monitoring lifecycle (start/stop/pause)"""
    def test_monitor_product_lifecycle(self, monitor):
        """Test the full monitoring lifecycle including pause/resume."""
        monitor.validate_interval = MagicMock(return_value=15)
        monitor.check_stock = MagicMock(return_value=(True, "Test", {}))
        monitor.handle_stock_status = MagicMock()
        monitor.after = MagicMock()
        monitor.pause_button = MagicMock()
        
        # Test start monitoring
        monitor.start_monitoring()
        assert monitor.check_stock.call_count == 1
        assert not monitor.paused
        
        # Test pause/resume
        monitor.paused = True
        monitor.monitor_product()
        assert monitor.check_stock.call_count == 1  # Should not increase
        
        monitor.paused = False
        monitor.monitor_product()
        assert monitor.check_stock.call_count == 2

    def test_pause_resume_cycle(self, monitor):
        """Test pause/resume functionality including edge cases."""
        monitor.pause_button = MagicMock()
        monitor.after_cancel = MagicMock()
        monitor.monitor_product = MagicMock()
        
        # Test pause/resume without scheduled check
        monitor.scheduled_check = None
        monitor.toggle_pause()
        assert monitor.paused
        monitor.pause_button.config.assert_called_with(text="▶️ Resume")
        monitor.after_cancel.assert_not_called()
        
        monitor.toggle_pause()
        assert not monitor.paused
        monitor.pause_button.config.assert_called_with(text="⏸️ Pause")
        monitor.monitor_product.assert_called_once()

    def test_cleanup(self, monitor):
        """Test cleanup operations."""
        monitor.notebook.forget = MagicMock()
        monitor.cleanup()
        monitor.notebook.forget.assert_called_once()

class TestErrorHandling:
    """Tests for error conditions and recovery"""
    def test_api_errors(self, monitor):
        """Test handling of API errors."""
        error = APIError(404, "Not found")
        monitor.log_message = MagicMock()
        monitor.handle_monitoring_error(error)
        monitor.log_message.assert_called_with("❌ Error monitoring: API Error (404): Not found")

    def test_monitoring_errors(self, monitor):
        """Test comprehensive error handling."""
        monitor.validate_interval = MagicMock(return_value=15)
        monitor.check_stock = MagicMock(side_effect=APIError(500, "Server error"))
        monitor.after = MagicMock()
        monitor.log_message = MagicMock()
        
        monitor.monitor_product()
        monitor.log_message.assert_called_with(
            "❌ Error monitoring: API Error (500): Server error"
        )
        monitor.after.assert_called_once_with(15000, monitor.monitor_product)
        assert monitor.status['error_count'] == 1

    def test_cleanup_errors(self, monitor):
        """Test cleanup error handling."""
        monitor.notebook.forget = MagicMock(side_effect=Exception("Cleanup error"))
        monitor.log_error = MagicMock()
        monitor.cleanup()
        monitor.log_error.assert_called_once_with("Error during cleanup: Cleanup error")

class TestEdgeCases:
    """Tests for edge cases and boundary conditions"""
    def test_handle_stock_status(self, monitor):
        """Test stock status handling including edge cases."""
        monitor.log_status = MagicMock()
        monitor.update_status_label = MagicMock()
        monitor.notify_stock_available = MagicMock()
        
        status_details = {
            'name': 'Test Product',
            'stock': 5,
            'status': 'InStock',
            'purchasable': 'Yes'
        }
        
        # Test first check (no previous status)
        monitor.handle_stock_status(True, "Test Product", status_details)
        monitor.log_status.assert_called_with(status_details)
        monitor.update_status_label.assert_called_with(status_details)
        monitor.notify_stock_available.assert_called_with("Test Product", 5)
        
        # Test no change in status
        monitor.notify_stock_available.reset_mock()
        monitor.handle_stock_status(True, "Test Product", status_details)
        monitor.notify_stock_available.assert_not_called()
        
        # Test status change from available to unavailable
        monitor.notify_stock_available.reset_mock()
        monitor.handle_stock_status(False, "Test Product", {**status_details, 'stock': 0})
        assert monitor.status['last_status'] is False
        monitor.notify_stock_available.assert_not_called() 