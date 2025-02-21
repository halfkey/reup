"""Main GUI application for stock monitoring."""

from typing import Dict, Optional, List
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from ..config.constants import STORES, WINDOW_SIZE, DEFAULT_INTERVAL
from ..config.styles import STYLES, PRODUCT_COLUMNS
from ..managers.profile_manager import ProfileManager
from ..managers.search_manager import SearchManager
from ..core.product_monitor import ProductMonitor
from ..core.task_monitor import TaskMonitor
from ..core.profile_monitor import ProfileMonitor
from ..utils.exceptions import ProfileError, ProfileLoadError, APIError
import logging
from datetime import datetime
import requests
from pathlib import Path
from reup.managers.profile_handler import ProfileHandler

class StockMonitorGUI:
    """Main GUI application for stock monitoring."""
    
    def __init__(self, root=None):
        """Initialize the main window.
        
        Args:
            root: Optional tkinter root window. If None, creates a new one.
        """
        self.root = root if root is not None else tk.Tk()
        self.root.title("Reup")
        
        # Set window size
        self.root.geometry(f"{WINDOW_SIZE[0]}x{WINDOW_SIZE[1]}")
        self.root.minsize(WINDOW_SIZE[0], WINDOW_SIZE[1])
        
        self.search_results = {}
        self.setup_root_window()
        self.initialize_managers()
        self.setup_styles()
        self.create_main_interface()
        self.setup_logging()
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.profile_handler = ProfileHandler()
        
    def setup_root_window(self):
        """Configure the root window."""
        self.root.configure(bg='#f0f0f0')
        self.root.resizable(True, True)
        
        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
    def initialize_managers(self):
        """Initialize component managers."""
        self.profile_manager = ProfileManager()
        self.search_manager = SearchManager()
        self.monitor_tabs = {}
        
    def setup_styles(self):
        """Configure ttk styles."""
        self.style = ttk.Style()
        for style_name, style_config in STYLES.items():
            self.style.configure(style_name, **style_config)
            
        # Configure tabs
        self.style.configure('TNotebook.Tab', padding=[15, 5])
        self.style.configure('TNotebook', tabmargins=[5, 5, 2, 0])
        
        # Configure plus tab style
        self.style.configure('Plus.TFrame', background='#f0f0f0')
        
        # Configure additional styles
        self.style.configure('Header.TLabel', 
                           font=('Arial', 12, 'bold'),
                           background='#f0f0f0')
        self.style.configure('Status.TLabel',
                           font=('Arial', 10),
                           background='#f0f0f0') 

    def create_main_interface(self):
        """Create the main interface components."""
        self.main_container = ttk.Frame(self.root, style='Custom.TFrame')
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create main dashboard tab
        self.setup_tab = ttk.Frame(self.notebook, style='Custom.TFrame')
        self.notebook.add(self.setup_tab, text="📋 Dashboard")
        
        # Create tab components
        self.create_profile_section()
        self.create_search_section()
        self.create_product_list()
        self.create_found_products_section()
        
        # Bind tab selection only
        self.notebook.bind('<<NotebookTabChanged>>', self.handle_tab_change)

    def create_profile_section(self):
        """Create profile management section."""
        frame = ttk.LabelFrame(self.setup_tab, text=" Profile Management ", style='Custom.TLabelframe')
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        profile_frame = ttk.Frame(frame, style='Custom.TFrame')
        profile_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Profile selection
        ttk.Label(profile_frame, text="Profile:").pack(side=tk.LEFT)
        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(
            profile_frame,
            textvariable=self.profile_var,
            state='readonly',
            width=20
        )
        self.profile_combo.pack(side=tk.LEFT, padx=5)
        
        # Profile buttons
        ttk.Button(
            profile_frame,
            text="Load",
            style='Custom.TButton',
            command=self.load_selected_profile
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            profile_frame,
            text="Save",
            style='Custom.TButton',
            command=self.save_current_profile
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            profile_frame,
            text="Delete",
            style='Custom.TButton',
            command=self.delete_selected_profile
        ).pack(side=tk.LEFT, padx=5)
        
        # Update profile list
        self.update_profile_list()

    def create_search_section(self):
        """Create product search section."""
        frame = ttk.LabelFrame(self.setup_tab, text=" Product Search ", style='Custom.TLabelframe')
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        search_frame = ttk.Frame(frame, style='Custom.TFrame')
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Store selection
        ttk.Label(search_frame, text="Store:").pack(side=tk.LEFT)
        self.store_var = tk.StringVar(value=list(STORES.keys())[0])
        store_combo = ttk.Combobox(
            search_frame,
            textvariable=self.store_var,
            values=list(STORES.keys()),
            state='readonly',
            width=15
        )
        store_combo.pack(side=tk.LEFT, padx=5)
        
        # Search entry
        self.search_entry = ttk.Entry(search_frame, width=40)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        # Bind Enter key to perform search
        self.search_entry.bind('<Return>', lambda e: self.perform_search())
        
        ttk.Button(
            search_frame,
            text="🔍 Search",
            style='Custom.TButton',
            command=self.perform_search
        ).pack(side=tk.LEFT, padx=5)

    def create_product_list(self):
        """Create the product list section."""
        # Product list frame
        product_frame = ttk.LabelFrame(self.setup_tab, text=" Products ", style='Custom.TLabelframe')
        product_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create buttons frame
        button_frame = ttk.Frame(product_frame, style='Custom.TFrame')
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Add Start Task button
        ttk.Button(
            button_frame,
            text="Start Task",
            style='Custom.TButton',
            command=self.start_task_monitoring
        ).pack(side=tk.LEFT, padx=5)
        
        # Add Clear All button
        ttk.Button(
            button_frame,
            text="Clear All",
            style='Custom.TButton',
            command=self.clear_product_tree
        ).pack(side=tk.LEFT, padx=5)
        
        # Create and configure product treeview
        self.product_tree = self.create_product_treeview(product_frame)

    def create_product_treeview(self, parent: ttk.Frame) -> ttk.Treeview:
        """Create and configure the product treeview."""
        # Create treeview with scrollbar
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create treeview with Name first (removed Cart column)
        tree = ttk.Treeview(
            tree_frame,
            columns=('Name', 'URL', 'Status', 'Action'),  # Removed 'Cart'
            show='headings',
            selectmode='browse',
            height=10
        )
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure scrollbar
        scrollbar.config(command=tree.yview)
        tree.config(yscrollcommand=scrollbar.set)
        
        # Configure columns
        tree.column('Name', width=200, anchor=tk.W)
        tree.column('URL', width=300, anchor=tk.W)
        tree.column('Status', width=150, anchor=tk.CENTER)
        tree.column('Action', width=50, anchor=tk.CENTER)
        
        # Configure headings
        tree.heading('Name', text='Product Name', anchor=tk.W)
        tree.heading('URL', text='Product URL', anchor=tk.W)
        tree.heading('Status', text='Status', anchor=tk.CENTER)
        tree.heading('Action', text='', anchor=tk.CENTER)
        
        # Bind click events
        tree.bind('<Double-1>', self.handle_tree_double_click)
        tree.bind('<Button-1>', self.handle_tree_click)
        
        return tree

    def handle_tab_change(self, event):
        """Handle tab change event."""
        # Implementation of handle_tab_change method
        pass

    def on_closing(self):
        """Handle window closing event."""
        try:
            # Stop all monitoring tabs
            for tab_name in list(self.monitor_tabs.keys()):
                try:
                    tab = self.monitor_tabs[tab_name]
                    if hasattr(tab, 'stop_monitoring'):
                        tab.stop_monitoring()
                except Exception as e:
                    logging.error(f"Error stopping monitor {tab_name}: {str(e)}")
            
            # Clear monitor tabs dictionary
            self.monitor_tabs.clear()
            
            logging.info("Application closed")
        finally:
            self.root.destroy()

    def save_current_profile(self):
        """Save current profile."""
        profile_name = self.profile_var.get()
        if not profile_name:
            profile_name = simpledialog.askstring("Save Profile", "Enter profile name:")
            if not profile_name:
                return
        
        try:
            # Get products from tree
            products = []
            for item in self.product_tree.get_children():
                values = self.product_tree.item(item)['values']
                products.append({
                    'name': values[0],
                    'url': values[1]
                })
            
            self.profile_handler.save_profile(profile_name, {'products': products})
            
            # Update profile list
            self.update_profile_list()
            self.profile_var.set(profile_name)
            
            messagebox.showinfo("Success", f"Profile '{profile_name}' saved successfully")
            
        except Exception as e:
            self.handle_error(e, "Save Profile Error")

    def load_selected_profile(self):
        """Load selected profile."""
        profile_name = self.profile_var.get()
        if not profile_name:
            return
        
        try:
            profile = self.profile_manager.load_profile(profile_name)
            
            # Get currently monitored URLs to avoid clearing them
            monitored_urls = set()
            for item in self.product_tree.get_children():
                values = self.product_tree.item(item)['values']
                if values[2] == 'Monitoring':  # Check if item is being monitored
                    monitored_urls.add(values[1])  # Add URL to monitored set
            
            # Clear only non-monitored items
            for item in self.product_tree.get_children():
                values = self.product_tree.item(item)['values']
                if values[1] not in monitored_urls:
                    self.product_tree.delete(item)
            
            # Add new products from profile if not already monitored
            for product in profile['products']:
                if product['url'] not in monitored_urls:
                    self.add_product_to_monitor(product['url'])
            
        except Exception as e:
            self.handle_error(f"Error loading profile: {e}")

    def delete_selected_profile(self):
        """Delete the selected profile."""
        profile_name = self.profile_var.get()
        if not profile_name:
            return
        
        try:
            self.profile_manager.delete_profile(profile_name)
            self.update_profile_list()  # Refresh the combo box
        except Exception as e:
            self.handle_error(e, "Delete Profile Error")

    def start_profile_monitoring(self):
        """Start monitoring for all products in the current profile."""
        profile_name = self.profile_var.get()
        if not profile_name:
            messagebox.showwarning("Warning", "Please select a profile first")
            return
        
        try:
            # Load the profile
            profile = self.profile_manager.load_profile(profile_name)
            
            # Start monitoring each product
            for product in profile['products']:
                url = product['url']
                # Create unique tab name
                tab_name = f"Monitor_{url.split('/')[-1]}"
                
                # Check if already monitoring
                if tab_name not in self.monitor_tabs:
                    # Create new monitor tab
                    monitor_tab = ProductMonitor(self.notebook, url, self)
                    self.monitor_tabs[tab_name] = monitor_tab
                    
                    # Add the new monitor tab (keeping + tab at the end)
                    self.add_monitor_tab(monitor_tab, f"⚪ {tab_name}")
                    monitor_tab.start_monitoring()
                
            messagebox.showinfo("Success", f"Started monitoring profile '{profile_name}'")
            
        except Exception as e:
            self.handle_error(e, "Start Profile Monitoring Error")

    def clear_setup_gui(self):
        """Clear setup GUI."""
        # Implementation of clear_setup_gui method
        pass

    def perform_search(self):
        """Perform product search and display results."""
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning("Search Error", "Please enter a search term")
            return
        
        try:
            # Show searching indicator
            self.root.config(cursor="wait")
            self.root.update()
            
            # Perform search
            results = self.search_manager.search_products(
                self.store_var.get(),
                query
            )
            
            # Format results for display
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'display_name': result['name'][:80] + '...' if len(result['name']) > 80 else result['name'],
                    'price': f"${result['price']:.2f}" if result['price'] else 'N/A',
                    'url': result['url']
                })
            
            # Display results
            if formatted_results:
                self.display_search_results(formatted_results)
            else:
                messagebox.showinfo("Search Results", "No products found")
            
        except APIError as e:
            self.handle_error(e, "Search Error")
        except Exception as e:
            self.handle_error(e, "Unexpected Error")
        finally:
            # Reset cursor
            self.root.config(cursor="")

    def start_task_monitoring(self):
        """Start monitoring all products in the list."""
        try:
            # Create sequential task name
            existing_tasks = [name for name in self.monitor_tabs.keys() if name.startswith('Task ')]
            next_num = 1
            while f"Task {next_num}" in existing_tasks:
                next_num += 1
            task_name = f"Task {next_num}"
            
            # Get all products that need monitoring
            products_to_monitor = []
            for item in self.product_tree.get_children():
                values = self.product_tree.item(item)['values']
                if values[3] == '▶':  # If not already monitoring
                    products_to_monitor.append(values[1])  # URL is second column
            
            if not products_to_monitor:
                messagebox.showinfo("Info", "No products to monitor")
                return
            
            # Create a single monitor tab for all products
            monitor_tab = TaskMonitor(self.notebook, products_to_monitor, self)
            self.monitor_tabs[task_name] = monitor_tab
            
            # Add the new monitor tab
            self.add_monitor_tab(monitor_tab, task_name)
            monitor_tab.start_monitoring()
            
            # Update status for all monitored products
            for item in self.product_tree.get_children():
                values = self.product_tree.item(item)['values']
                if values[1] in products_to_monitor:
                    self.product_tree.item(item, values=(
                        values[0],  # Name
                        values[1],  # URL
                        'Monitoring',
                        '⏹'  # Stop button
                    ))
            
            # Clear dashboard after starting task
            self.clear_dashboard()
            
        except Exception as e:
            self.handle_error(e, "Start Task Error")

    def clear_dashboard(self):
        """Clear all fields in the dashboard."""
        # Clear search entry
        if hasattr(self, 'search_entry'):
            self.search_entry.delete(0, tk.END)
        
        # Clear product tree
        if hasattr(self, 'product_tree'):
            for item in self.product_tree.get_children():
                self.product_tree.delete(item)
        
        # Clear profile selection
        if hasattr(self, 'profile_var'):
            self.profile_var.set('')

    def clear_product_tree(self):
        """Clear all products from the tree."""
        try:
            # Stop all monitoring first
            for tab_name in list(self.monitor_tabs.keys()):
                self.stop_monitoring(tab_name)
            
            # Clear the tree
            for item in self.product_tree.get_children():
                self.product_tree.delete(item)
            
        except Exception as e:
            self.handle_error(e, "Clear Products Error")

    def handle_tree_double_click(self, event):
        """Handle double click on tree item."""
        tree = event.widget
        item = tree.selection()[0]
        values = tree.item(item)['values']
        if values:
            url = values[1]  # URL is second column
            import webbrowser
            webbrowser.open(url)

    def handle_tree_click(self, event):
        """Handle single click on tree item."""
        tree = event.widget
        region = tree.identify_region(event.x, event.y)
        if region == "cell":
            column = tree.identify_column(event.x)
            item = tree.identify_row(event.y)
            if item:
                values = tree.item(item)['values']
                if values:
                    if column == "#4":  # Action column
                        url = values[1]  # URL is second column
                        if values[3] == '⏵':  # Start monitoring
                            self.start_monitoring(url)
                        else:  # Stop monitoring
                            tab_name = f"Monitor_{url.split('/')[-1]}"
                            self.stop_monitoring(tab_name)

    def handle_error(self, error: Exception, title: str = "Error"):
        """Handle and log errors."""
        message = str(error)
        logging.error(f"{title}: {message}")
        messagebox.showerror(title, message)

    def setup_logging(self):
        """Configure logging."""
        log_dir = Path(__file__).parent.parent.parent / 'data' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / 'reup.log'
        
        logging.basicConfig(
            filename=str(log_file),
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        ) 

    def display_search_results(self, results: List[Dict]):
        """Display search results in a new window."""
        # Create results window
        results_window = tk.Toplevel(self.root)
        results_window.title("Search Results")
        results_window.geometry("800x600")
        
        # Create main frame
        frame = ttk.Frame(results_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add instructions
        ttk.Label(
            frame,
            text="Click '✓' or '+' to select products, then use 'Add Selected' to add them to monitoring",
            background='#f0f0f0'
        ).pack(fill=tk.X, pady=(0, 10))
        
        # Create treeview with scrollbar
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create results tree
        tree = ttk.Treeview(
            tree_frame,
            columns=('Select', 'Name', 'Price', 'Add'),
            show='headings',
            selectmode='extended'
        )
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure scrollbar
        scrollbar.config(command=tree.yview)
        tree.config(yscrollcommand=scrollbar.set)
        
        # Configure columns
        tree.column('Select', width=50, anchor=tk.CENTER)
        tree.column('Name', width=450, anchor=tk.W)
        tree.column('Price', width=100, anchor=tk.CENTER)
        tree.column('Add', width=100, anchor=tk.CENTER)
        
        # Configure headings
        tree.heading('Select', text='✓', anchor=tk.CENTER)
        tree.heading('Name', text='Product Name', anchor=tk.W)
        tree.heading('Price', text='Price', anchor=tk.CENTER)
        tree.heading('Add', text='Select', anchor=tk.CENTER)
        
        # Add results to tree
        for result in results:
            tree.insert('', 'end', values=(
                '☐',  # Checkbox
                result['display_name'],
                result['price'],
                '➕'   # Add button
            ), tags=('result',))
        
        # Store URLs in a dictionary
        self.search_results = {
            result['display_name']: result['url']
            for result in results
        }
        
        # Create buttons frame
        buttons_frame = ttk.Frame(frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        # Add buttons for multiple selection
        ttk.Button(
            buttons_frame,
            text="Select All",
            style='Custom.TButton',
            command=lambda: self.toggle_all_selections(tree, True)
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="Deselect All",
            style='Custom.TButton',
            command=lambda: self.toggle_all_selections(tree, False)
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="Add Selected",
            style='Custom.TButton',
            command=lambda: self.add_selected_products(tree, results_window)
        ).pack(side=tk.LEFT, padx=5)
        
        # Add close button
        ttk.Button(
            buttons_frame,
            text="Close",
            style='Custom.TButton',
            command=results_window.destroy
        ).pack(side=tk.RIGHT, padx=5)
        
        # Bind click events
        tree.bind('<Button-1>', lambda e: self.handle_result_click(e, tree))

    def toggle_all_selections(self, tree, select: bool):
        """Toggle all checkboxes in the tree."""
        for item in tree.get_children():
            values = list(tree.item(item)['values'])
            values[0] = '☑' if select else '☐'  # Set checkbox
            values[3] = '✓' if select else '➕'  # Set add button
            tree.item(item, values=values)

    def handle_result_click(self, event, tree):
        """Handle click on search result."""
        region = tree.identify_region(event.x, event.y)
        if region == "cell":
            column = tree.identify_column(event.x)
            item = tree.identify_row(event.y)
            if item:
                values = tree.item(item)['values']
                if values:
                    if column in ("#1", "#4"):  # Checkbox or Add column
                        # Toggle selection
                        new_values = list(values)
                        new_values[0] = '☑' if values[0] == '☐' else '☐'  # Toggle checkbox
                        new_values[3] = '✓' if values[0] == '☐' else '➕'  # Toggle add button
                        tree.item(item, values=new_values)

    def add_selected_products(self, tree, window):
        """Add all selected products to monitoring."""
        added_count = 0
        for item in tree.get_children():
            values = tree.item(item)['values']
            if values[0] == '☑':  # If checkbox is checked
                product_name = values[1]
                url = self.search_results.get(product_name)
                if url:
                    self.add_product_to_monitor(url)
                    added_count += 1
        
        if added_count > 0:
            messagebox.showinfo(
                "Products Added",
                f"Successfully added {added_count} product(s) to monitoring list"
            )
            window.destroy()
        else:
            messagebox.showwarning(
                "No Selection",
                "Please select at least one product to add"
            )

    def add_product_to_monitor(self, url: str) -> ProductMonitor:
        """Add a product to monitor."""
        try:
            # Create monitor tab
            monitor = ProductMonitor(self.notebook, url, self)
            
            # Add to tree
            name = monitor.check_stock()[1] or "Unknown"
            item = self.product_tree.insert('', 'end', values=(
                name,
                url,
                'Not Monitoring',
                '▶'  # Start button
            ))
            
            return monitor
        except Exception as e:
            self.handle_error(e, "Stock Check Error")
            return None

    def format_product_name(self, name: str, max_length: int = 80) -> str:
        """Format product name to maximum length with ellipsis."""
        if len(name) <= max_length:
            return name
        return name[:max_length-3] + "..." 

    def check_stock(self, url: str):
        """Check stock status for a product URL."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            from ..utils.helpers import check_stock
            return check_stock(url, headers)
        except Exception as e:
            self.handle_error(e, "Stock Check Error")
            return False, "Error checking stock", None

    def log_message(self, message: str):
        """Log a message to both file and console."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"[{timestamp}] {message}"
        
        # Log to file
        logging.info(message)
        
        # Update UI if log display exists
        if hasattr(self, 'log_display'):
            self.log_display.insert(tk.END, full_message + "\n")
            self.log_display.see(tk.END)
            
            # Limit the number of lines
            lines = int(self.log_display.index('end-1c').split('.')[0])
            if lines > 1000:  # Keep last 1000 lines
                self.log_display.delete('1.0', f'{lines-1000}.0')

    def create_log_display(self, parent: ttk.Frame) -> tk.Text:
        """Create a log display widget."""
        log_frame = ttk.Frame(parent)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create text widget with scrollbar
        scrollbar = ttk.Scrollbar(log_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        log_display = tk.Text(
            log_frame,
            height=6,
            wrap=tk.WORD,
            font=('Consolas', 9),
            yscrollcommand=scrollbar.set
        )
        log_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=log_display.yview)
        
        return log_display 

    def start_monitoring(self, url: str):
        """Start monitoring a single product."""
        try:
            # Create unique tab name from URL
            tab_name = f"Monitor_{url.split('/')[-1]}"
            
            # Check if already monitoring
            if tab_name in self.monitor_tabs:
                self.notebook.select(self.monitor_tabs[tab_name])
                return
            
            # Create new monitor tab
            monitor_tab = ProductMonitor(self.notebook, url, self)
            self.monitor_tabs[tab_name] = monitor_tab
            
            # Add the new monitor tab (keeping + tab at the end)
            self.add_monitor_tab(monitor_tab, f"⚪ {tab_name}")
            
            # Start monitoring
            monitor_tab.start_monitoring()
            
        except Exception as e:
            self.handle_error(e, "Start Monitoring Error")

    def stop_monitoring(self, tab_name: str):
        """Stop monitoring a product."""
        try:
            if tab_name in self.monitor_tabs:
                # Get the monitor tab
                monitor_tab = self.monitor_tabs[tab_name]
                
                # Stop monitoring
                if hasattr(monitor_tab, 'stop_monitoring'):
                    monitor_tab.stop_monitoring()
                
                # Update tree status if URL found
                url = monitor_tab.url if hasattr(monitor_tab, 'url') else None
                if url:
                    for item in self.product_tree.get_children():
                        values = self.product_tree.item(item)['values']
                        if values[1] == url:  # URL is second column
                            self.product_tree.item(item, values=(
                                values[0],  # Name
                                values[1],  # URL
                                'Stopped',
                                '⏵'  # Start button
                            ))
                            break
                
                # Remove the tab
                self.notebook.forget(monitor_tab)
                del self.monitor_tabs[tab_name]
                
        except Exception as e:
            self.handle_error(e, "Stop Monitoring Error")

    def save_profile(self):
        """Save current configuration to a profile."""
        profile_name = self.profile_var.get()
        if not profile_name:
            return
            
        try:
            # Get products from tree
            products = []
            for item in self.product_tree.get_children():
                values = self.product_tree.item(item)['values']
                products.append({
                    'name': values[0],
                    'url': values[1]
                })
            
            self.profile_handler.save_profile(profile_name, {'products': products})
            
        except Exception as e:
            self.handle_error(e)

    def load_profile(self):
        """Load selected profile."""
        profile_name = self.profile_var.get()
        if not profile_name:
            return
        
        try:
            # Load profile data
            profile = self.profile_handler.load_profile(profile_name)
            
            # Clear existing products
            self.clear_product_tree()
            
            # Add products from profile
            for product in profile['products']:
                self.add_product_to_monitor(product['url'])
            
        except Exception as e:
            self.handle_error(f"Error loading profile: {e}")

    def update_profile_list(self):
        """Update profile combo box with available profiles."""
        profiles = [''] + list(self.profile_manager.list_profiles())
        self.profile_combo['values'] = profiles 

    def add_monitor_tab(self, tab, text):
        """Add a new monitor tab."""
        self.notebook.add(tab, text=text)
        self.notebook.select(tab)

    def setup_connections(self):
        """Set up signal connections"""
        # ... existing connections ...
        
        # Add connection for clearing setup page
        self.task_monitor.signals.clear_setup_page.connect(self.clear_setup_page)

    def clear_setup_page(self):
        """Clear all fields in the setup page"""
        # Clear search entry
        if hasattr(self, 'search_entry'):
            self.search_entry.delete(0, tk.END)
        
        # Clear product tree
        if hasattr(self, 'product_tree'):
            for item in self.product_tree.get_children():
                self.product_tree.delete(item)
        
        # Clear profile selection
        if hasattr(self, 'profile_var'):
            self.profile_var.set('')

    def create_found_products_section(self):
        """Create section for products found in stock."""
        frame = ttk.LabelFrame(self.setup_tab, text=" Found In Stock ", style='Custom.TLabelframe')
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create scrollbar
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create text widget for found products
        self.found_products = tk.Text(
            frame,
            height=6,
            wrap=tk.WORD,
            font=('Consolas', 10),
            background='#ffffff',
            yscrollcommand=scrollbar.set
        )
        self.found_products.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Configure scrollbar
        scrollbar.config(command=self.found_products.yview)
        
        # Configure tags
        self.found_products.tag_configure('normal', spacing1=2)
        self.found_products.tag_configure('hyperlink', foreground='blue', underline=1) 