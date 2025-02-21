import pytest
from unittest.mock import MagicMock
from tests.test_utils.test_monitor import TestMonitor


@pytest.fixture
def test_monitor():
    """Create a test monitor instance for testing."""
    # Create instance with mocked components
    root = MagicMock()
    app = MagicMock()
    monitor = TestMonitor(root, "https://test.com", app)

    # Add required mocks
    monitor.log_display = MagicMock()
    monitor.status_label = MagicMock()
    monitor.after = MagicMock()
    monitor.after_cancel = MagicMock()

    return monitor


def test_monitor_functionality(test_monitor):
    """Test basic monitor functionality."""
    success, name, status = test_monitor.check_stock()
    assert success
    assert name == "Test Product"
    assert status["status"] == "InStock"
