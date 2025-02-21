import pytest
from pathlib import Path
import sys
import tkinter as tk
from unittest.mock import MagicMock, patch
from tests.test_helpers import TestMonitor

# Add project root to Python path for tests
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import from reup package
from reup.gui.main_window import StockMonitorGUI


class MockVariable:
    """Mock base class for tkinter variables."""

    _default = ""

    def __init__(self, master=None, value=None, name=None):
        self._master = master
        self._name = name
        self._value = value if value is not None else self._default
        self.trace_info = {}

    def get(self):
        return self._value

    def set(self, value):
        self._value = value
        self._notify_traces()

    def trace_add(self, mode, callback):
        if mode not in self.trace_info:
            self.trace_info[mode] = []
        self.trace_info[mode].append(callback)

    def trace_remove(self, mode, cbname):
        if mode in self.trace_info and cbname in self.trace_info[mode]:
            self.trace_info[mode].remove(cbname)

    def _notify_traces(self):
        for mode, callbacks in self.trace_info.items():
            for cb in callbacks:
                cb()


class MockStringVar(MockVariable):
    """Mock StringVar."""

    _default = ""


class MockWidget:
    """Base class for mock widgets."""

    def __init__(self, master=None, **kw):
        self.master = master
        self.tk = master.tk if master else None
        self._w = f".{kw.get('name', self.__class__.__name__.lower())}"
        self.children = {}
        self._last_child_ids = {}  # Add this for tkinter widget naming
        self.configure = MagicMock()
        self.config = self.configure  # Add config as alias for configure
        self.pack = MagicMock()
        self.grid = MagicMock()
        self.bind = MagicMock()

        # Store widget options
        self._options = kw

        # Add after methods
        self.after = self.master.after if self.master else MagicMock()
        self.after_cancel = self.master.after_cancel if self.master else MagicMock()

        # Add view methods for scrolling
        self.yview = MagicMock()
        self.xview = MagicMock()

    def _get_options(self):
        """Get widget configuration options."""
        return self._options

    def _register(self, widget):
        """Register a child widget."""
        name = widget.__class__.__name__.lower()
        if name not in self._last_child_ids:
            self._last_child_ids[name] = 0
        self._last_child_ids[name] += 1
        widget._w = f"{self._w}.{name}{self._last_child_ids[name]}"
        self.children[widget._w] = widget


class MockEntry(MockWidget):
    """Mock Entry widget."""

    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)
        self._value = "15"  # Default interval value

    def get(self):
        return self._value

    def delete(self, first, last=None):
        self._value = ""

    def insert(self, index, string):
        self._value = string


class MockTk:
    """Mock Tk window."""

    def __init__(self):
        self.calls = []
        self.protocol_handlers = {}

        # Add tk interpreter mock
        self.tk = MagicMock()
        self.tk.call = MagicMock(return_value=None)
        self.tk.getvar = MagicMock(return_value="")
        self.tk.splitlist = MagicMock(return_value=[])
        self.tk.wantobjects = True

        # Add widget creation methods
        self.createcommand = MagicMock()
        self.deletecommand = MagicMock()
        self.eval = MagicMock(return_value="")

        # Add widget attributes
        self._w = "."
        self._last_child_ids = {}
        self._after_ids = {}
        self._after_counter = 0

        # Add children tracking
        self.children = {}  # Required by tkinter for widget hierarchy

    def title(self, title_str):
        self.calls.append(("title", title_str))

    def geometry(self, geometry_str):
        self.calls.append(("geometry", geometry_str))

    def minsize(self, width, height):
        self.calls.append(("minsize", width, height))

    def configure(self, **kwargs):
        self.calls.append(("configure", kwargs))

    def resizable(self, width, height):
        self.calls.append(("resizable", width, height))

    def grid_rowconfigure(self, row, **kwargs):
        self.calls.append(("grid_rowconfigure", row, kwargs))

    def grid_columnconfigure(self, col, **kwargs):
        self.calls.append(("grid_columnconfigure", col, kwargs))

    def protocol(self, name, handler):
        self.protocol_handlers[name] = handler
        self.calls.append(("protocol", name, handler))

    def destroy(self):
        self.calls.append(("destroy",))

    def after(self, ms, func=None, *args):
        """Mock the after method."""
        self._after_counter += 1
        after_id = f"after#{self._after_counter}"
        if func:
            self._after_ids[after_id] = (func, args)
            # Execute immediately in tests
            func(*args)
        return after_id

    def after_cancel(self, after_id):
        """Mock the after_cancel method."""
        if after_id in self._after_ids:
            del self._after_ids[after_id]

    def winfo_id(self):
        return 1

    def _root(self):
        """Return the root window."""
        return self

    def _options(self, cnf):
        """Convert options dict to tcl format."""
        opts = []
        for k, v in cnf.items():
            opts.append(f"-{k}")
            opts.append(str(v))
        return tuple(opts)


