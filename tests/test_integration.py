import pytest
import tkinter as tk
from reup.gui.main_window import StockMonitorGUI
from unittest.mock import MagicMock
import time

@pytest.mark.timeout(10)  # Add timeout to prevent hanging
def test_full_monitoring_cycle(root, app, mock_api, monkeypatch):
    """Test a full monitoring cycle."""
    # Mock necessary components
    app.notebook = MagicMock()
    app.product_tree = MagicMock()
    app.monitor_tabs = {}
    app.handle_error = MagicMock()
    app.style = MagicMock()
    app.log_message = MagicMock()
    
    # Mock tree methods
    app.product_tree.get_children = MagicMock(return_value=[])
    app.product_tree.item = MagicMock(return_value={'values': ['', '', '', '', '']})
    app.product_tree.insert = MagicMock(return_value='item1')
    
    # Mock notebook methods
    app.notebook.select = MagicMock()
    app.notebook.forget = MagicMock()
    app.notebook.add = MagicMock()
    app.notebook.index = MagicMock(return_value=1)
    app.notebook.tab = MagicMock()
    
    # Mock check_stock to simulate stock changes
    stock_status = {'available': False}
    
    # Mock response object
    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self.json_data = json_data
            self.status_code = status_code
            
        def json(self):
            return self.json_data
    
    # Mock requests.get
    def mock_requests_get(*args, **kwargs):
        stock_status['available'] = not stock_status['available']  # Toggle availability
        mock_data = mock_api['products'][0].copy()
        mock_data['availability']['isAvailableOnline'] = stock_status['available']
        mock_data['availability']['onlineAvailability'] = 'InStock' if stock_status['available'] else 'OutOfStock'
        mock_data['availability']['onlineAvailabilityCount'] = 5 if stock_status['available'] else 0
        return MockResponse(mock_data)
    
    # Apply mocks
    monkeypatch.setattr('requests.get', mock_requests_get)
    
    # Add test product
    url = "https://www.bestbuy.ca/en-ca/product/12345"
    monitor = app.add_product_to_monitor(url)
    assert monitor is not None
    
    # Mock interval validation
    monitor.interval_entry = MagicMock()
    monitor.interval_entry.get.return_value = "15"
    
    # Mock the after method to execute immediately but prevent recursion
    monitor.monitor_count = 0  # Add counter to prevent infinite recursion
    def mock_after(ms, func, *args):
        if monitor.monitor_count < 3 and not monitor.paused:  # Limit to 3 cycles
            monitor.monitor_count += 1
            func(*args)
        return "after_id"
    
    monitor.after = mock_after
    monitor.after_cancel = MagicMock()
    
    # Start monitoring
    app.start_monitoring(url)
    tab_name = f"Monitor_{url.split('/')[-1]}"
    assert tab_name in app.monitor_tabs
    
    # Run one monitoring cycle manually
    monitor.monitor_product()
        
    # Verify monitoring status
    assert monitor.last_check_status is not None
    
    # Test pause/resume
    monitor.toggle_pause()
    assert monitor.paused
    
    monitor.toggle_pause()
    assert not monitor.paused
    
    # Stop monitoring
    app.stop_monitoring(tab_name)
    assert tab_name not in app.monitor_tabs 