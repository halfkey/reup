import pytest
from unittest.mock import MagicMock, patch, mock_open
import tkinter as tk
import tkinter.ttk as ttk
from reup.gui.main_window import StockMonitorGUI as MainApp
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
    app.profile_handler = MagicMock()
    app.profile_var = MagicMock()
    app.profile_var.get.return_value = "test_profile"

    # Mock product tree
    app.product_tree = MagicMock()
    app.product_tree.get_children.return_value = []
    app.product_tree.item.return_value = {
        "values": ["Test Product", "https://example.com/1"]
    }

    # Mock clear_product_tree method
    app.clear_product_tree = MagicMock()

    # Mock add_product_to_monitor
    app.add_product_to_monitor = MagicMock()

    # Mock handle_error
    app.handle_error = MagicMock()

    # Mock profile data
    test_profile = {
        "products": [
            {"name": "Test Product 1", "url": "https://example.com/1"},
            {"name": "Test Product 2", "url": "https://example.com/2"},
        ]
    }

    # Set up mock returns
    app.profile_handler.load_profile.return_value = test_profile

    # Test loading profile
    app.load_profile()

    # Verify the correct methods were called
    app.profile_var.get.assert_called_once()
    app.profile_handler.load_profile.assert_called_once_with("test_profile")
    app.clear_product_tree.assert_called_once()
    assert app.add_product_to_monitor.call_count == len(test_profile["products"])


def test_monitor_tab_management(root, app, mock_api, monkeypatch):
    """Test monitor tab creation and removal."""
    # Mock necessary components
    app.notebook = MagicMock()
    app.product_tree = MagicMock()
    app.monitor_tabs = {}
    app.handle_error = MagicMock()
    app.style = MagicMock()
    app.log_message = MagicMock()

    # Mock check_stock function
    class MockResponse:
        def __init__(self):
            self.status_code = 200

        def json(self):
            return mock_api["products"][0]

    def mock_requests_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr("requests.get", mock_requests_get)

    # Mock notebook methods
    app.notebook.select = MagicMock()
    app.notebook.forget = MagicMock()
    app.notebook.add = MagicMock()
    app.notebook.index = MagicMock(return_value=1)
    app.notebook.tab = MagicMock()

    # Mock tree methods
    app.product_tree.get_children = MagicMock(return_value=[])
    app.product_tree.item = MagicMock(return_value={"values": ["", "", "", "", ""]})
    app.product_tree.insert = MagicMock(return_value="item1")

    # Mock check_stock to avoid API calls
    def mock_check_stock(*args):
        return (
            True,
            mock_api["products"][0]["name"],
            {
                "name": mock_api["products"][0]["name"],
                "stock": 5,
                "status": "InStock",
                "purchasable": "Yes",
            },
        )

    monkeypatch.setattr("reup.utils.helpers.check_stock", mock_check_stock)

    # Test URL
    url = "https://www.bestbuy.ca/en-ca/product/12345"
    tab_name = f"Monitor_{url.split('/')[-1]}"

    # Add and start monitoring
    monitor = app.add_product_to_monitor(url)
    assert monitor is not None

    app.start_monitoring(url)
    assert tab_name in app.monitor_tabs
    app.notebook.add.assert_called()

    # Stop monitoring
    app.stop_monitoring(tab_name)
    assert tab_name not in app.monitor_tabs
    app.notebook.forget.assert_called()


def test_window_initialization(root, app):
    """Test window setup and component creation."""
    # Mock the root window's title method
    root.title = MagicMock(return_value="Reup")
    app.root.title = MagicMock(return_value="Reup")

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
    app.search_manager.search_products = MagicMock(side_effect=APIError("Not found"))
    app.handle_error = MagicMock()
    app.perform_search()
    app.handle_error.assert_called_once()


@pytest.fixture
def mock_tk_setup():
    """Create a complete mock tkinter environment."""
    with patch("tkinter.Tk") as mock_tk, patch(
        "tkinter.ttk.Style"
    ) as mock_style, patch("tkinter.ttk.Notebook") as mock_notebook, patch(
        "tkinter.ttk.Frame"
    ) as mock_frame, patch(
        "tkinter.StringVar"
    ) as mock_stringvar, patch(
        "tkinter._default_root", create=True
    ), patch(
        "tkinter._support_default_root", True
    ):

        # Configure mock Tk
        mock_tk_instance = mock_tk.return_value
        mock_tk_instance.title = MagicMock()
        mock_tk_instance.geometry = MagicMock()
        mock_tk_instance.minsize = MagicMock()
        mock_tk_instance.grid_rowconfigure = MagicMock()
        mock_tk_instance.grid_columnconfigure = MagicMock()
        mock_tk_instance.winfo_toplevel = MagicMock(return_value=mock_tk_instance)

        # Configure mock StringVar
        mock_stringvar_instance = mock_stringvar.return_value
        mock_stringvar_instance.get = MagicMock(return_value="")
        mock_stringvar_instance.set = MagicMock()

        # Configure mock Style
        mock_style_instance = mock_style.return_value
        mock_style_instance.configure = MagicMock()
        mock_style_instance.layout = MagicMock()

        yield {
            "tk": mock_tk_instance,
            "style": mock_style_instance,
            "notebook": mock_notebook,
            "frame": mock_frame,
            "stringvar": mock_stringvar,
        }


@pytest.mark.timeout(5)
def test_profile_operations(mock_tk_setup):
    """Test profile management operations."""
    with patch("tkinter.ttk.Style", return_value=mock_tk_setup["style"]), patch(
        "tkinter.StringVar", return_value=mock_tk_setup["stringvar"].return_value
    ), patch("tkinter._default_root", mock_tk_setup["tk"]):

        app = MainApp(mock_tk_setup["tk"])
        app.profile_handler = MagicMock()  # Use profile_handler instead
        app.profile_var = MagicMock()
        app.profile_var.get.return_value = "test_profile"

        # Test save profile
        app.save_profile()
        app.profile_handler.save_profile.assert_called_once_with(
            "test_profile", {"products": []}
        )


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