class MockTreeview(MockWidget):
    """Mock Treeview widget."""

    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)
        self._items = {}
        self._columns = {}
        self._headings = {}

    def insert(self, parent, index, **kw):
        item_id = f"I{len(self._items)}"
        self._items[item_id] = kw
        return item_id

    def get_children(self, item=None):
        return list(self._items.keys())

    def item(self, item_id, **kw):
        if kw:  # Setting values
            self._items[item_id].update(kw)
        return self._items[item_id]

    def delete(self, *items):
        for item in items:
            if item in self._items:
                del self._items[item]

    def column(self, column_id, **kw):
        """Configure column properties."""
        if column_id not in self._columns:
            self._columns[column_id] = {}
        self._columns[column_id].update(kw)

    def heading(self, column_id, **kw):
        """Configure column heading."""
        if column_id not in self._headings:
            self._headings[column_id] = {}
        self._headings[column_id].update(kw)


class MockNotebook(MockWidget):
    """Mock Notebook widget."""

    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)
        self._tabs = {}
        self._current = None

    def add(self, child, **kw):
        tab_id = f"t{len(self._tabs)}"
        self._tabs[tab_id] = {"widget": child, "options": kw}
        if not self._current:
            self._current = tab_id

    def select(self, tab_id=None):
        if tab_id is None:
            return self._current
        self._current = tab_id

    def forget(self, tab):
        for tab_id, info in self._tabs.items():
            if info["widget"] == tab:
                del self._tabs[tab_id]
                break


class MockTtkEntry(MockWidget):
    """Mock ttk.Entry widget."""

    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)
        self._value = ""

    def get(self):
        return self._value

    def delete(self, first, last=None):
        self._value = ""

    def insert(self, index, string):
        self._value = string


class MockScrollbar(MockWidget):
    """Mock Scrollbar widget."""

    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)
        self.set = MagicMock()  # Add set method for scrollbar


class MockText(MockWidget):
    """Mock Text widget."""

    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)
        self._content = ""
        self._mark = "1.0"

    def insert(self, index, text):
        self._content += text

    def delete(self, start, end=None):
        self._content = ""

    def get(self, start, end=None):
        return self._content

    def see(self, index):
        pass

    def index(self, index):
        return self._mark


