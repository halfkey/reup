import pytest
from unittest.mock import MagicMock, patch
import tkinter as tk
from tkinter import ttk
from stock_monitor.core.base_monitor import BaseMonitor
from tests.test_helpers import TestMonitor  # Changed from relative to absolute import

@pytest.fixture
def mock_parent():
    parent = MagicMock()
    parent.style = MagicMock()
    parent.log_message = MagicMock()
    return parent

@pytest.fixture
def base_monitor(mock_parent):
    monitor = TestMonitor(MagicMock(), mock_parent)
    monitor.log_display = MagicMock()
    return monitor

def test_base_monitor_init(mock_parent):
    """Test BaseMonitor initialization."""
    parent = MagicMock()
    monitor = TestMonitor(parent, mock_parent)
    
    assert monitor.main_app == mock_parent
    assert monitor.style == mock_parent.style
    assert monitor.log_display is None

def test_log_error(base_monitor):
    """Test error logging with and without main_app."""
    # Test with main_app
    error_msg = "Test error"
    base_monitor.log_error(error_msg)
    base_monitor.main_app.log_message.assert_called_once_with(f"Error: {error_msg}")
    
    # Test without main_app
    base_monitor.main_app = None
    with patch('logging.error') as mock_log:
        base_monitor.log_error(error_msg)
        mock_log.assert_called_once_with(error_msg)

def test_update_status(base_monitor):
    """Test status updates."""
    # Test with status_label
    base_monitor.status_label = MagicMock()
    status_info = {'status': 'Available'}
    
    base_monitor.update_status(status_info)
    base_monitor.status_label.config.assert_called_once_with(
        text=f"Status: {status_info['status']}"
    )
    
    # Test without status_label
    base_monitor.status_label = None
    base_monitor.update_status(status_info)  # Should not raise error
    
    # Test with missing status key
    base_monitor.status_label = MagicMock()
    empty_status = {}
    base_monitor.update_status(empty_status)
    base_monitor.status_label.config.assert_called_with(
        text="Status: Unknown"
    )

def test_log_message(base_monitor):
    """Test message logging."""
    test_message = "Test message"
    timestamp = "2024-02-20 12:00:00"
    
    # Test with log_display
    with patch('stock_monitor.core.base_monitor.get_timestamp', return_value=timestamp):
        base_monitor.log_message(test_message)
        
        expected_log = f"{timestamp} {test_message}\n"
        base_monitor.log_display.insert.assert_called_once_with("1.0", expected_log)
        base_monitor.log_display.see.assert_called_once_with("1.0")
        base_monitor.parent.log_message.assert_called_once_with(test_message)
    
    # Test without log_display
    base_monitor.log_display = None
    base_monitor.parent.log_message.reset_mock()
    
    with patch('stock_monitor.core.base_monitor.get_timestamp', return_value=timestamp):
        base_monitor.log_message(test_message)
        base_monitor.parent.log_message.assert_called_once_with(test_message)

def test_abstract_method_implementations(base_monitor):
    """Test that concrete implementations can be called."""
    # These should not raise any exceptions
    base_monitor.setup_ui()
    base_monitor.start_monitoring()
    base_monitor.stop_monitoring()

def test_abstract_methods():
    """Test that abstract methods raise NotImplementedError."""
    monitor = TestMonitor(MagicMock(), MagicMock())
    
    # Create a new class without implementing abstract methods
    class IncompleteMonitor(BaseMonitor):
        pass
    
    with pytest.raises(TypeError):
        IncompleteMonitor(MagicMock(), MagicMock())

def test_log_error_with_main_app(base_monitor):
    """Test error logging with main_app."""
    error_msg = "Test error"
    base_monitor.main_app.log_message = MagicMock()
    
    base_monitor.log_error(error_msg)
    base_monitor.main_app.log_message.assert_called_once_with(f"Error: {error_msg}")

def test_log_error_without_main_app(base_monitor):
    """Test error logging without main_app."""
    error_msg = "Test error"
    base_monitor.main_app = None
    
    with patch('logging.error') as mock_log:
        base_monitor.log_error(error_msg)
        mock_log.assert_called_once_with(error_msg)

def test_update_status_with_label(base_monitor):
    """Test status updates with label."""
    base_monitor.status_label = MagicMock()
    status_info = {'status': 'Available'}
    
    base_monitor.update_status(status_info)
    base_monitor.status_label.config.assert_called_once_with(
        text="Status: Available"
    )

def test_update_status_without_label(base_monitor):
    """Test status updates without label."""
    base_monitor.status_label = None
    status_info = {'status': 'Available'}
    
    # Should not raise any errors
    base_monitor.update_status(status_info)

def test_update_status_with_missing_status(base_monitor):
    """Test status updates with missing status key."""
    base_monitor.status_label = MagicMock()
    status_info = {}  # Missing status key
    
    base_monitor.update_status(status_info)
    base_monitor.status_label.config.assert_called_once_with(
        text="Status: Unknown"
    ) 