from typing import Dict, Optional, List
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from config import STYLES, STORES, WINDOW_SIZE, DEFAULT_INTERVAL
from profile_manager import ProfileManager
from search_manager import SearchManager
from product_monitor import ProductMonitor
from exceptions import ProfileError, ProfileLoadError, APIError
import logging
from datetime import datetime
from profile_monitor import ProfileMonitor
import requests

class StockMonitorGUI:
    """Main GUI application for stock monitoring."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.search_results = {}
        self.setup_root_window()
        self.initialize_managers()
        self.setup_styles()
        self.create_main_interface()
        self.setup_logging()
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_root_window(self):
        """Configure the root window."""
        self.root.title("Stock Monitor")
        self.root.geometry(f"{WINDOW_SIZE[0]}x{WINDOW_SIZE[1]}")
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
        
    def setup_logging(self):
        """Configure logging."""
        logging.basicConfig(
            filename='stock_monitor.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def create_main_interface(self):
        """Create the main interface components."""
        self.main_container = ttk.Frame(self.root, style='Custom.TFrame')
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create main setup tab
        self.setup_tab = ttk.Frame(self.notebook, style='Custom.TFrame')
        self.notebook.add(self.setup_tab, text="📋 Setup")
        
        # Create tab components
        self.create_profile_section()
        self.create_search_section()
        self.create_product_list()
        
        # Create new task tab (plus button) - will always be last
        self.new_task_tab = ttk.Frame(self.notebook, style='Plus.TFrame')
        self.notebook.add(self.new_task_tab, text=" + ")
        
        # Bind tab selection
        self.notebook.bind('<<NotebookTabChanged>>', self.handle_tab_change)
        self.notebook.bind('<Button-3>', self.show_tab_menu)
        
    def create_profile_section(self):
        """Create profile management section."""
        # Main profile frame
        frame = ttk.LabelFrame(self.setup_tab, text=" Profile Management ", style='Custom.TLabelframe')
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Main controls container
        controls = ttk.Frame(frame, style='Custom.TFrame')
        controls.pack(fill=tk.X, padx=10, pady=10)
        
        # Left side with profile selection and buttons
        left_side = ttk.Frame(controls, style='Custom.TFrame')
        left_side.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Profile selection row
        selection_frame = ttk.Frame(left_side, style='Custom.TFrame')
        selection_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(selection_frame, 
                 text="Profile:", 
                 background='#f0f0f0').pack(side=tk.LEFT, padx=(0, 5))
        
        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(
            selection_frame,
            textvariable=self.profile_var,
            values=[''] + list(self.profile_manager.list_profiles()),
            state='readonly',
            width=30
        )
        self.profile_combo.pack(side=tk.LEFT, padx=5)
        
        # Buttons row
        buttons_frame = ttk.Frame(left_side, style='Custom.TFrame')
        buttons_frame.pack(fill=tk.X)
        
        # Define all profile management buttons
        buttons = [
            ("💾 Save Profile", self.save_current_profile),
            ("📂 Load Profile", self.load_selected_profile),
            ("🗑️ Delete Profile", self.delete_selected_profile),
            ("▶ Start Monitoring", self.start_profile_monitoring)
        ]
        
        # Create buttons with consistent spacing
        for text, command in buttons:
            btn = ttk.Button(
                buttons_frame,
                text=text,
                style='Custom.TButton',
                command=command
            )
            btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Add "New Profile" button
        ttk.Button(
            buttons_frame,
            text="🆕 New Profile",
            style='Custom.TButton',
            command=self.clear_setup_gui
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # Right side with interval setting
        right_side = ttk.Frame(controls, style='Custom.TFrame')
        right_side.pack(side=tk.RIGHT, padx=(20, 0))
        
        ttk.Label(right_side, 
                 text="Check Interval (sec):", 
                 background='#f0f0f0').pack(side=tk.LEFT, padx=5)
        
        self.interval_entry = ttk.Entry(right_side, width=5)
        self.interval_entry.insert(0, DEFAULT_INTERVAL)
        self.interval_entry.pack(side=tk.LEFT, padx=5)
        
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
        
        ttk.Button(
            search_frame,
            text="🔍 Search",
            style='Custom.TButton',
            command=self.perform_search
        ).pack(side=tk.LEFT, padx=5)
        
    def create_product_list(self):
        """Create product list section."""
        frame = ttk.LabelFrame(self.setup_tab, text=" Monitored Products ", style='Custom.TLabelframe')
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Add control buttons
        controls = ttk.Frame(frame, style='Custom.TFrame')
        controls.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        ttk.Button(
            controls,
            text="▶ Start Monitoring",
            style='Custom.TButton',
            command=self.start_task_monitoring
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            controls,
            text="🗑️ Clear List",
            style='Custom.TButton',
            command=lambda: self.clear_product_tree()
        ).pack(side=tk.LEFT, padx=5)
        
        # Create treeview
        self.product_tree = self.create_product_treeview(frame)
        
    def create_product_treeview(self, parent: ttk.Frame) -> ttk.Treeview:
        """Create and configure the product treeview."""
        # Create treeview with scrollbar
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create treeview with Name first
        tree = ttk.Treeview(
            tree_frame,
            columns=('Name', 'URL', 'Status', 'Action', 'Cart'),
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
        tree.column('Cart', width=100, anchor=tk.CENTER)
        
        # Configure headings
        tree.heading('Name', text='Product Name', anchor=tk.W)
        tree.heading('URL', text='Product URL', anchor=tk.W)
        tree.heading('Status', text='Status', anchor=tk.CENTER)
        tree.heading('Action', text='', anchor=tk.CENTER)
        tree.heading('Cart', text='Cart', anchor=tk.CENTER)
        
        # Hide URL column (optional)
        # tree.column('URL', width=0, stretch=False)
        
        # Bind click events
        tree.bind('<Double-1>', self.handle_tree_double_click)
        tree.bind('<Button-1>', self.handle_tree_click)
        
        return tree

    def handle_tree_double_click(self, event):
        """Handle double click on tree item."""
        tree = event.widget
        item = tree.selection()[0]
        values = tree.item(item)['values']
        if values:
            url = values[0]
            # Open URL in default browser
            import webbrowser
            webbrowser.open(url)

    def handle_tree_click(self, event):
        """Handle single click on tree item."""
        tree = event.widget
        region = tree.identify_region(event.x, event.y)
        if region == "cell":
            column = tree.identify_column(event.x)
            item = tree.identify_row(event.y)
            if item and column == "#3":  # Action column
                values = tree.item(item)['values']
                if values:
                    url = values[0]
                    if values[2] == '⏵':  # Start monitoring
                        self.start_monitoring(url)
                    else:  # Stop monitoring
                        tab_name = f"Monitor_{url.split('/')[-1]}"
                        self.stop_monitoring(tab_name)
            elif item and column == "#4":  # Cart column
                values = tree.item(item)['values']
                if values:
                    url = values[0]
                    self.add_to_cart(url)

    def add_to_cart(self, url: str):
        """Add product to cart."""
        try:
            # Open URL in default browser
            import webbrowser
            webbrowser.open(url)
            self.log_message(f"Opening product page: {url}")
        except Exception as e:
            self.handle_error(e, "Failed to open product page")

    def handle_error(self, error: Exception, title: str = "Error"):
        """Handle and log errors."""
        message = str(error)
        logging.error(f"{title}: {message}")
        messagebox.showerror(title, message)
        
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
            
    def start_monitoring(self, url: str):
        """Start monitoring a product."""
        try:
            product_name = url.split('/')[-1]
            tab_name = f"Monitor_{product_name}"
            
            if tab_name in self.monitor_tabs:
                raise ValueError("Already monitoring this product")
                
            monitor_tab = ProductMonitor(self.notebook, url, self)
            self.monitor_tabs[tab_name] = monitor_tab
            self.notebook.add(monitor_tab, text=f"📊 {product_name}")
            self.notebook.select(monitor_tab)
            
            logging.info(f"Started monitoring: {url}")
            
        except Exception as e:
            self.handle_error(e, "Monitoring Error")
            
    def stop_monitoring(self, tab_name: str):
        """Stop monitoring a product."""
        try:
            if tab_name in self.monitor_tabs:
                tab = self.monitor_tabs[tab_name]
                if hasattr(tab, 'stop_monitoring'):
                    tab.stop_monitoring()
                try:
                    self.notebook.forget(tab)
                except Exception:
                    pass  # Tab might already be gone
                self.monitor_tabs.pop(tab_name, None)
        except Exception as e:
            logging.error(f"Error stopping monitor {tab_name}: {str(e)}")
            
    def save_current_profile(self):
        """Save current configuration as a profile."""
        try:
            name = self.get_profile_name()
            if not name:
                return
            
            # Validate profile name
            if not name.strip():
                raise ValueError("Profile name cannot be empty")
            
            data = self.collect_profile_data()
            self.profile_manager.save_profile(name, data)
            
            # Update profile list
            self.update_profile_list()
            messagebox.showinfo("Success", f"Profile '{name}' saved successfully")
            
        except Exception as e:
            self.handle_error(e, "Profile Save Error")
            
    def load_selected_profile(self):
        """Load selected profile."""
        try:
            name = self.profile_var.get()
            if not name:
                raise ValueError("No profile selected")
            
            data = self.profile_manager.load_profile(name)
            if not data:
                raise ProfileLoadError("Failed to load profile data")
            
            self.apply_profile_data(data)
            logging.info(f"Profile loaded: {name}")
            
        except ProfileError as e:
            self.handle_error(e, "Profile Load Error")
        except Exception as e:
            self.handle_error(e, "Unexpected Error")
            
    def delete_selected_profile(self):
        """Delete the selected profile."""
        try:
            name = self.profile_var.get()
            if not name:
                messagebox.showwarning("Warning", "Please select a profile to delete")
                return
            
            if messagebox.askyesno("Confirm Delete", 
                                  f"Are you sure you want to delete profile '{name}'?\n"
                                  "This action cannot be undone."):
                if self.profile_manager.delete_profile(name):
                    # Clear the current selection
                    self.profile_var.set('')
                    # Update the profile list
                    self.update_profile_list()
                    # Show success message
                    messagebox.showinfo("Success", f"Profile '{name}' deleted successfully")
                    # Log the deletion
                    logging.info(f"Profile deleted: {name}")
                else:
                    raise ValueError(f"Failed to delete profile: {name}")
                
        except Exception as e:
            self.handle_error(e, "Profile Delete Error")
            
    def update_profile_list(self):
        """Update the profile combo box with current profiles."""
        try:
            profiles = self.profile_manager.list_profiles()
            # Add empty option at the start
            self.profile_combo['values'] = [''] + profiles
            
            current = self.profile_var.get()
            if not profiles:
                # No profiles exist
                self.profile_var.set('')
                self.profile_combo.set('')
            elif current and current not in profiles:
                # Current selection was deleted, select blank
                self.profile_var.set('')
                self.profile_combo.set('')
        
        except Exception as e:
            self.handle_error(e, "Failed to update profile list")
            
    def cleanup(self):
        """Perform cleanup before closing."""
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
            
            # Clear any remaining widgets
            try:
                self.profile_var.set('')
                self.product_tree.delete(*self.product_tree.get_children())
            except Exception:
                pass  # Ignore errors during cleanup
            
            logging.info("Application closed")
            
        except Exception as e:
            logging.error(f"Error during cleanup: {str(e)}")

    def collect_profile_data(self) -> Dict:
        """Collect current configuration for profile saving."""
        data = {
            'products': [],
            'interval': self.interval_entry.get(),
            'store': self.store_var.get()
        }
        
        # Collect products from main list
        for item in self.product_tree.get_children():
            values = self.product_tree.item(item)['values']
            data['products'].append({
                'url': values[0],
                'status': values[1],
                'monitoring': True,  # Changed to True since we want to monitor these
                'interval': self.interval_entry.get()
            })
        
        # Collect active monitoring tabs
        for tab_name, tab in self.monitor_tabs.items():
            data['products'].append({
                'url': tab.url,
                'interval': tab.interval_entry.get(),
                'monitoring': True
            })
        
        return data

    def get_profile_name(self) -> Optional[str]:
        """Get profile name from user."""
        name = simpledialog.askstring("Save Profile", "Enter profile name:")
        if name:
            # Remove any path-like characters
            name = name.replace('/', '').replace('\\', '')
        return name

    def apply_profile_data(self, data: Dict):
        """Apply loaded profile data."""
        try:
            # Clear existing products and monitoring
            self.clear_current_state()
            
            # Set basic settings
            self.interval_entry.delete(0, tk.END)
            self.interval_entry.insert(0, data.get('interval', DEFAULT_INTERVAL))
            
            if 'store' in data:
                self.store_var.set(data['store'])
            
            # Load products
            for product in data.get('products', []):
                url = product.get('url')
                if url:  # Make sure we have a URL
                    if product.get('monitoring', True):  # Default to True if not specified
                        self.start_monitoring(url)
                    else:
                        self.product_tree.insert('', 'end', values=(
                            url,
                            product.get('status', 'Not checked'),
                            '⏵',
                            ''
                        ))
                    
        except Exception as e:
            self.handle_error(e, "Failed to apply profile data")

    def clear_current_state(self):
        """Clear all current products and monitoring."""
        # Clear product tree
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)
        
        # Stop all monitoring
        for tab_name in list(self.monitor_tabs.keys()):
            self.stop_monitoring(tab_name)

    def on_closing(self):
        """Handle window closing."""
        try:
            self.cleanup()
        finally:
            self.root.destroy()

    def start_profile_monitoring(self):
        """Start monitoring for the selected profile."""
        try:
            # Get selected profile
            profile_name = self.profile_var.get()
            if not profile_name:
                messagebox.showwarning("Warning", "Please select a profile to monitor")
                return
            
            # Check if profile is already being monitored
            if profile_name in self.monitor_tabs:
                messagebox.showwarning("Warning", "This profile is already being monitored")
                return
            
            # Load profile data
            try:
                profile_data = self.profile_manager.load_profile(profile_name)
            except ProfileLoadError as e:
                self.handle_error(e, "Profile Load Error")
                return
            
            # Get products to monitor
            products = profile_data.get('products', [])
            if not products:
                messagebox.showwarning("No Products", "No products found in this profile")
                return
            
            # Get the plus tab index (last tab)
            plus_tab_index = self.notebook.index('end') - 1
            
            # Create monitoring tab
            monitor_tab = ProfileMonitor(self.notebook, profile_name, products, self)
            self.monitor_tabs[profile_name] = monitor_tab
            
            # Insert new tab before the plus tab
            self.notebook.insert(plus_tab_index, monitor_tab, text=f"📊 {profile_name}")
            self.notebook.select(plus_tab_index)
            
            # Clear setup GUI for new task
            self.clear_setup_gui()
            
            self.log_message(f"Started monitoring profile: {profile_name}")
            
        except Exception as e:
            self.handle_error(e, "Profile Monitoring Error")

    def log_message(self, message: str):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.info(f"[{timestamp}] {message}")

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

    def toggle_all_selections(self, tree, select: bool):
        """Toggle all checkboxes in the tree."""
        for item in tree.get_children():
            values = list(tree.item(item)['values'])
            values[0] = '☑' if select else '☐'  # Set checkbox
            values[3] = '✓' if select else '➕'  # Set add button
            tree.item(item, values=values)

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

    def add_product_to_monitor(self, url: str):
        """Add a single product to the monitoring list."""
        try:
            # Check if product is already in the list
            for item in self.product_tree.get_children():
                if self.product_tree.item(item)['values'][1] == url:  # URL is now second column
                    return  # Skip if already exists
            
            # Get product name
            _, product_name, _ = self.check_stock(url)
            display_name = self.format_product_name(product_name)
            
            # Add new product
            self.product_tree.insert('', 'end', values=(
                display_name,  # Name first
                url,
                'Not checked',
                '⏵',
                ''
            ))
        except Exception as e:
            self.log_message(f"Error adding product: {str(e)}")

    def format_product_name(self, name: str, max_length: int = 80) -> str:
        """Format product name to maximum length with ellipsis."""
        if len(name) <= max_length:
            return name
        return name[:max_length-3] + "..."

    def check_stock(self, url: str) -> tuple:
        """Check stock status for a product URL."""
        try:
            # Get product ID from URL
            product_id = url.split('/')[-1]
            
            # Create API URL
            api_url = f'https://www.bestbuy.ca/api/v2/json/product/{product_id}'
            
            # Make request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(api_url, headers=headers)
            if response.status_code != 200:
                raise APIError(response.status_code, "Failed to get product data")
            
            data = response.json()
            
            # Get availability info
            availability = data.get('availability', {})
            product_name = data.get('name', 'Unknown Product')
            stock_count = availability.get('onlineAvailabilityCount', 0)
            
            # Check if product is available
            is_available = (
                availability.get('isAvailableOnline', False) and
                availability.get('onlineAvailability') == "InStock" and
                stock_count > 0 and
                availability.get('buttonState') == "AddToCart"
            )
            
            # Create status details
            status_details = {
                'name': product_name,
                'stock': stock_count,
                'status': availability.get('onlineAvailability', 'Unknown'),
                'purchasable': 'Yes' if availability.get('buttonState') == "AddToCart" else 'No'
            }
            
            return is_available, product_name, status_details
            
        except Exception as e:
            logging.error(f"Error checking stock for {url}: {str(e)}")
            raise 

    def clear_setup_gui(self):
        """Clear all setup GUI elements."""
        # Clear profile selection
        self.profile_var.set('')
        
        # Clear interval entry
        self.interval_entry.delete(0, tk.END)
        self.interval_entry.insert(0, DEFAULT_INTERVAL)
        
        # Clear search entry
        self.search_entry.delete(0, tk.END)
        
        # Clear product tree
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)
        
        # Log action
        self.log_message("Cleared setup GUI for new profile")

    def start_task_monitoring(self):
        """Start monitoring current product list without profile."""
        try:
            # Check if there are products to monitor
            products = []
            for item in self.product_tree.get_children():
                values = self.product_tree.item(item)['values']
                products.append({
                    'url': values[1],  # URL is second column
                    'name': values[0],  # Name is first column
                    'status': 'Not checked',
                    'monitoring': True,
                    'interval': self.interval_entry.get()
                })
            
            if not products:
                messagebox.showwarning("No Products", "Please add products to monitor")
                return
            
            # Generate a task name
            task_name = f"Task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create monitoring tab
            monitor_tab = ProfileMonitor(self.notebook, task_name, products, self)
            self.monitor_tabs[task_name] = monitor_tab
            
            # Add the monitor tab
            self.add_monitor_tab(monitor_tab, f"📊 Task")
            
            # Clear setup GUI for new task
            self.clear_setup_gui()
            
        except Exception as e:
            self.handle_error(e, "Task Monitoring Error")

    def clear_product_tree(self):
        """Clear all products from the tree."""
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)

    def create_new_task(self):
        """Create a new empty task tab."""
        try:
            # Generate task name
            task_name = f"Task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create empty task
            monitor_tab = ProfileMonitor(self.notebook, task_name, [], self)
            self.monitor_tabs[task_name] = monitor_tab
            
            # Add the monitor tab
            self.add_monitor_tab(monitor_tab, f"📊 New Task")
            
            self.log_message(f"Created new task: {task_name}")
            
        except Exception as e:
            self.handle_error(e, "Task Creation Error")

    def handle_tab_change(self, event):
        """Handle tab selection changes."""
        try:
            current = self.notebook.select()
            if current == str(self.new_task_tab):  # If plus tab selected
                # Create new task
                self.create_new_task()
                # Switch back to setup tab
                self.notebook.select(0)
            
        except Exception as e:
            self.handle_error(e, "Tab Change Error")

    def show_tab_menu(self, event):
        """Show context menu for tabs."""
        try:
            # Get clicked tab
            clicked_tab = self.notebook.tk.call(self.notebook._w, "identify", "tab", event.x, event.y)
            
            # Don't show menu for setup or plus tab
            if clicked_tab in (0, 1):  # Setup and plus tabs
                return
            
            # Create context menu
            menu = tk.Menu(self.root, tearoff=0)
            
            # Add menu items
            menu.add_command(
                label="Rename",
                command=lambda: self.rename_tab(clicked_tab)
            )
            menu.add_command(
                label="Close",
                command=lambda: self.close_tab(clicked_tab)
            )
            
            # Show menu
            menu.post(event.x_root, event.y_root)
            
        except Exception as e:
            self.handle_error(e, "Menu Error")

    def rename_tab(self, tab_id):
        """Rename the selected tab."""
        try:
            current_name = self.notebook.tab(tab_id, "text")
            new_name = simpledialog.askstring(
                "Rename Tab",
                "Enter new name:",
                initialvalue=current_name
            )
            if new_name:
                self.notebook.tab(tab_id, text=new_name)
            
        except Exception as e:
            self.handle_error(e, "Rename Error")

    def close_tab(self, tab_id):
        """Close the selected tab."""
        try:
            # Get tab widget
            tab_widget = self.notebook.select() if tab_id is None else self.notebook.tabs()[tab_id]
            widget = self.notebook.nametowidget(tab_widget)
            
            # Confirm close
            if messagebox.askyesno("Close Tab", "Are you sure you want to close this tab?"):
                # Stop monitoring if needed
                if hasattr(widget, 'stop_monitoring'):
                    widget.stop_monitoring()
                
                # Remove from monitor tabs
                for name, tab in list(self.monitor_tabs.items()):
                    if tab == widget:
                        self.monitor_tabs.pop(name)
                        break
                
                # Remove tab
                self.notebook.forget(self.notebook.index(tab_widget))
                
                # Select setup tab
                self.notebook.select(0)
        
        except Exception as e:
            self.handle_error(e, "Close Error")

    def add_monitor_tab(self, monitor_tab, tab_name: str):
        """Add a new monitoring tab before the plus tab."""
        # Get the plus tab index (last tab)
        plus_tab = self.new_task_tab
        
        # Remove plus tab temporarily
        self.notebook.forget(plus_tab)
        
        # Add the new monitor tab
        self.notebook.add(monitor_tab, text=tab_name)  # No indicator in tab name
        
        # Re-add plus tab at the end
        self.notebook.add(plus_tab, text=" + ")
        
        # Select the new tab
        self.notebook.select(monitor_tab) 