@pytest.fixture
def mock_ttk():
    """Create mock ttk components."""
    mock = MagicMock()

    class MockStyle:
        def __init__(self, master=None):
            self.master = master
            self.configure = MagicMock()
            self.layout = MagicMock()
            self.tk = master.tk if master else MagicMock()
            self.tk.call = MagicMock(return_value=None)

    class MockTtkWidget(MockWidget):
        def __init__(self, master=None, **kw):
            super().__init__(master, **kw)
            self.configure = MagicMock()
            self.pack = MagicMock()
            self.grid = MagicMock()
            self.bind = MagicMock()

    mock.Style = MockStyle
    mock.Frame = lambda *args, **kwargs: MockTtkWidget(*args, **kwargs)
    mock.LabelFrame = lambda *args, **kwargs: MockTtkWidget(*args, **kwargs)
    mock.Label = lambda *args, **kwargs: MockTtkWidget(*args, **kwargs)
    mock.Button = lambda *args, **kwargs: MockTtkWidget(*args, **kwargs)
    mock.Entry = lambda *args, **kwargs: MockTtkEntry(*args, **kwargs)
    mock.Scrollbar = lambda *args, **kwargs: MockScrollbar(
        *args, **kwargs
    )  # Use MockScrollbar
    mock.Notebook = lambda *args, **kwargs: MockNotebook(*args, **kwargs)
    mock.Treeview = lambda *args, **kwargs: MockTreeview(*args, **kwargs)
    mock.Combobox = lambda *args, **kwargs: MockTtkWidget(*args, **kwargs)
    return mock


@pytest.fixture
def mock_tk():
    """Mock Tk and ttk to avoid actual window creation."""
    with patch("tkinter.Tk") as mock_tk, patch(
        "tkinter.ttk.Notebook"
    ) as mock_notebook, patch("tkinter.ttk.Frame") as mock_frame:

        # Add after_cancel method to mock
        mock_tk.after_cancel = MagicMock()
        mock_tk.after = MagicMock()

        yield {"tk": mock_tk, "notebook": mock_notebook, "frame": mock_frame}


@pytest.fixture
def root(monkeypatch, mock_tk, mock_ttk):
    """Create a mock root window for testing."""
    # Mock tkinter internals
    monkeypatch.setattr("tkinter.Tk", mock_tk["tk"])
    monkeypatch.setattr("tkinter.ttk", mock_ttk)
    monkeypatch.setattr("tkinter._default_root", None)
    monkeypatch.setattr("tkinter._support_default_root", True)
    monkeypatch.setattr("tkinter.StringVar", mock_tk["tk"].StringVar)
    monkeypatch.setattr("tkinter.messagebox.Message", MagicMock())

    # Create root and set as default
    root = mock_tk["tk"]
    monkeypatch.setattr("tkinter._default_root", root)
    return root


@pytest.fixture
def mock_api():
    """Mock API responses for testing."""
    return {
        "products": [
            {
                "name": "Test Product",
                "regularPrice": 99.99,
                "sku": "12345",
                "thumbnailImage": "http://example.com/image.jpg",
                "availability": {
                    "isAvailableOnline": True,
                    "onlineAvailability": "InStock",
                    "onlineAvailabilityCount": 5,
                    "buttonState": "AddToCart",
                },
            }
        ]
    }


@pytest.fixture
def app(root, monkeypatch, mock_ttk):
    """Create a test instance of the main application."""
    # Mock ttk.Style before creating app
    monkeypatch.setattr("tkinter.ttk.Style", mock_ttk.Style)

    from reup.gui.main_window import StockMonitorGUI

    with patch("tkinter._get_default_root", return_value=root):
        app = StockMonitorGUI(root)
    return app


@pytest.fixture
def tmp_profiles_dir(tmp_path):
    """Create a temporary profiles directory."""
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    return profiles_dir


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


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return {"check_interval": 15, "notification_timeout": 10, "max_products": 100}


@pytest.fixture
def mock_profile():
    """Mock profile data for testing"""
    return {
        "name": "test_profile",
        "products": [
            {"url": "https://example.com/product/1"},
            {"url": "https://example.com/product/2"},
        ],
    }


@pytest.fixture(autouse=True)
def debug_test_failure(request):
    """Print extra info on test failures."""
    yield
    if request.session.testsfailed:
        print("\nTest failed! Current test:", request.node.name)
        print("Function:", request.function.__name__)
        print("File:", request.fspath)
        if hasattr(request.node, "rep_call"):
            print("Error:", request.node.rep_call.longrepr)
