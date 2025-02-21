import pytest
from unittest.mock import MagicMock
from reup.core.base_monitor import BaseMonitor

class TestMonitor(BaseMonitor):
    """Concrete implementation of BaseMonitor for testing."""
    def check_stock(self):
        return True, "Test Product", {'status': 'InStock'}
        
    def setup_ui(self):
        pass
        
    def validate_interval(self):
        return 15
        
    def monitor_product(self):
        pass
        
    def start_monitoring(self):
        """Implementation of abstract start_monitoring method."""
        self.paused = False
        self.monitor_product()
        
    def stop_monitoring(self):
        """Implementation of abstract stop_monitoring method."""
        self.paused = True
        if hasattr(self, 'scheduled_check'):
            self.after_cancel(self.scheduled_check)

@pytest.fixture
def test_monitor_instance(root, app):
    """Create a test monitor instance."""
    monitor = TestMonitor(root, "https://test.com", app)
    monitor.log_display = MagicMock()
    monitor.status_label = MagicMock()
    monitor.after = MagicMock()
    monitor.after_cancel = MagicMock()
    return monitor 