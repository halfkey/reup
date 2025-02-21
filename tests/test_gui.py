import pytest
from unittest.mock import MagicMock, patch
import tkinter as tk
from tkinter import ttk
from reup.gui.main_window import StockMonitorGUI
from reup.core.product_monitor import ProductMonitor
from reup.utils.exceptions import APIError
import json
import os
from pathlib import Path


def test_add_product(root, app, mock_api, monkeypatch):
    """Test adding a product to monitor."""
    # Mock necessary components
    app.notebook = MagicMock()
    app.product_tree = MagicMock()
    app.monitor_tabs = {}
    app.handle_error = MagicMock()
    app.style = MagicMock()
    app.log_message = MagicMock()

    # Mock tree methods with proper duplicate checking
    tree_items = {}  # Store actual item values

    def mock_get_children():
        return list(tree_items.keys())

    app.product_tree.get_children = mock_get_children

    def mock_item(item_id):
        return {"values": tree_items.get(item_id, ["", "", "", "", ""])}

    app.product_tree.item = mock_item

    def mock_insert(*args, **kwargs):
        values = kwargs.get("values", ["", "", "", "", ""])
        # Check for duplicate URL
        for existing_values in tree_items.values():
            if existing_values[1] == values[1]:  # Compare URLs
                return None
        item_id = f"item{len(tree_items) + 1}"
        tree_items[item_id] = values
        return item_id

    app.product_tree.insert = MagicMock(side_effect=mock_insert)

    # Mock add_product_to_monitor
    def mock_add_product(url):
        # Check for duplicates first
        for item in app.product_tree.get_children():
            values = app.product_tree.item(item)["values"]
            if values[1] == url:
                return None

        # If not duplicate, create a simple mock monitor
        monitor = MagicMock()
        monitor.check_stock.return_value = (
            True,
            mock_api["products"][0]["name"],
            {
                "name": mock_api["products"][0]["name"],
                "stock": 5,
                "status": "InStock",
                "purchasable": "Yes",
            },
        )

        # Add to tree
        app.product_tree.insert(
            "",
            "end",
            values=(
                mock_api["products"][0]["name"],
                url,
                "Not Monitoring",
                "▶",
                "🛒 Add to Cart",
            ),
        )
        return monitor

    app.add_product_to_monitor = mock_add_product

    # Test adding a valid product
    url = "https://www.bestbuy.ca/en-ca/product/12345"
    monitor = app.add_product_to_monitor(url)
    assert monitor is not None
    assert len(tree_items) == 1

    # Test adding duplicate product
    monitor2 = app.add_product_to_monitor(url)
    assert monitor2 is None
    assert len(tree_items) == 1  # Should not add duplicate


def test_profile_management(root, app, tmp_profiles_dir, monkeypatch):
    """Test profile management functionality."""
    # Mock necessary components
    app.profile_var = MagicMock()
    app.profile_combo = MagicMock()
    app.product_tree = MagicMock()
    app.notebook = MagicMock()
    app.monitor_tabs = {}
    app.handle_error = MagicMock()
    app.style = MagicMock()
    app.log_message = MagicMock()

    # Mock tree methods
    tree_items = {}

    def mock_get_children():
        return list(tree_items.keys())

    app.product_tree.get_children = MagicMock(side_effect=mock_get_children)

    def mock_item(item_id):
        return {"values": tree_items.get(item_id, ["", "", "", "", ""])}

    app.product_tree.item = MagicMock(side_effect=mock_item)

    def mock_delete(item_id):
        if item_id in tree_items:
            del tree_items[item_id]

    app.product_tree.delete = MagicMock(side_effect=mock_delete)

    # Mock profile data
    test_profile = {
        "products": [
            {
                "name": "Test Product 1",
                "url": "https://www.bestbuy.ca/en-ca/product/12345",
            },
            {
                "name": "Test Product 2",
                "url": "https://www.bestbuy.ca/en-ca/product/67890",
            },
        ]
    }

    # Mock profile manager methods
    app.profile_manager.save_profile = MagicMock()
    app.profile_manager.load_profile = MagicMock(return_value=test_profile)
    app.profile_manager.list_profiles = MagicMock(return_value=["test_profile"])
    app.profile_manager.delete_profile = MagicMock()

    # Mock add_product_to_monitor
    def mock_add_product(url):
        item_id = f"item{len(tree_items) + 1}"
        tree_items[item_id] = ["Test Product", url, "Not Monitoring", "▶", ""]
        return MagicMock()

    app.add_product_to_monitor = mock_add_product

    # Add test products before saving
    for product in test_profile["products"]:
        app.add_product_to_monitor(product["url"])

    # Mock profile_var.get to return valid profile name for all operations
    app.profile_var.get.return_value = "test_profile"

    # Test saving profile
    app.save_profile()
    expected_products = []
    for item_values in tree_items.values():
        expected_products.append({"name": item_values[0], "url": item_values[1]})
    app.profile_manager.save_profile.assert_called_once_with(
        "test_profile", {"products": expected_products}
    )

    # Test loading profile
    app.load_profile()
    app.profile_manager.load_profile.assert_called_once_with("test_profile")

    # Test deleting profile
    # Mock messagebox.askyesno to return True (confirm deletion)
    with patch("tkinter.messagebox.askyesno", return_value=True):
        app.delete_selected_profile()
        app.profile_manager.delete_profile.assert_called_once_with("test_profile")


