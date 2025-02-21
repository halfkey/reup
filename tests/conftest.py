import pytest
from pathlib import Path
import sys
import tkinter as tk
from unittest.mock import MagicMock, patch
from tests.fixtures.monitor_fixtures import TestMonitor

# Add project root to Python path for tests
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

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
        self.tk = master.tk if master else MagicMock()
        self._w = "widget"
        self.configure = MagicMock()
        self.config = self.configure
        self.grid = MagicMock()
        self.pack = MagicMock()
        self.destroy = MagicMock()
        self.bind = MagicMock()
        self.unbind = MagicMock()
        self.update = MagicMock()
        self.children = {}

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
    def __init__(self):
        # Basic window attributes
        self.geometry = MagicMock()
        self.minsize = MagicMock()
        self.title = MagicMock()
        self.configure = MagicMock()
        self.grid_rowconfigure = MagicMock()
        self.grid_columnconfigure = MagicMock()
        self.protocol = MagicMock()
        self.resizable = MagicMock()
        self.log_message = MagicMock()
        
        # Add tk interpreter
        self.tk = MagicMock()
        self.tk.call = MagicMock()
        self.tk.getvar = MagicMock()
        self.tk.setvar = MagicMock()
        self.tk.createcommand = MagicMock()
        self.tk.deletecommand = MagicMock()
        self.tk.eval = MagicMock()
        self.tk.wantobjects = True
        self._w = "."
        
        # Add widget tracking
        self._last_child_ids = {}
        self.children = {}
        
        # Add after methods
        self.after_ids = {}
        self.after_counter = 0
        
        # Add style support
        self.style = MagicMock()
        self.style.configure = MagicMock()
        self.style.map = MagicMock()
        
    def after(self, ms, func=None, *args):
        """Mock the after method."""
        self.after_counter += 1
        after_id = f"after#{self.after_counter}"
        if func:
            self.after_ids[after_id] = (func, args)
        return after_id
        
    def after_cancel(self, after_id):
        """Mock the after_cancel method."""
        if after_id in self.after_ids:
            del self.after_ids[after_id]
            
    def _register_child(self, widget):
        """Register a child widget."""
        name = widget.__class__.__name__.lower()
        if name not in self._last_child_ids:
            self._last_child_ids[name] = 0
        self._last_child_ids[name] += 1
        widget._w = f"{self._w}.{name}{self._last_child_ids[name]}"
        self.children[widget._w] = widget

class MockTreeview(MagicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add required Treeview methods
        self.yview = MagicMock()
        self.heading = MagicMock()
        self.column = MagicMock()
        self.insert = MagicMock()
        self.delete = MagicMock()
        self.get_children = MagicMock(return_value=[])
        self.item = MagicMock(return_value={'values': ['', '', '', '', '']})
        self.selection = MagicMock(return_value=[])
        self.set = MagicMock()
        self.see = MagicMock()
        self.configure = MagicMock()
        self.config = MagicMock()

class MockNotebook(MockWidget):
    """Mock Notebook widget."""
    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)
        self._tabs = {}
        self._current = None
        
    def add(self, child, **kw):
        tab_id = f"t{len(self._tabs)}"
        self._tabs[tab_id] = {'widget': child, 'options': kw}
        if not self._current:
            self._current = tab_id
            
    def select(self, tab_id=None):
        if tab_id is None:
            return self._current
        self._current = tab_id
        
    def forget(self, tab):
        for tab_id, info in self._tabs.items():
            if info['widget'] == tab:
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
        self.set = MagicMock()
        self.get = MagicMock()

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
    """Mock ttk widgets."""
    mock = MagicMock()
    
    class MockStyle:
        def __init__(self, master=None):
            self.master = master
            self.configure = MagicMock()
            self.map = MagicMock()
            
    mock.Style = MockStyle
    mock.Frame = lambda *args, **kwargs: MockWidget(*args, **kwargs)
    mock.Label = lambda *args, **kwargs: MockWidget(*args, **kwargs)
    mock.Entry = MockTtkEntry
    mock.Button = lambda *args, **kwargs: MockWidget(*args, **kwargs)
    mock.Notebook = MockNotebook
    mock.Treeview = MockTreeview
    mock.Scrollbar = MockScrollbar
    return mock

