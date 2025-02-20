import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import threading
import queue
from datetime import datetime
import requests
import json
from plyer import notification
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class StockMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Stock Monitor")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')  # Light gray background
        
        # Monitor state
        self.monitoring = False
        self.monitor_thread = None
        self.message_queue = queue.Queue()
        self.products = {}
        
        # Style configuration
        self.style = ttk.Style()
        self.style.configure('Custom.TButton', padding=10)
        self.style.configure('Custom.TFrame', background='#f0f0f0')
        self.style.configure('Custom.TLabelframe', background='#f0f0f0')
        self.style.configure('Custom.TLabelframe.Label', background='#f0f0f0', font=('Arial', 10, 'bold'))
        
        # Create main container with padding
        self.main_container = ttk.Frame(root, style='Custom.TFrame')
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create main setup tab
        self.setup_tab = ttk.Frame(self.notebook, style='Custom.TFrame')
        self.notebook.add(self.setup_tab, text="📋 Setup")
        
        # Create profiles frame in setup tab
        self.create_profiles_frame()
        
        # Create product management frame in setup tab
        self.create_product_frame()
        
        # Dictionary to store monitoring tabs
        self.monitor_tabs = {}
        
        # Remove the automatic driver initialization
        self.driver = None
        
        # Make main window resizable
        self.root.resizable(True, True)
        
        # Configure grid weights for resizing
        self.main_container.grid(row=0, column=0, sticky="nsew")
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)

    def create_profiles_frame(self):
        profile_frame = ttk.LabelFrame(self.setup_tab, text=" Profile Management ", style='Custom.TLabelframe')
        profile_frame.pack(fill=tk.X, padx=10, pady=5)
        
        controls = ttk.Frame(profile_frame, style='Custom.TFrame')
        controls.pack(fill=tk.X, padx=10, pady=10)
        
        # Left side controls
        left_controls = ttk.Frame(controls, style='Custom.TFrame')
        left_controls.pack(side=tk.LEFT)
        
        # Profile selection
        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(
            left_controls,
            textvariable=self.profile_var,
            width=30,
            state='readonly'
        )
        self.profile_combo.pack(side=tk.LEFT, padx=5)
        
        # Profile buttons
        save_profile_btn = ttk.Button(
            left_controls,
            text="💾 Save Profile",
            style='Custom.TButton',
            command=self.save_profile
        )
        save_profile_btn.pack(side=tk.LEFT, padx=5)
        
        load_profile_btn = ttk.Button(
            left_controls,
            text="📂 Load Profile",
            style='Custom.TButton',
            command=self.load_profile
        )
        load_profile_btn.pack(side=tk.LEFT, padx=5)
        
        start_monitor_btn = ttk.Button(
            left_controls,
            text="▶ Start Monitoring",
            style='Custom.TButton',
            command=self.start_profile_monitoring
        )
        start_monitor_btn.pack(side=tk.LEFT, padx=5)
        
        # Right side controls
        right_controls = ttk.Frame(controls, style='Custom.TFrame')
        right_controls.pack(side=tk.RIGHT)
        
        ttk.Label(right_controls, text="Check Interval (sec):", background='#f0f0f0').pack(side=tk.LEFT, padx=5)
        self.interval_entry = ttk.Entry(right_controls, width=5)
        self.interval_entry.insert(0, "15")
        self.interval_entry.pack(side=tk.LEFT, padx=5)
        
        # Load existing profiles
        self.load_profiles()

    def create_product_frame(self):
        # URL input section
        self.url_frame = ttk.LabelFrame(self.setup_tab, text=" Add New Product ", style='Custom.TLabelframe')
        self.url_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Store selection and search frame
        store_search_frame = ttk.Frame(self.url_frame, style='Custom.TFrame')
        store_search_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        # Store dropdown
        self.stores = {
            'Best Buy': {
                'name': 'Best Buy',
                'search_url': 'https://www.bestbuy.ca/api/v2/json/search?query={}',
                'product_base_url': 'https://www.bestbuy.ca/en-ca/product/',
            },
            'Amazon': {
                'name': 'Amazon',
                'search_url': 'https://www.amazon.ca/s?k={}',
                'product_base_url': 'https://www.amazon.ca/dp/',
            },
            'Newegg': {
                'name': 'Newegg',
                'search_url': 'https://www.newegg.ca/p/pl?d={}',
                'product_base_url': 'https://www.newegg.ca/p/',
            }
        }
        
        ttk.Label(store_search_frame, text="Store:").pack(side=tk.LEFT, padx=(0, 5))
        self.store_var = tk.StringVar(value='Best Buy')
        store_dropdown = ttk.Combobox(
            store_search_frame, 
            textvariable=self.store_var,
            values=list(self.stores.keys()),
            state='readonly',
            width=15
        )
        store_dropdown.pack(side=tk.LEFT, padx=5)
        
        # Search entry and button
        ttk.Label(store_search_frame, text="Search:").pack(side=tk.LEFT, padx=(10, 5))
        self.search_entry = ttk.Entry(store_search_frame, width=40)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        search_button = ttk.Button(
            store_search_frame, 
            text="🔍 Search", 
            style='Custom.TButton',
            command=self.search_products
        )
        search_button.pack(side=tk.LEFT, padx=5)
        
        # Search results frame
        self.results_frame = ttk.Frame(self.url_frame, style='Custom.TFrame')
        self.results_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Search results treeview
        self.results_tree = ttk.Treeview(
            self.results_frame, 
            columns=('Name', 'Price', 'Add'),
            show='headings',
            height=5
        )
        self.results_tree.heading('Name', text='Product Name')
        self.results_tree.heading('Price', text='Price')
        self.results_tree.heading('Add', text='')
        self.results_tree.column('Name', width=500)
        self.results_tree.column('Price', width=100)
        self.results_tree.column('Add', width=50)
        
        # Add scrollbar to results
        results_scroll = ttk.Scrollbar(self.results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=results_scroll.set)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.X, expand=True)
        results_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind click event for adding from search results
        self.results_tree.bind('<ButtonRelease-1>', self.handle_result_click)
        
        # URL manual entry (optional)
        url_input_frame = ttk.Frame(self.url_frame, style='Custom.TFrame')
        url_input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(url_input_frame, text="Or enter URL directly:").pack(side=tk.LEFT, padx=(0, 5))
        self.url_entry = ttk.Entry(url_input_frame, width=80)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.add_button = ttk.Button(
            url_input_frame,
            text="Add URL",
            style='Custom.TButton',
            command=self.add_product
        )
        self.add_button.pack(side=tk.LEFT, padx=5)
        
        # Product list section
        self.list_frame = ttk.LabelFrame(self.setup_tab, text=" Product List ", style='Custom.TLabelframe')
        self.list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Configure Treeview style
        self.style.configure("Treeview", font=('Arial', 10), rowheight=30)
        self.style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))
        
        # Create treeview for products
        self.tree = ttk.Treeview(self.list_frame, columns=('URL', 'Status', 'Action', 'Cart'), show='headings')
        self.tree.heading('URL', text='Product URL')
        self.tree.heading('Status', text='Status')
        self.tree.heading('Action', text='')  # Empty heading for cleaner look
        self.tree.heading('Cart', text='')  # Empty heading for cart button
        self.tree.column('URL', width=600)
        self.tree.column('Status', width=150)
        self.tree.column('Action', width=50)
        self.tree.column('Cart', width=100)  # Width for cart button
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add scrollbar to treeview
        scrollbar = ttk.Scrollbar(self.list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10, padx=(0, 10))
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Bind click event for the Action button
        self.tree.bind('<ButtonRelease-1>', self.handle_click)

    def add_product(self):
        url = self.url_entry.get().strip()
        if url:
            if url not in self.products:
                self.products[url] = {
                    'last_status': None,
                    'monitoring': False,
                    'scheduled_check': None
                }
                self.tree.insert('', 'end', values=(url, 'Not checked', '⏵', ''))  # Added empty cart column
                self.url_entry.delete(0, tk.END)
                self.log_message(f"➕ Added new product to monitor: {url}")
                
                if self.status_label.cget("text") == "Status: Running":
                    self.start_product_monitoring(url)
            else:
                messagebox.showwarning("Duplicate URL", "This URL is already being monitored.")
        else:
            messagebox.showwarning("Invalid URL", "Please enter a valid URL.")

    def remove_product(self):
        selected_item = self.tree.selection()
        if selected_item:
            url = self.tree.item(selected_item)['values'][0]
            self.products.pop(url, None)
            self.tree.delete(selected_item)
            self.log_message(f"➖ Removed product from monitoring: {url}")

    def log_message(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.message_queue.put(f"[{timestamp}] {message}\n")

    def check_messages(self):
        while not self.message_queue.empty():
            message = self.message_queue.get()
            self.log_display.insert(tk.END, message)
            self.log_display.see(tk.END)
        self.root.after(100, self.check_messages)

    def check_stock(self, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            product_id = url.split('/')[-1]
            api_url = f'https://www.bestbuy.ca/api/v2/json/product/{product_id}'
            
            response = requests.get(api_url, headers=headers)
            
            if response.status_code != 200:
                self.log_message(f"Error: API returned status code {response.status_code}")
                return False, None, None
            
            data = response.json()
            
            availability = data.get('availability', {})
            product_name = data.get('name', 'Product')
            stock_count = availability.get('onlineAvailabilityCount', 0)
            
            is_available = (
                availability.get('isAvailableOnline', False)
                and availability.get('onlineAvailability') == "InStock"
                and stock_count > 0
                and availability.get('buttonState') == "AddToCart"
            )
            
            # Create detailed status message
            status_details = {
                'name': product_name,
                'stock': stock_count,
                'status': availability.get('onlineAvailability', 'Unknown'),
                'purchasable': 'Yes' if availability.get('buttonState') == "AddToCart" else 'No'
            }
            
            return is_available, product_name, status_details
            
        except Exception as e:
            self.log_message(f"Error checking stock for {url}: {str(e)}")
            return False, None, None

    def update_product_status(self, url, is_available, status_text):
        for item in self.tree.get_children():
            if self.tree.item(item)['values'][0] == url:
                cart_button = '🛒 Add to Cart' if is_available else ''
                self.tree.item(item, values=(url, status_text, '⏹', cart_button))
                break

    def handle_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            item = self.tree.identify_row(event.y)
            column = self.tree.identify_column(event.x)
            
            if column == '#3':  # Action button
                url = self.tree.item(item)['values'][0]
                if self.tree.item(item)['values'][2] == '⏹':
                    self.stop_product_monitoring(url)
                else:
                    self.start_product_monitoring(url)
            elif column == '#4':  # Cart button
                url = self.tree.item(item)['values'][0]
                if self.tree.item(item)['values'][3] == '🛒 Add to Cart':
                    self.add_to_cart(url)

    def update_product_control(self, url, is_monitoring):
        for item in self.tree.get_children():
            if self.tree.item(item)['values'][0] == url:
                current_values = self.tree.item(item)['values']
                control_text = '⏹' if is_monitoring else '⏵'  # Simple square and triangle
                self.tree.item(item, values=(current_values[0], current_values[1], control_text, current_values[3]))
                break

    def start_product_monitoring(self, url):
        try:
            interval = int(self.interval_entry.get())
            if interval < 5:
                self.log_message("⚠️ Interval too short, using 5 seconds")
                interval = 5
        except ValueError:
            self.log_message("⚠️ Invalid interval, using 15 seconds")
            interval = 15

        # Create a new monitoring tab for this product
        product_name = url.split('/')[-1]  # Use product ID as temporary name
        tab_name = f"Monitor_{product_name}"
        
        if tab_name in self.monitor_tabs:
            self.log_message(f"⚠️ Already monitoring {product_name}")
            return
        
        try:
            # Create new monitoring tab
            monitor_tab = ProductMonitorTab(self.notebook, url, self)
            self.monitor_tabs[tab_name] = monitor_tab
            self.notebook.add(monitor_tab, text=f"📊 {product_name}")
            self.notebook.select(monitor_tab)
            
            # Clear the product from the main list
            for item in self.tree.get_children():
                if self.tree.item(item)['values'][0] == url:
                    self.tree.delete(item)
                    break
            
            # Remove from products dictionary in main GUI
            if url in self.products:
                del self.products[url]
            
            # Reset URL entry and store selection for new products
            self.url_entry.delete(0, tk.END)
            self.search_entry.delete(0, tk.END)
            
            # Clear search results
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            
            self.log_message(f"▶ Started monitoring: {url}")
            
        except Exception as e:
            self.log_message(f"❌ Error creating monitoring tab: {str(e)}")

    def stop_product_monitoring(self, url):
        if url in self.products and self.products[url]['scheduled_check']:
            self.after_cancel(self.products[url]['scheduled_check'])
            self.products[url]['scheduled_check'] = None
        self.update_product_control(url, False)
        self.log_message(f"⏹ Stopped monitoring: {url}")

    def monitor_product(self, url):
        if not url in self.products:
            self.products[url] = {'scheduled_check': None}
        
        try:
            is_available, product_name, status_details = self.check_stock(url)
            
            # Update status in tree view
            status_text = f"In Stock ({status_details['stock']})" if is_available else "Out of Stock"
            self.update_product_status(url, is_available, status_text)
            
            # Log status
            status_message = (
                f"Checking: {status_details['name']}\n"
                f"Status: {status_details['status']}\n"
                f"Stock: {status_details['stock']}\n"
                f"Purchasable: {status_details['purchasable']}"
            )
            self.log_message(status_message)
            
            # Schedule next check
            interval = int(self.interval_entry.get()) * 1000
            self.products[url]['scheduled_check'] = self.after(interval, lambda: self.monitor_product(url))
            
        except Exception as e:
            self.log_message(f"❌ Error monitoring {url}: {str(e)}")
            self.products[url]['scheduled_check'] = self.after(15000, lambda: self.monitor_product(url))

    def start_monitoring(self):
        if not self.products:
            messagebox.showwarning("No Products", "Please add at least one product URL to monitor.")
            return
        
        try:
            interval = int(self.interval_entry.get())
            if interval < 5:
                messagebox.showwarning("Invalid Interval", "Please use an interval of 5 seconds or more.")
                return
        except ValueError:
            messagebox.showwarning("Invalid Interval", "Please enter a valid number for the interval.")
            return
        
        # Start monitoring all inactive products
        for url in self.products:
            if not self.products[url]['monitoring']:
                self.start_product_monitoring(url)
        
        # Only disable remove button and interval entry
        self.remove_button.config(state=tk.DISABLED)
        self.interval_entry.config(state=tk.DISABLED)
        self.status_label.config(text="Status: Running")

    def stop_monitoring(self):
        # Stop all active products
        for url in self.products:
            if self.products[url]['monitoring']:
                self.stop_product_monitoring(url)
        
        self.add_button.config(state=tk.NORMAL)
        self.remove_button.config(state=tk.NORMAL)
        self.interval_entry.config(state=tk.NORMAL)
        self.status_label.config(text="Status: Stopped")

    def add_to_cart(self, url):
        try:
            self.log_message("🛒 Initializing automated checkout...")
            
            # Create new browser instance for each attempt
            options = webdriver.ChromeOptions()
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument("--window-size=1920,1080")
            
            # Create new driver instance
            driver = webdriver.Chrome(options=options)
            
            try:
                self.log_message("🌐 Opening Best Buy product page...")
                driver.get(url)
                
                # Try multiple possible button selectors
                wait = WebDriverWait(driver, 20)
                button_selectors = [
                    '[data-button-state="ADD_TO_CART"]',
                    'button[data-button-state="ADD_TO_CART"]',
                    '.addToCartButton',
                    '#addToCartButton',
                    '[data-automation="add-to-cart-button"]',
                    '[automation-id="addToCartButton"]',
                    '.add-to-cart-button',
                    '//button[contains(text(), "Add to Cart")]'  # XPath
                ]
                
                add_to_cart_button = None
                for selector in button_selectors:
                    try:
                        if selector.startswith('//'):
                            # XPath selector
                            add_to_cart_button = wait.until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                        else:
                            # CSS selector
                            add_to_cart_button = wait.until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                        if add_to_cart_button:
                            self.log_message(f"✅ Found Add to Cart button using selector: {selector}")
                            break
                    except:
                        continue
                
                if add_to_cart_button:
                    self.log_message("🖱️ Attempting to click Add to Cart button...")
                    
                    # Try multiple click methods
                    try:
                        # Method 1: Regular click
                        add_to_cart_button.click()
                    except:
                        try:
                            # Method 2: JavaScript click
                            driver.execute_script("arguments[0].click();", add_to_cart_button)
                        except:
                            # Method 3: Action chains
                            from selenium.webdriver.common.action_chains import ActionChains
                            actions = ActionChains(driver)
                            actions.move_to_element(add_to_cart_button).click().perform()
                    
                    # Wait for cart confirmation or modal
                    try:
                        wait.until(
                            EC.presence_of_element_located((
                                By.CSS_SELECTOR, 
                                '.cart-modal,.modal-dialog,[class*="cartModal"]'
                            ))
                        )
                        self.log_message("✅ Item successfully added to cart!")
                    except:
                        self.log_message("⚠️ Could not confirm if item was added to cart")
                    
                    # Keep browser open for manual interaction
                    self.log_message("ℹ️ Browser will remain open for 30 seconds to complete purchase")
                    time.sleep(30)
                else:
                    self.log_message("❌ Could not find Add to Cart button")
                
            except Exception as e:
                self.log_message(f"❌ Error during checkout process: {str(e)}")
            
            finally:
                self.log_message("🔄 Closing browser...")
                driver.quit()
                
        except Exception as e:
            self.log_message(f"❌ Failed to initialize browser: {str(e)}")
            # Fallback to manual method
            import webbrowser
            webbrowser.open(url)
            self.log_message("↗️ Opening product page for manual add to cart")

    def search_products(self):
        search_term = self.search_entry.get().strip()
        if not search_term:
            messagebox.showwarning("Search Error", "Please enter a search term")
            return
        
        store = self.stores[self.store_var.get()]
        self.log_message(f"🔍 Searching {store['name']} for: {search_term}")
        
        # Clear previous results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        try:
            # Different search implementation for each store
            if store['name'] == 'Best Buy':
                self.search_bestbuy(search_term)
            elif store['name'] == 'Amazon':
                self.search_amazon(search_term)
            elif store['name'] == 'Newegg':
                self.search_newegg(search_term)
            
        except Exception as e:
            self.log_message(f"❌ Search error: {str(e)}")

    def search_bestbuy(self, search_term):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        search_url = self.stores['Best Buy']['search_url'].format(search_term)
        response = requests.get(search_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            products = data.get('products', [])
            
            for product in products[:10]:  # Show top 10 results
                self.results_tree.insert('', 'end', values=(
                    product.get('name'),
                    f"${product.get('regularPrice')}",
                    '➕'
                ), tags=(product.get('sku'),))
            
            self.log_message(f"Found {len(products)} products")
        else:
            self.log_message("❌ Search failed")

    def handle_result_click(self, event):
        region = self.results_tree.identify_region(event.x, event.y)
        if region == "cell":
            item = self.results_tree.identify_row(event.y)
            column = self.results_tree.identify_column(event.x)
            
            if column == '#3':  # Add button column
                store = self.stores[self.store_var.get()]
                product_id = self.results_tree.item(item)['tags'][0]
                product_url = f"{store['product_base_url']}{product_id}"
                
                # Add to monitoring list
                if product_url not in self.products:
                    self.products[product_url] = {
                        'last_status': None,
                        'monitoring': False,
                        'scheduled_check': None
                    }
                    self.tree.insert('', 'end', values=(product_url, 'Not checked', '⏵', ''))
                    self.log_message(f"➕ Added new product to monitor: {product_url}")
                else:
                    messagebox.showwarning("Duplicate URL", "This URL is already being monitored.")

    def __del__(self):
        pass  # Remove the driver cleanup since we're creating new instances

    def save_profile(self):
        import json
        import os
        
        # Get profile name
        from tkinter import simpledialog
        profile_name = simpledialog.askstring("Save Profile", "Enter profile name:")
        if not profile_name:
            return
        
        # Create profiles directory if it doesn't exist
        if not os.path.exists('profiles'):
            os.makedirs('profiles')
        
        # Collect current monitoring items
        profile_data = {
            'products': [],
            'interval': self.interval_entry.get(),
            'store': self.store_var.get()
        }
        
        # Save products from main list
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            profile_data['products'].append({
                'url': values[0],
                'monitoring': False  # Products in main list are not being monitored
            })
        
        # Save products from active monitoring tabs
        for tab_name, tab in self.monitor_tabs.items():
            if isinstance(tab, ProductMonitorTab):
                profile_data['products'].append({
                    'url': tab.url,
                    'monitoring': True,  # Products in monitoring tabs are active
                    'interval': tab.interval_entry.get()  # Save individual interval
                })
        
        # Save to file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'profiles/{profile_name}_{timestamp}.json'
        
        try:
            with open(filename, 'w') as f:
                json.dump(profile_data, f, indent=4)
            
            self.log_message(f"💾 Saved profile: {profile_name}")
            
            # Clean up old profile files
            self.cleanup_old_profiles(profile_name)
            
            # Refresh profile list
            self.load_profiles()
            
        except Exception as e:
            self.log_message(f"❌ Error saving profile: {str(e)}")

    def cleanup_old_profiles(self, profile_name):
        """Keep only the most recent version of each profile."""
        import os
        import glob
        
        # Get all files for this profile
        pattern = f'profiles/{profile_name}_*.json'
        files = glob.glob(pattern)
        
        # Sort by timestamp (newest first)
        files.sort(reverse=True)
        
        # Remove all but the newest file
        for old_file in files[1:]:
            try:
                os.remove(old_file)
            except:
                pass

    def load_profiles(self):
        import os
        import glob
        
        if os.path.exists('profiles'):
            # Get the most recent version of each profile
            profiles = {}
            for file in glob.glob('profiles/*.json'):
                profile_name = file.split('/')[-1].split('_')[0]
                if profile_name not in profiles:
                    profiles[profile_name] = file
                else:
                    # Keep the newer file
                    if file > profiles[profile_name]:
                        profiles[profile_name] = file
            
            profile_names = list(profiles.keys())
            self.profile_combo['values'] = profile_names
            if profile_names:
                self.profile_combo.set(profile_names[0])

    def load_profile(self):
        import json
        
        profile_name = self.profile_var.get()
        if not profile_name:
            return
        
        try:
            with open(f'profiles/{profile_name}.json', 'r') as f:
                profile_data = json.load(f)
            
            # Stop all current monitoring
            self.stop_monitoring()
            
            # Clear current items
            for item in self.tree.get_children():
                self.tree.delete(item)
            self.products.clear()
            
            # Set interval
            self.interval_entry.delete(0, tk.END)
            self.interval_entry.insert(0, profile_data['interval'])
            
            # Set store
            self.store_var.set(profile_data['store'])
            
            # Add products
            for product in profile_data['products']:
                self.url_entry.delete(0, tk.END)
                self.url_entry.insert(0, product['url'])
                self.add_product()
                
                # Start monitoring if it was monitoring before
                if product['monitoring']:
                    self.start_product_monitoring(product['url'])
            
            self.log_message(f"📂 Loaded profile: {profile_name}")
            
        except Exception as e:
            self.log_message(f"❌ Error loading profile: {str(e)}")

    def create_frames(self):
        # URL input section
        self.url_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        
        # Control Panel
        control_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        # Product list section
        self.list_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        self.main_container.grid_rowconfigure(2, weight=2)
        
        # Log section
        self.log_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        self.main_container.grid_rowconfigure(3, weight=1)

    def start_profile_monitoring(self):
        profile_name = self.profile_var.get()
        if not profile_name:
            messagebox.showwarning("No Profile", "Please select a profile to monitor")
            return
        
        if profile_name in self.monitor_tabs:
            messagebox.showwarning("Already Monitoring", "This profile is already being monitored")
            return
        
        try:
            # Create new monitoring tab
            monitor_tab = MonitoringTab(self.notebook, profile_name, self)
            self.monitor_tabs[profile_name] = monitor_tab
            self.notebook.add(monitor_tab, text=f"📊 {profile_name}")
            self.notebook.select(monitor_tab)
            
            self.log_message(f"Created monitoring tab for profile: {profile_name}")
            
        except Exception as e:
            self.log_message(f"❌ Error creating monitoring tab: {str(e)}")

    def close_monitoring_tab(self, profile_name):
        if profile_name in self.monitor_tabs:
            tab = self.monitor_tabs[profile_name]
            # Stop all monitoring in the tab
            tab.stop_monitoring()
            # Remove the tab
            self.notebook.forget(tab)
            self.monitor_tabs.pop(profile_name)

class MonitoringTab(ttk.Frame):
    def __init__(self, parent, profile_name, main_app):
        super().__init__(parent)
        self.profile_name = profile_name
        self.main_app = main_app
        self.notebook = parent
        
        # Initialize monitoring state
        self.products = {}
        
        # Use main app's style
        self.style = main_app.style
        
        # Create monitoring interface
        self.create_monitor_interface()
        
        # Load profile data and start monitoring
        self.load_and_start_monitoring()

    def create_monitor_interface(self):
        # Control panel
        control_frame = ttk.LabelFrame(self, text=" Controls ", style='Custom.TLabelframe')
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        controls = ttk.Frame(control_frame, style='Custom.TFrame')
        controls.pack(fill=tk.X, padx=10, pady=10)
        
        # Stop button
        self.stop_button = ttk.Button(
            controls,
            text="⏹ Stop Monitoring",
            style='Custom.TButton',
            command=self.stop_monitoring
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Status and interval
        ttk.Label(controls, text="Check Interval (sec):", background='#f0f0f0').pack(side=tk.LEFT, padx=(20, 5))
        self.interval_entry = ttk.Entry(controls, width=5)
        self.interval_entry.insert(0, self.main_app.interval_entry.get())
        self.interval_entry.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(
            controls,
            text="Status: Starting...",
            background='#f0f0f0',
            font=('Arial', 10, 'bold')
        )
        self.status_label.pack(side=tk.RIGHT, padx=5)
        
        # Product list
        self.list_frame = ttk.LabelFrame(self, text=" Monitored Products ", style='Custom.TLabelframe')
        self.list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create product tree
        self.create_product_tree()
        
        # Activity log
        self.log_frame = ttk.LabelFrame(self, text=" Activity Log ", style='Custom.TLabelframe')
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_display = scrolledtext.ScrolledText(
            self.log_frame,
            height=10,
            font=('Consolas', 10),
            background='#ffffff'
        )
        self.log_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def create_product_tree(self):
        # Configure Treeview style
        self.style.configure("Treeview", font=('Arial', 10), rowheight=30)
        self.style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))
        
        # Create treeview for products
        self.tree = ttk.Treeview(self.list_frame, columns=('URL', 'Status', 'Action', 'Cart'), show='headings')
        self.tree.heading('URL', text='Product URL')
        self.tree.heading('Status', text='Status')
        self.tree.heading('Action', text='')  # Empty heading for cleaner look
        self.tree.heading('Cart', text='')  # Empty heading for cart button
        self.tree.column('URL', width=600)
        self.tree.column('Status', width=150)
        self.tree.column('Action', width=50)
        self.tree.column('Cart', width=100)  # Width for cart button
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add scrollbar to treeview
        scrollbar = ttk.Scrollbar(self.list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10, padx=(0, 10))
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Bind click event for the Action button
        self.tree.bind('<ButtonRelease-1>', self.handle_click)
    
    def load_and_start_monitoring(self):
        try:
            # Load profile data
            with open(f'profiles/{self.profile_name}.json', 'r') as f:
                profile_data = json.load(f)
            
            # Set interval
            self.interval_entry.delete(0, tk.END)
            self.interval_entry.insert(0, profile_data['interval'])
            
            # Add and start monitoring for each product
            for product in profile_data['products']:
                url = product['url']
                self.products[url] = {'scheduled_check': None}
                self.tree.insert('', 'end', values=(url, 'Starting...', '⏹', ''))
                
                # Start monitoring
                self.monitor_product(url)
                self.update_product_control(url, True)
            
            self.status_label.config(text="Status: Running")
            self.log_message(f"Started monitoring profile: {self.profile_name}")
            
        except Exception as e:
            self.log_message(f"❌ Error loading profile: {str(e)}")

    def stop_monitoring(self):
        if self.scheduled_check:
            self.after_cancel(self.scheduled_check)
            self.scheduled_check = None
        
        # Update main GUI
        self.main_app.update_product_control(self.url, False)
        
        # Add the product back to the main list
        self.main_app.products[self.url] = {
            'last_status': None,
            'monitoring': False,
            'scheduled_check': None
        }
        self.main_app.tree.insert('', 'end', values=(self.url, 'Not checked', '⏵', ''))
        
        # Remove tab
        tab_name = f"Monitor_{self.url.split('/')[-1]}"
        self.main_app.monitor_tabs.pop(tab_name, None)
        self.notebook.forget(self)
        
        self.log_message("Stopped monitoring")

    def monitor_product(self, url):
        if not url in self.products:
            self.products[url] = {'scheduled_check': None}
        
        try:
            is_available, product_name, status_details = self.main_app.check_stock(url)
            
            # Update status in tree view
            status_text = f"In Stock ({status_details['stock']})" if is_available else "Out of Stock"
            self.update_product_status(url, is_available, status_text)
            
            # Log status
            status_message = (
                f"Checking: {status_details['name']}\n"
                f"Status: {status_details['status']}\n"
                f"Stock: {status_details['stock']}\n"
                f"Purchasable: {status_details['purchasable']}"
            )
            self.log_message(status_message)
            
            # Schedule next check
            interval = int(self.interval_entry.get()) * 1000
            self.products[url]['scheduled_check'] = self.after(interval, lambda: self.monitor_product(url))
            
        except Exception as e:
            self.log_message(f"❌ Error monitoring {url}: {str(e)}")
            self.products[url]['scheduled_check'] = self.after(15000, lambda: self.monitor_product(url))

    def update_product_status(self, url, is_available, status_text):
        for item in self.tree.get_children():
            if self.tree.item(item)['values'][0] == url:
                cart_button = '🛒 Add to Cart' if is_available else ''
                self.tree.item(item, values=(url, status_text, '⏹', cart_button))
                break

    def update_product_control(self, url, is_monitoring):
        for item in self.tree.get_children():
            if self.tree.item(item)['values'][0] == url:
                current_values = self.tree.item(item)['values']
                control_text = '⏹' if is_monitoring else '⏵'
                self.tree.item(item, values=(current_values[0], current_values[1], control_text, current_values[3]))
                break

    def log_message(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_display.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_display.see(tk.END)

    def handle_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            item = self.tree.identify_row(event.y)
            column = self.tree.identify_column(event.x)
            
            if column == '#3':  # Action button
                url = self.tree.item(item)['values'][0]
                if self.tree.item(item)['values'][2] == '⏹':
                    self.stop_product_monitoring(url)
                else:
                    self.start_product_monitoring(url)
            elif column == '#4':  # Cart button
                url = self.tree.item(item)['values'][0]
                if self.tree.item(item)['values'][3] == '🛒 Add to Cart':
                    self.main_app.add_to_cart(url)

    def start_product_monitoring(self, url):
        try:
            interval = int(self.interval_entry.get())
            if interval < 5:
                self.log_message("⚠️ Interval too short, using 5 seconds")
                interval = 5
        except ValueError:
            self.log_message("⚠️ Invalid interval, using 15 seconds")
            interval = 15

        # Create a new monitoring tab for this product
        product_name = url.split('/')[-1]  # Use product ID as temporary name
        tab_name = f"Monitor_{product_name}"
        
        if tab_name in self.main_app.monitor_tabs:
            self.log_message(f"⚠️ Already monitoring {product_name}")
            return
        
        try:
            # Create new monitoring tab
            monitor_tab = ProductMonitorTab(self.notebook, url, self.main_app)
            self.main_app.monitor_tabs[tab_name] = monitor_tab
            self.notebook.add(monitor_tab, text=f"📊 {product_name}")
            self.notebook.select(monitor_tab)
            
            # Clear the product from the main list
            for item in self.tree.get_children():
                if self.tree.item(item)['values'][0] == url:
                    self.tree.delete(item)
                    break
            
            # Remove from products dictionary in main GUI
            if url in self.main_app.products:
                del self.main_app.products[url]
            
            # Reset URL entry and store selection for new products
            self.main_app.url_entry.delete(0, tk.END)
            self.main_app.search_entry.delete(0, tk.END)
            
            # Clear search results
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            
            self.log_message(f"▶ Started monitoring: {url}")
            
        except Exception as e:
            self.log_message(f"❌ Error creating monitoring tab: {str(e)}")

    def stop_product_monitoring(self, url):
        if url in self.products and self.products[url]['scheduled_check']:
            self.after_cancel(self.products[url]['scheduled_check'])
            self.products[url]['scheduled_check'] = None
        self.update_product_control(url, False)
        self.log_message(f"⏹ Stopped monitoring: {url}")

class ProductMonitorTab(ttk.Frame):
    def __init__(self, parent, url, main_app):
        super().__init__(parent)
        self.url = url
        self.main_app = main_app
        self.notebook = parent
        
        # Initialize monitoring state
        self.scheduled_check = None
        
        # Use main app's style
        self.style = main_app.style
        
        # Create monitoring interface
        self.create_monitor_interface()
        
        # Start monitoring
        self.start_monitoring()

    def create_monitor_interface(self):
        # Control panel
        control_frame = ttk.LabelFrame(self, text=" Controls ", style='Custom.TLabelframe')
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        controls = ttk.Frame(control_frame, style='Custom.TFrame')
        controls.pack(fill=tk.X, padx=10, pady=10)
        
        # Stop button
        self.stop_button = ttk.Button(
            controls,
            text="⏹ Stop Monitoring",
            style='Custom.TButton',
            command=self.stop_monitoring
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Status and interval
        ttk.Label(controls, text="Check Interval (sec):", background='#f0f0f0').pack(side=tk.LEFT, padx=(20, 5))
        self.interval_entry = ttk.Entry(controls, width=5)
        self.interval_entry.insert(0, self.main_app.interval_entry.get())
        self.interval_entry.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(
            controls,
            text="Status: Running",
            background='#f0f0f0',
            font=('Arial', 10, 'bold')
        )
        self.status_label.pack(side=tk.RIGHT, padx=5)
        
        # Activity log
        self.log_frame = ttk.LabelFrame(self, text=" Activity Log ", style='Custom.TLabelframe')
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_display = scrolledtext.ScrolledText(
            self.log_frame,
            height=10,
            font=('Consolas', 10),
            background='#ffffff'
        )
        self.log_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def start_monitoring(self):
        self.monitor_product()
        self.log_message(f"Started monitoring: {self.url}")

    def stop_monitoring(self):
        if self.scheduled_check:
            self.after_cancel(self.scheduled_check)
            self.scheduled_check = None
        
        # Remove tab
        tab_name = f"Monitor_{self.url.split('/')[-1]}"
        self.main_app.monitor_tabs.pop(tab_name, None)
        self.notebook.forget(self)
        
        self.log_message("⏹ Stopped monitoring")

    def monitor_product(self):
        try:
            is_available, product_name, status_details = self.main_app.check_stock(self.url)
            
            # Log status
            status_message = (
                f"Checking: {status_details['name']}\n"
                f"Status: {status_details['status']}\n"
                f"Stock: {status_details['stock']}\n"
                f"Purchasable: {status_details['purchasable']}"
            )
            self.log_message(status_message)
            
            # Schedule next check
            interval = int(self.interval_entry.get()) * 1000
            self.scheduled_check = self.after(interval, self.monitor_product)
            
            # Update status label with last check time
            check_time = datetime.now().strftime("%H:%M:%S")
            self.status_label.config(text=f"Status: Running (Last check: {check_time})")
            
            # Show notification if item becomes available
            if is_available:
                notification.notify(
                    title='Product In Stock!',
                    message=f'{status_details["name"]} is now available!\n{status_details["stock"]} units in stock',
                    timeout=10
                )
            
        except Exception as e:
            self.log_message(f"❌ Error monitoring: {str(e)}")
            self.scheduled_check = self.after(15000, self.monitor_product)

    def log_message(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_display.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_display.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = StockMonitorGUI(root)
    root.mainloop() 