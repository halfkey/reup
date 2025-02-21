from typing import List, Dict
from .base_monitor import BaseMonitor
import tkinter as tk
from tkinter import ttk
from ..config.constants import DEFAULT_INTERVAL, MIN_INTERVAL
from ..utils.helpers import check_stock, parse_url
from plyer import notification
from datetime import datetime


class TaskMonitor(BaseMonitor):
    def __init__(self, notebook, urls: List[str], parent):
        super().__init__(notebook, parent)
        self.notebook = notebook
        self.urls = urls
        self.parent = parent
        self.scheduled_check = None
        self.paused = False
        self.scanning_index = 0  # For animation
        self.scanning_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.tab_chars = [
            "⠋",
            "⠙",
            "⠚",
            "⠞",
            "⠖",
            "⠦",
            "⠴",
            "⠲",
            "⠳",
            "⠓",
        ]  # Smoother animation
        self.tab_index = 0  # For tab animation
        self.tab_animation = None  # For tab animation scheduling

        # Initialize UI components
        self.interval_entry = None
        self.status_label = None
        self.start_button = None
        self.pause_button = None
        self.log_display = None
        self.product_tree = None
        self.found_products = None

        # Create UI
        self.setup_ui()

    def setup_ui(self):
        """Initialize the UI components."""
        # Control panel
        self.control_frame = self.create_control_frame()

        # Product list
        self.create_product_list()

        # Found products section
        self.create_found_products_section()

        # Activity log
        self.log_frame = self.create_log_frame()

    def create_product_list(self):
        """Create product list section."""
        frame = ttk.LabelFrame(self, text=" Products ", style="Custom.TLabelframe")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create treeview with scrollbar
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add separate columns for Play/Pause and Delete
        self.product_tree = ttk.Treeview(
            tree_frame,
            columns=("Name", "URL", "Store", "Status", "Control", "Delete"),
            show="headings",
            yscrollcommand=scrollbar.set,
        )

        # Configure columns
        self.product_tree.heading("Name", text="Product Name", anchor="center")
        self.product_tree.heading("URL", text="URL", anchor="center")
        self.product_tree.heading("Store", text="Store", anchor="center")
        self.product_tree.heading("Status", text="Status", anchor="center")
        self.product_tree.heading("Control", text="Control", anchor="center")
        self.product_tree.heading("Delete", text="Delete", anchor="center")

        self.product_tree.column("Name", width=300, anchor="w")
        self.product_tree.column("URL", width=0, stretch=False)  # Hide URL column
        self.product_tree.column("Store", width=80, anchor="center")
        self.product_tree.column("Status", width=80, anchor="center")
        self.product_tree.column("Control", width=50, anchor="center")
        self.product_tree.column("Delete", width=50, anchor="center")

        self.product_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.product_tree.yview)

        # Bind click event for actions
        self.product_tree.bind("<Button-1>", self.handle_tree_click)

        # Add products to tree
        for url in self.urls:
            store = "Best Buy CA" if "bestbuy" in url.lower() else "Unknown"
            self.product_tree.insert(
                "",
                "end",
                values=(
                    "Loading...",  # Name
                    url,  # URL (hidden)
                    store,  # Store
                    "Monitoring",  # Status
                    "⏸",  # Control button
                    "🗑",  # Delete button
                ),
            )

    def create_control_frame(self) -> ttk.Frame:
        """Create the control panel frame."""
        frame = ttk.LabelFrame(self, text=" Controls ", style="Custom.TLabelframe")
        frame.pack(fill=tk.X, padx=10, pady=5)

        controls = ttk.Frame(frame, style="Custom.TFrame")
        controls.pack(fill=tk.X, padx=10, pady=10)

        # Left side - Control buttons
        buttons_frame = ttk.Frame(controls, style="Custom.TFrame")
        buttons_frame.pack(side=tk.LEFT)

        # Start/Stop button
        self.start_button = ttk.Button(
            buttons_frame,
            text="▶ Start",
            style="Custom.TButton",
            command=self.start_monitoring,
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        # Pause button
        self.pause_button = ttk.Button(
            buttons_frame,
            text="⏸️ Pause",
            style="Custom.TButton",
            command=self.toggle_pause,
        )
        self.pause_button.pack(side=tk.LEFT, padx=5)

        # Right side - Interval control only
        interval_frame = ttk.Frame(controls, style="Custom.TFrame")
        interval_frame.pack(side=tk.RIGHT, padx=5)

        ttk.Label(
            interval_frame, text="Check Interval (sec):", style="Status.TLabel"
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.interval_entry = ttk.Entry(interval_frame, width=5)
        self.interval_entry.insert(0, str(DEFAULT_INTERVAL))
        self.interval_entry.pack(side=tk.LEFT)

        return frame

    def create_log_frame(self) -> ttk.Frame:
        """Create the log frame."""
        frame = ttk.LabelFrame(self, text=" Activity Log ", style="Custom.TLabelframe")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.log_display = tk.Text(
            frame, height=10, font=("Consolas", 10), background="#ffffff", wrap=tk.WORD
        )
        self.log_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Configure tag for new messages
        self.log_display.tag_configure("new_message", justify="left")

        return frame

    def create_found_products_section(self):
        """Create section for products found in stock."""
        frame = ttk.LabelFrame(
            self, text=" Found In Stock ", style="Custom.TLabelframe"
        )
        frame.pack(fill=tk.X, padx=10, pady=5)

        # Create text widget for found products
        self.found_products = tk.Text(
            frame, height=3, wrap=tk.WORD, font=("Consolas", 10), background="#ffffff"
        )
        self.found_products.pack(fill=tk.X, padx=10, pady=5)

        # Configure tag for hyperlinks
        self.found_products.tag_configure("hyperlink", foreground="blue", underline=1)

    def validate_interval(self):
        """Validate the interval value."""
        try:
            interval = int(self.interval_entry.get())
            if interval < MIN_INTERVAL:
                raise ValueError(f"Interval must be at least {MIN_INTERVAL} seconds")
            return interval
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError("Invalid interval")
            raise

    def use_default_interval(self):
        """Reset to default interval."""
        self.interval_entry.delete(0, tk.END)
        self.interval_entry.insert(0, str(DEFAULT_INTERVAL))

    def stop_monitoring(self):
        """Stop monitoring and cleanup."""
        if self.scheduled_check:
            self.after_cancel(self.scheduled_check)
            self.scheduled_check = None

        # Stop tab animation
        if self.tab_animation:
            self.after_cancel(self.tab_animation)
            self.tab_animation = None

        # Update button text back to Start
        self.start_button.config(text="▶ Start", command=self.start_monitoring)

        self.log_message("⏹ Stopped monitoring all products")

        # Remove animation from tab
        current_text = self.notebook.tab(self, "text")
        base_text = current_text.split(" ")[
            -1
        ]  # Get text after any existing indicators
        self.notebook.tab(self, text=base_text)

    def toggle_pause(self):
        """Toggle pause state."""
        self.paused = not self.paused

        if self.paused:
            self.pause_button.config(text="▶️ Resume")
            if self.scheduled_check:
                self.after_cancel(self.scheduled_check)
            if self.tab_animation:
                self.after_cancel(self.tab_animation)
            self.log_message("⏸️ Monitoring paused")

            # Remove animation while paused
            current_text = self.notebook.tab(self, "text")
            base_text = current_text.split(" ")[-1]
            self.notebook.tab(self, text=base_text)
        else:
            self.pause_button.config(text="⏸️ Pause")
            self.log_message("▶️ Monitoring resumed")
            self.monitor_products()

            # Resume tab animation
            current_text = self.notebook.tab(self, "text")
            base_text = current_text.split(" ")[-1]
            self.notebook.tab(self, text=f"{self.tab_chars[0]} {base_text}")
            self.update_tab_animation()

    def handle_monitoring_error(self, error: Exception):
        """Handle monitoring errors."""
        self.log_message(f"❌ Error monitoring: {str(error)}")

    def start_monitoring(self):
        """Start monitoring all products."""
        try:
            self.validate_interval()
            self.log_message("Starting monitoring for all products...")
            self.monitor_products()
            self.start_button.config(text="Stop", command=self.stop_monitoring)

            # Start tab animation - just the animated dots
            current_text = self.notebook.tab(self, "text")
            base_text = current_text.split(" ")[
                -1
            ]  # Get text after any existing indicators
            self.notebook.tab(self, text=f"{self.tab_chars[0]} {base_text}")
            self.update_tab_animation()

        except ValueError as e:
            self.log_message(f"Warning: {str(e)}")
            self.use_default_interval()
            self.monitor_products()

    def update_scanning_animation(self):
        """Update the scanning animation in the status."""
        if not self.paused and self.scheduled_check:
            self.scanning_index = (self.scanning_index + 1) % len(self.scanning_chars)
            current_status = self.status_label.cget("text")
            if "Checking" in current_status:
                self.status_label.config(
                    text=f"Checking {self.scanning_chars[self.scanning_index]}"
                )
            self.after(100, self.update_scanning_animation)

    def monitor_products(self):
        """Monitor all products."""
        if self.paused:
            return

        try:
            total_products = len(self.product_tree.get_children())
            checked_products = 0
            active_products = False  # Track if any products still need monitoring

            for item in self.product_tree.get_children():
                values = self.product_tree.item(item)["values"]
                url = values[1]  # Get URL from second column
                status = values[3]  # Status is fourth column

                # Skip products that are paused or already found
                if status in ["Paused", "Restock"]:
                    continue

                active_products = True
                self.log_message(f"Checking product: {url}")

                try:
                    product_id = parse_url(url)
                    success, name, result = check_stock(product_id)
                    checked_products += 1

                    if success and result:
                        stock = result.get("stock", "Unknown")

                        # If product is in stock
                        if stock == "1":
                            # Update status to Restock and pause monitoring
                            self.product_tree.item(
                                item,
                                values=(
                                    name or "Unknown Product",
                                    url,
                                    (
                                        "Best Buy CA"
                                        if "bestbuy" in url.lower()
                                        else "Unknown"
                                    ),
                                    "Restock",  # Changed from 'Found' to 'Restock'
                                    "▶",  # Show play button
                                    "🗑",  # Keep delete button
                                ),
                            )
                            self.notify_stock_available(name, stock, url)
                            self.add_found_product(name, url)
                            self.log_message(
                                f"✅ Found {name} in stock! Pausing monitoring for this item."
                            )
                        else:
                            # Normal status update for not-found items
                            self.update_product_status(
                                item, name or "Unknown Product", url, stock
                            )
                    else:
                        self.update_product_status(item, "Error Loading", url, "0")

                except Exception as e:
                    self.log_message(f"❌ Error checking {url}: {str(e)}")
                    self.update_product_status(item, "Error", url, "0")

            # If all products are found in stock, stop the task
            if not active_products:
                self.log_message("🎉 All products found in stock! Stopping task.")
                self.stop_monitoring()
                return

            # Schedule next check if not paused and there are still products to monitor
            if not self.paused:
                interval = self.validate_interval() * 1000  # Convert to milliseconds
                self.scheduled_check = self.after(interval, self.monitor_products)

        except Exception as e:
            self.log_message(f"❌ Error monitoring: {str(e)}")
            # Retry after interval even if error occurs
            if not self.paused:
                interval = self.validate_interval() * 1000
                self.scheduled_check = self.after(interval, self.monitor_products)

    def update_product_status(self, item, name, url, stock):
        """Update the status of a product in the tree view."""
        try:
            status_text = "Monitoring"
            control_button = "⏸"  # Default control button
            store = "Best Buy CA" if "bestbuy" in url.lower() else "Unknown"

            # If product is in stock, we'll stop monitoring it
            if stock == "1":
                status_text = "Restock"  # Changed from 'Found' to 'Restock'
                self.product_tree.tag_configure(item, foreground="green")

            # Update the item with new values
            self.product_tree.item(
                item,
                values=(
                    name,
                    url,
                    store,
                    status_text,
                    control_button,
                    "🗑",  # Delete button always available
                ),
            )

            self.log_message(f"📊 Updated {name}: {status_text}")

        except Exception as e:
            self.log_message(f"⚠️ Error updating product status: {str(e)}")

    def notify_stock_available(self, product_name: str, stock_count: int, url: str):
        """Send notification for stock availability."""
        message = f"{product_name} is now available!\n{stock_count} units in stock"
        self.log_message(f"ALERT: {message}")

        try:
            notification.notify(
                title="Product In Stock!", message=message, timeout=10, app_name="Reup"
            )

            # Log message without clickable URL
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_display.insert(
                "end", f"[{timestamp}] Product found in stock!\n", "new_message"
            )

        except Exception as e:
            self.log_message(f"⚠️ Could not send notification: {str(e)}")

    def open_url(self, url):
        """Open URL in default browser."""
        import webbrowser

        webbrowser.open(url)

    def log_message(self, message: str):
        """Log a message to the activity log."""
        if hasattr(self, "log_display") and self.log_display is not None:
            # Add timestamp
            timestamp = datetime.now().strftime("%H:%M:%S")
            full_message = f"[{timestamp}] {message}\n"

            # Insert at the end and scroll to see the new message
            self.log_display.insert("end", full_message, "new_message")
            self.log_display.see("end")  # Auto-scroll to the bottom

            # Limit the number of lines (optional)
            lines = int(self.log_display.index("end-1c").split(".")[0])
            if lines > 1000:  # Keep last 1000 lines
                self.log_display.delete("1.0", "501.0")  # Remove oldest lines

    def update_tab_animation(self):
        """Update the tab name animation."""
        if not self.paused and self.scheduled_check:
            self.tab_index = (self.tab_index + 1) % len(self.tab_chars)
            current_text = self.notebook.tab(self, "text")
            base_text = current_text.split(" ")[
                -1
            ]  # Get text after any existing indicators
            self.notebook.tab(
                self, text=f"{self.tab_chars[self.tab_index]} {base_text}"
            )
            self.tab_animation = self.after(100, self.update_tab_animation)

    def check_stock(self):
        """Check stock for all URLs."""
        if not self.scheduled_check:
            return

        try:
            # Update scanning animation
            self.scanning_index = (self.scanning_index + 1) % len(self.scanning_chars)
            self.status_label.config(
                text=f"Scanning {self.scanning_chars[self.scanning_index]}"
            )

            for item in self.product_tree.get_children():
                url = self.product_tree.item(item)["values"][
                    1
                ]  # Get URL from second column
                name = self.product_tree.item(item)["values"][
                    0
                ]  # Get name from first column

                result = check_stock(url)
                if result:
                    stock = result.get("stock", "Unknown")

                    # Update item with new values - no price
                    self.update_product_status(item, name, url, stock)

                    # Notify if stock becomes available
                    if stock not in ["Out of Stock", "Unknown"] and stock != "0":
                        self.notify_stock_available(name, stock, url)

            # Schedule next check
            if not self.paused:
                interval = int(self.interval_entry.get())
                self.scheduled_check = self.after(interval * 1000, self.check_stock)

        except Exception as e:
            self.log_message(f"⚠️ Error checking stock: {str(e)}")

    def add_found_product(self, name: str, url: str):
        """Add a found product to the list with clickable URL."""
        timestamp = datetime.now().strftime("%H:%M:%S")

        def add_to_list(text_widget):
            if text_widget:
                # Get current number of items
                content = text_widget.get("1.0", "end-1c")
                item_number = len(content.split("\n")) + 1 if content.strip() else 1

                # Format name to be shorter if needed
                short_name = name[:50] + "..." if len(name) > 50 else name

                # Add numbered list item with timestamp and name
                text_widget.insert(
                    "end", f"{item_number}. [{timestamp}] {short_name} - ", "normal"
                )

                # Add URL
                text_widget.insert("end", url, "hyperlink")

                # Add space and Open button
                text_widget.insert("end", " [", "normal")
                text_widget.insert("end", "Open", "button")
                text_widget.insert("end", "]\n", "normal")

                # Configure URL hyperlink
                url_tag = f"link_{timestamp}"
                last_line_start = text_widget.index("end-2c linestart")
                url_start = f"{last_line_start} linestart+{len(f'{item_number}. [{timestamp}] {short_name} - ')}c"
                url_end = f"{last_line_start} linestart+{len(f'{item_number}. [{timestamp}] {short_name} - {url}')}c"
                text_widget.tag_add(url_tag, url_start, url_end)
                text_widget.tag_configure(url_tag, foreground="blue", underline=1)
                text_widget.tag_bind(
                    url_tag, "<Button-1>", lambda e, url=url: self.open_url(url)
                )

                # Configure Open button
                button_tag = f"button_{timestamp}"
                button_start = f"{last_line_start} linestart+{len(f'{item_number}. [{timestamp}] {short_name} - {url} [')}c"
                button_end = f"{last_line_start} linestart+{len(f'{item_number}. [{timestamp}] {short_name} - {url} [Open')}c"
                text_widget.tag_add(button_tag, button_start, button_end)
                text_widget.tag_configure(button_tag, foreground="green", underline=1)
                text_widget.tag_bind(
                    button_tag, "<Button-1>", lambda e, url=url: self.open_url(url)
                )
                text_widget.tag_bind(
                    button_tag, "<Enter>", lambda e: text_widget.config(cursor="hand2")
                )
                text_widget.tag_bind(
                    button_tag, "<Leave>", lambda e: text_widget.config(cursor="")
                )

                # Scroll to show the new entry
                text_widget.see("end")

        # Add to task monitor's found products list
        if hasattr(self, "found_products") and self.found_products:
            add_to_list(self.found_products)

        # Add to main window's found products list
        if hasattr(self.parent, "found_products") and self.parent.found_products:
            add_to_list(self.parent.found_products)

    def handle_tree_click(self, event):
        """Handle click events on the product tree."""
        region = self.product_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.product_tree.identify_column(event.x)
            item = self.product_tree.identify_row(event.y)
            if item and (column == "#5" or column == "#6"):  # Control or Delete column
                values = self.product_tree.item(item)["values"]
                if values:
                    if column == "#5":  # Control column
                        self.handle_pause_resume(item, values)
                    else:  # Delete column
                        self.handle_delete(item, values)

    def handle_pause_resume(self, item, values):
        """Handle pause/resume button click."""
        name = values[0]
        url = values[1]
        store = values[2]
        status = values[3]

        if status == "Monitoring":
            # Pause monitoring
            self.product_tree.item(item, values=(name, url, store, "Paused", "▶", "🗑"))
            self.log_message(f"Paused monitoring for {name}")
        else:
            # Resume monitoring
            self.product_tree.item(
                item, values=(name, url, store, "Monitoring", "⏸", "🗑")
            )
            self.log_message(f"Resumed monitoring for {name}")

    def handle_delete(self, item, values):
        """Handle delete button click."""
        name = values[0]
        self.product_tree.delete(item)
        self.log_message(f"Removed {name} from monitoring")