@pytest.fixture
def mock_tk(monkeypatch):
    """Mock tkinter components."""
    monkeypatch.setattr('tkinter.ttk.Treeview', MockTreeview)
    mock = MagicMock()
    
    class MockTk:
        def __init__(self):
            # Basic window attributes
            self.geometry = MagicMock()
            self.minsize = MagicMock()
            self.title = MagicMock()
            self.configure = MagicMock()
            self.grid_rowconfigure = MagicMock()
            self.grid_columnconfigure = MagicMock()
            self.protocol = MagicMock()
            self.resizable = MagicMock()
            self.log_message = MagicMock()
            
            # Add tk interpreter
            self.tk = MagicMock()
            self.tk.call = MagicMock()
            self.tk.getvar = MagicMock()
            self.tk.setvar = MagicMock()
            self.tk.createcommand = MagicMock()
            self.tk.deletecommand = MagicMock()
            self.tk.eval = MagicMock()
            self.tk.wantobjects = True
            self._w = "."
            
            # Add widget tracking
            self._last_child_ids = {}
            self.children = {}
            
            # Add after methods
            self.after_ids = {}
            self.after_counter = 0
            
            # Add style support
            self.style = MagicMock()
            self.style.configure = MagicMock()
            self.style.map = MagicMock()
            
        def after(self, ms, func=None, *args):
            """Mock the after method."""
            self.after_counter += 1
            after_id = f"after#{self.after_counter}"
            if func:
                self.after_ids[after_id] = (func, args)
            return after_id
            
        def after_cancel(self, after_id):
            """Mock the after_cancel method."""
            if after_id in self.after_ids:
                del self.after_ids[after_id]
            
        def _register_child(self, widget):
            """Register a child widget."""
            name = widget.__class__.__name__.lower()
            if name not in self._last_child_ids:
                self._last_child_ids[name] = 0
            self._last_child_ids[name] += 1
            widget._w = f"{self._w}.{name}{self._last_child_ids[name]}"
            self.children[widget._w] = widget
    
    mock.Tk = MockTk
    mock.Frame = lambda *args, **kwargs: MockWidget(*args, **kwargs)
    mock.Label = lambda *args, **kwargs: MockWidget(*args, **kwargs)
    mock.Button = lambda *args, **kwargs: MockWidget(*args, **kwargs)
    mock.Entry = MockEntry
    mock.Scrollbar = MockScrollbar
    mock.Text = lambda *args, **kwargs: MockText(*args, **kwargs)
    mock.StringVar = MockStringVar
    
    # Constants
    mock.END = 'end'
    mock.BOTH = 'both'
    mock.X = 'x'
    mock.Y = 'y'
    mock.LEFT = 'left'
    mock.RIGHT = 'right'
    mock.TOP = 'top'
    mock.BOTTOM = 'bottom'
    mock.NSEW = 'nsew'
    return mock

@pytest.fixture
def root(monkeypatch, mock_tk, mock_ttk):
    """Create a mock root window for testing."""
    # Mock tkinter internals
    monkeypatch.setattr('tkinter.Tk', mock_tk.Tk)
    monkeypatch.setattr('tkinter.ttk', mock_ttk)
    monkeypatch.setattr('tkinter._default_root', None)
    monkeypatch.setattr('tkinter._support_default_root', True)
    monkeypatch.setattr('tkinter.StringVar', mock_tk.StringVar)
    monkeypatch.setattr('tkinter.messagebox.Message', MagicMock())
    
    # Create root and set as default
    root = mock_tk.Tk()
    monkeypatch.setattr('tkinter._default_root', root)
    return root

@pytest.fixture
def mock_api():
    """Mock API responses for testing."""
    return {
        'products': [{
            'name': 'Test Product',
            'regularPrice': 99.99,
            'sku': '12345',
            'thumbnailImage': 'http://example.com/image.jpg',
            'availability': {
                'isAvailableOnline': True,
                'onlineAvailability': 'InStock',
                'onlineAvailabilityCount': 5,
                'buttonState': 'AddToCart'
            }
        }]
    }

@pytest.fixture
def app(root, monkeypatch, mock_ttk):
    """Create a test instance of the main application."""
    # Mock ttk.Style before creating app
    monkeypatch.setattr('tkinter.ttk.Style', mock_ttk.Style)
    
    from reup.gui.main_window import StockMonitorGUI
    with patch('tkinter._get_default_root', return_value=root):
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
    return {
        'check_interval': 15,
        'notification_timeout': 10,
        'max_products': 100
    }

@pytest.fixture
def mock_profile():
    """Mock profile data for testing"""
    return {
        'name': 'test_profile',
        'products': [
            {'url': 'https://example.com/product/1'},
            {'url': 'https://example.com/product/2'}
        ]
    } 