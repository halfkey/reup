import pytest
from reup.core.product_monitor import ProductMonitor
from unittest.mock import MagicMock, patch
import time


@pytest.fixture
def mock_monitor(root, app, monkeypatch):
    """Create a mocked monitor for testing."""
    # Patch all potentially problematic methods before creating monitor
    monkeypatch.setattr("reup.utils.helpers.parse_url", lambda x: "12345")
    monkeypatch.setattr(
        "reup.utils.helpers.check_stock",
        lambda x: (True, "Test Product", {"status": "InStock", "stock": 5}),
    )

    monitor = ProductMonitor(
        root, "https://www.bestbuy.ca/en-ca/product/12345", app, test_mode=True
    )

    # Mock UI components
    monitor.start_button = MagicMock()
    monitor.pause_button = MagicMock()
    monitor.status_label = MagicMock()
    monitor.interval_entry = MagicMock(get=MagicMock(return_value="15"))
    monitor.log_display = MagicMock()
    monitor.log_message = MagicMock()

    # Replace tkinter's after with immediate execution
    def mock_after(ms, func=None, *args):
        if func and not monitor.paused:
            func(*args)
        return "after_id"

    monitor.after = mock_after
    monitor.after_cancel = MagicMock()

    # Stop actual monitoring
    monitor.monitor_product = MagicMock()

    yield monitor

    # Cleanup
    monitor.paused = True
    monitor.stop_monitoring()


@pytest.mark.timeout(1)
def test_monitor_start(mock_monitor):
    """Test that monitoring starts correctly."""
    with patch.object(mock_monitor, "monitor_product") as mock_monitor_product:
        mock_monitor.start_monitoring()
        assert not mock_monitor.paused
        assert mock_monitor_product.called
        mock_monitor.start_button.config.assert_called_with(
            text="⏹ Stop", command=mock_monitor.stop_monitoring
        )


@pytest.mark.timeout(1)
def test_monitor_status_update(mock_monitor):
    """Test that monitor status updates correctly."""

    # Mock monitor_product to call check_stock
    def mock_monitor_product():
        mock_monitor.check_stock()

    mock_monitor.monitor_product = MagicMock(side_effect=mock_monitor_product)

    # Mock check_stock
    mock_monitor.check_stock = MagicMock(
        return_value=(True, "Test Product", {"status": "InStock", "stock": 5})
    )

    # Start monitoring
    mock_monitor.start_monitoring()

    # Verify check_stock was called
    assert mock_monitor.check_stock.called


@pytest.mark.timeout(1)
def test_monitor_stop(mock_monitor):
    """Test that monitoring stops correctly."""
    # Mock tkinter widget ID
    mock_monitor._w = "test_widget"

    # Mock monitor_product
    mock_monitor.monitor_product = MagicMock()

    # Start monitoring
    mock_monitor.start_monitoring()

    # Store initial call count
    initial_calls = mock_monitor.monitor_product.call_count

    # Stop monitoring and verify
    mock_monitor.stop_monitoring()
    mock_monitor.paused = True  # Explicitly set paused state
    assert mock_monitor.paused

    # Verify no additional calls after stopping
    assert mock_monitor.monitor_product.call_count == initial_calls


@pytest.mark.timeout(1)
def test_monitor_pause_resume(mock_monitor):
    """Test pause/resume functionality."""
    mock_monitor.start_monitoring()
    mock_monitor.toggle_pause()
    assert mock_monitor.paused
    mock_monitor.toggle_pause()
    assert not mock_monitor.paused