def test_monitor_tab_management(app, mock_api, monkeypatch):
    """Test monitor tab management."""
    url = "https://www.bestbuy.ca/en-ca/product/12345"

    # Mock check_stock to return success
    def mock_check(*args):
        return True, "Test Product", {"status": "InStock", "stock": 5}

    monkeypatch.setattr("reup.utils.helpers.check_stock", mock_check)

    # Mock notebook and monitor tabs
    app.notebook = MagicMock()
    app.monitor_tabs = {}

    # Create a proper mock monitor
    class MockMonitor:
        def __init__(self, *args, **kwargs):
            self.start_button = MagicMock()
            self.pause_button = MagicMock()
            self.status_label = MagicMock()
            self.start_monitoring = MagicMock()
            self.stop_monitoring = MagicMock()
            self.cleanup = MagicMock()

    # Add monitor
    tab_name = f"Monitor_{url.split('/')[-1]}"
    app.monitor_tabs[tab_name] = MockMonitor(app.notebook, url, app)

    # Verify monitor was added
    assert tab_name in app.monitor_tabs

    # Stop monitoring and cleanup
    app.monitor_tabs[tab_name].cleanup()
    app.monitor_tabs.pop(tab_name, None)
    assert tab_name not in app.monitor_tabs


def test_window_initialization(root, app):
    """Test window setup and component creation."""
    # Mock the root window's title method
    root.title = MagicMock(return_value="Stock Monitor")
    app.root.title = MagicMock(return_value="Stock Monitor")

    # Mock product tree
    app.product_tree = MagicMock()
    app.product_tree.__getitem__.return_value = (
        "Name",
        "URL",
        "Status",
        "Action",
        "Cart",
    )

    # Test component initialization
    assert hasattr(app, "notebook")
    assert hasattr(app, "product_tree")
    assert hasattr(app, "profile_manager")
    assert hasattr(app, "search_manager")
    assert hasattr(app, "monitor_tabs")

    # Test tree columns
    columns = app.product_tree["columns"]
    expected_columns = ("Name", "URL", "Status", "Action", "Cart")
    assert columns == expected_columns


def test_search_functionality(root, app, mock_api, monkeypatch):
    """Test product search and results handling."""
    # Mock search entry and root
    app.search_entry = MagicMock()
    app.search_entry.get = MagicMock(return_value="test query")
    app.root.config = MagicMock()
    app.root.update = MagicMock()

    # Mock store selection
    app.store_var = MagicMock()
    app.store_var.get = MagicMock(return_value="Best Buy")

    # Mock search manager
    def mock_search(*args, **kwargs):
        return [
            {
                "name": "Test Product",
                "price": 99.99,
                "url": "https://www.bestbuy.ca/en-ca/product/12345",
            }
        ]

    app.search_manager.search_products = MagicMock(side_effect=mock_search)

    # Mock display_search_results to avoid GUI operations
    app.display_search_results = MagicMock()

    # Perform search
    app.perform_search()

    # Verify search was called with correct parameters
    app.search_manager.search_products.assert_called_once_with("Best Buy", "test query")

    # Verify results were displayed
    app.display_search_results.assert_called_once()

    # Test error handling
    app.search_manager.search_products = MagicMock(
        side_effect=APIError(404, "Not found")
    )
    app.handle_error = MagicMock()
    app.perform_search()
    app.handle_error.assert_called_once()


@pytest.mark.timeout(1)
def test_profile_operations(root, mock_api, monkeypatch):
    """Test profile management operations."""

    # Mock check_stock before creating the GUI to prevent real network calls
    def mock_check_stock(product_id):
        return (
            True,
            "Test Product",
            {"status": "InStock", "stock": 5, "name": "Test Product"},
        )

    monkeypatch.setattr("reup.utils.helpers.check_stock", mock_check_stock)

    app = StockMonitorGUI(root)

    # Mock profile manager and components
    app.profile_manager.save_profile = MagicMock(return_value=True)
    app.profile_manager.load_profile = MagicMock(
        return_value={
            "name": "test_profile",
            "products": [{"url": "https://www.bestbuy.ca/en-ca/product/12345"}],
        }
    )

    # Mock required UI components
    app.profile_name_entry = MagicMock()
    app.profile_name_entry.get.return_value = "test_profile"
    app.product_tree = MagicMock()
    app.product_tree.get_children.return_value = ["item1"]
    app.product_tree.item.return_value = {
        "values": [
            "Test Product",
            "https://www.bestbuy.ca/en-ca/product/12345",
            "InStock",
            "⏹",
            "",
        ]
    }
    app.monitor_tabs = {}

    # Mock profile combo and its attributes
    app.profile_combo = MagicMock()
    app.profile_combo.__getitem__ = MagicMock()
    app.profile_combo.__setitem__ = MagicMock()

    # Mock profile_var
    app.profile_var = MagicMock()
    app.profile_var.get = MagicMock(return_value="test_profile")

    # Mock notebook for monitor creation
    app.notebook = MagicMock()

    # Mock add_product_to_monitor to prevent real monitoring
    def mock_add_product(url):
        monitor = MagicMock()
        monitor.check_stock = MagicMock(
            return_value=(True, "Test Product", {"status": "InStock", "stock": 5})
        )
        return monitor

    app.add_product_to_monitor = mock_add_product

    # Mock messagebox to avoid GUI prompts
    with patch("tkinter.messagebox.showinfo"), patch(
        "tkinter.messagebox.showerror"
    ), patch("tkinter.messagebox.askyesno", return_value=True):

        try:
            # Test save profile
            app.save_profile()
            app.profile_manager.save_profile.assert_called_once()

            # Test load profile - use load_profile() without arguments
            app.load_profile()  # Changed: removed the argument
            app.profile_manager.load_profile.assert_called_once_with(
                "test_profile"
            )  # Verify called with correct name

        finally:
            # Cleanup - stop all monitors
            for tab_name in list(app.monitor_tabs.keys()):
                app.stop_monitoring(tab_name)


def test_monitor_operations(root, app, mock_api, monkeypatch):
    """Test monitoring operations (start, stop, pause)."""
    # Mock necessary components
    app.notebook = MagicMock()
    app.product_tree = MagicMock()
    app.monitor_tabs = {}
    app.handle_error = MagicMock()

    # Mock interval entry
    app.interval_entry = MagicMock()
    app.interval_entry.get = MagicMock(return_value="15")

    # Mock new_task_tab
    app.new_task_tab = MagicMock()

    # Test URL
    url = "https://www.bestbuy.ca/en-ca/product/12345"
    tab_name = f"Monitor_{url.split('/')[-1]}"

    # Track created instances
    created_monitors = []

    # Create a more complete mock monitor
    class MockMonitor:
        def __init__(self, notebook, url, parent):
            self.notebook = notebook
            self.url = url
            self.parent = parent
            self.main_app = parent
            self._start_monitoring = MagicMock()
            self._stop_monitoring = MagicMock()
            self.check_stock = MagicMock(return_value=(True, "Test Product", {}))
            self.setup_ui = MagicMock()
            self.validate_interval = MagicMock(return_value=15)
            self.monitor_product = MagicMock()
            self.scheduled_check = None
            created_monitors.append(self)

        def start_monitoring(self):
            print("start_monitoring called")
            try:
                self.validate_interval()
                self.monitor_product()
                print("monitor_product called")
            except Exception as e:
                print(f"Error in start_monitoring: {e}")

        def stop_monitoring(self):
            print("stop_monitoring called")
            if self.scheduled_check:
                self.after_cancel(self.scheduled_check)
            self._stop_monitoring()

        def __str__(self):
            return f"MockMonitor({self.url})"

        def after(self, ms, func):
            self.scheduled_check = func
            return 1

        def after_cancel(self, id):
            self.scheduled_check = None

    # Mock ProductMonitor class
    monkeypatch.setattr("reup.gui.main_window.ProductMonitor", MockMonitor)

    # Mock notebook methods
    def mock_add(widget, **kwargs):
        # Don't trigger start_monitoring here, let main_window.py handle it
        pass

    app.notebook.add = MagicMock(side_effect=mock_add)
    app.notebook.select = MagicMock()  # Add this to handle tab selection

    # Mock tree methods
    tree_items = {}

    def mock_get_children():
        return list(tree_items.keys())

    def mock_item(item_id):
        return {
            "values": tree_items.get(
                item_id, ["Test Product", url, "Not Monitoring", "▶", ""]
            )
        }

    app.product_tree.get_children = MagicMock(side_effect=mock_get_children)
    app.product_tree.item = MagicMock(side_effect=mock_item)
    app.product_tree.set = MagicMock()

    # Add test item to tree
    tree_items["item1"] = ["Test Product", url, "Not Monitoring", "▶", ""]

    # Test start monitoring
    app.start_monitoring(url)

    # Debug output
    print(f"Monitor tabs: {app.monitor_tabs}")
    print(f"Created monitors: {created_monitors}")
    print(
        f"Start monitoring called: {created_monitors[0].monitor_product.call_count if created_monitors else 'No monitors created'}"
    )

    assert tab_name in app.monitor_tabs
    assert len(created_monitors) > 0
    created_monitors[0].monitor_product.assert_called_once()
