from typing import List, Dict, Optional, Tuple
import tkinter as tk
from tkinter import ttk
from .base_monitor import BaseMonitor
from datetime import datetime, timedelta
import logging
from plyer import notification


class ProfileMonitor(BaseMonitor):
    """Monitor multiple products with profile/task management."""

    def __init__(self, parent, profile_name: str, products: List[Dict], main_app):
        """Initialize the monitor."""
        # Initialize base class first
        super().__init__(parent, main_app)

        # Core state
        self.profile_name = profile_name
        self.is_profile = not profile_name.startswith("Task_")
        self.products = {}
        self.paused = False
        self.active = False  # Track monitoring state

        # Performance optimizations
        self._cache = {}  # Cache for product info
        self._check_times = {}  # Track check times
        self._max_log_lines = 1000  # Maximum log lines to keep

        # UI components (initialized in setup_ui)
        self.control_frame = None
        self.tree = None
        self.log_display = None
        self.interval_entry = None
        self.status_label = None
        self.pause_button = None

        # New state variables
        self.spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_index = 0
        self.spinner_after_id = None

        # Initialize UI and start monitoring
        self.setup_ui()
        self._initialize_products(products)
        self.update_activity_indicator()

    def setup_ui(self):
        """Initialize the UI components."""
        # Create frames first
        self.control_frame = None
        self.tree = None
        self.log_display = None

        # Then create UI components
        self.create_control_panel()
        self.create_products_list()
        self.create_log_frame()

    def create_control_panel(self):
        """Create the control panel with modern styling."""
        title = (
            f" {self.profile_name} Controls " if self.is_profile else " Task Controls "
        )

        self.control_frame = ttk.Frame(self, style="Custom.TFrame")
        self.control_frame.pack(fill=tk.X, padx=20, pady=(20, 10))

        # Header
        header_frame = ttk.Frame(self.control_frame, style="Custom.TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(header_frame, text=title, style="Header.TLabel").pack(side=tk.LEFT)

        # Controls container
        controls = ttk.Frame(self.control_frame, style="Custom.TFrame")
        controls.pack(fill=tk.X)

        # Left side - Control buttons
        buttons_frame = ttk.Frame(controls, style="Custom.TFrame")
        buttons_frame.pack(side=tk.LEFT)

        self.stop_button = ttk.Button(
            buttons_frame,
            text="⏹ Stop",
            style="Custom.TButton",
            command=self.stop_monitoring,
        )
        self.stop_button.pack(side=tk.LEFT, padx=(0, 5))

        self.pause_button = ttk.Button(
            buttons_frame,
            text="⏸️ Pause",
            style="Custom.TButton",
            command=self.toggle_pause,
        )
        self.pause_button.pack(side=tk.LEFT, padx=5)

        # Right side - Interval and status
        right_frame = ttk.Frame(controls, style="Custom.TFrame")
        right_frame.pack(side=tk.RIGHT)

        # Interval control with modern styling
        interval_frame = ttk.Frame(right_frame, style="Custom.TFrame")
        interval_frame.pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(interval_frame, text="Check Interval", style="Status.TLabel").pack(
            side=tk.LEFT, padx=(0, 5)
        )

        self.interval_entry = ttk.Entry(interval_frame, width=5, font=("Segoe UI", 10))
        self.interval_entry.insert(0, self.main_app.interval_entry.get())
        self.interval_entry.pack(side=tk.LEFT)

        ttk.Label(interval_frame, text="seconds", style="Status.TLabel").pack(
            side=tk.LEFT, padx=(5, 0)
        )

        # Status label with modern styling
        self.status_label = ttk.Label(
            right_frame, text="Status: Starting...", style="Status.TLabel"
        )
        self.status_label.pack(side=tk.RIGHT)

    def create_products_list(self):
        """Create products list with modern styling."""
        list_frame = ttk.Frame(self, style="Custom.TFrame")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Header
        ttk.Label(list_frame, text="Monitored Products", style="Header.TLabel").pack(
            anchor=tk.W, pady=(0, 10)
        )

        # Create treeview with modern styling
        tree_frame = ttk.Frame(list_frame, style="Custom.TFrame")
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("Name", "URL", "Status", "Activity"),
            show="headings",
            style="Custom.Treeview",
        )

        # Configure modern scrollbar
        scrollbar = ttk.Scrollbar(
            tree_frame, orient=tk.VERTICAL, command=self.tree.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Configure columns with modern widths
        self.tree.column("Name", width=400, anchor=tk.W)
        self.tree.column("URL", width=400, anchor=tk.W)
        self.tree.column("Status", width=150, anchor=tk.CENTER)
        self.tree.column("Activity", width=100, anchor=tk.CENTER)

        # Configure modern headings
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col, anchor=tk.W)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def create_log_frame(self):
        """Create the log display."""
        log_frame = ttk.LabelFrame(
            self, text=" Activity Log ", style="Custom.TLabelframe"
        )
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.log_display = tk.Text(
            log_frame,
            height=10,
            font=("Consolas", 10),
            background="#ffffff",
            wrap=tk.WORD,
        )
        self.log_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def start_monitoring(self):
        """Start monitoring all products."""
        if not self.products:
            self.log_message("No products to monitor")
            return

        self.paused = False
        self.active = True
        self.status_label.config(text="Status: Running")

        # Start spinner animation
        self._update_spinner()

        # Log start message
        self.log_message(f"Started monitoring {len(self.products)} products")

        # Start monitoring each product
        for url in self.products.keys():
            self.check_product(url)

    def check_product(self, url: str) -> None:
        """Check product stock status and update UI."""
        if self.paused or url not in self.products:
            return

        # Check rate limiting
        if not self._check_rate_limit(url):
            return

        try:
            product = self.products[url]

            # Check cache first
            cached_info = self._get_cached_product_info(url)
            if cached_info:
                self._update_product_state(url, **cached_info)
                return

            # Perform actual check
            is_available, name, details = self.main_app.check_stock(url)
            current_time = datetime.now().strftime("%H:%M:%S")

            # Cache the result
            self._cache[url] = (
                datetime.now(),
                {
                    "name": name,
                    "is_available": is_available,
                    "details": details,
                    "current_time": current_time,
                },
            )

            # Update state and UI
            self._update_product_state(url, name, is_available, details, current_time)

            # Reset retry count on success
            product["retry_count"] = 0

            # Schedule next check
            interval_ms = int(self.interval_entry.get()) * 1000
            product["scheduled_check"] = self.after(
                interval_ms, lambda: self.check_product(url)
            )

        except Exception as e:
            self._handle_check_error(url, str(e))

    def _check_rate_limit(self, url: str, min_interval: int = 5) -> bool:
        """Check if enough time has passed since last check."""
        now = datetime.now()
        if url in self._check_times:
            if (now - self._check_times[url]).seconds < min_interval:
                return False
        self._check_times[url] = now
        return True

    def _get_cached_product_info(self, url: str, max_age: int = 300) -> Optional[Dict]:
        """Get cached product info if not expired."""
        if url in self._cache:
            cache_time, info = self._cache[url]
            if (datetime.now() - cache_time).seconds < max_age:
                return info
        return None

    def _update_product_state(
        self, url: str, name: str, is_available: bool, details: Dict, current_time: str
    ) -> None:
        """Update product state and UI efficiently."""
        try:
            status = (
                f"In Stock ({details['stock']})" if is_available else "Out of Stock"
            )

            # Update tree with activity indicator
            if item := self.find_tree_item(url):
                self.tree.item(
                    item,
                    values=(
                        self.main_app.format_product_name(name),
                        url,
                        status,
                        "🔄",  # Active checking indicator
                    ),
                )

                # Schedule indicator reset after 1 second
                self.after(1000, lambda: self._reset_activity_indicator(item))

            # Log and notify
            self.log_message(f"Checking {name}: {status}")
            if is_available:
                self.notify_stock_available(name, details["stock"])
        except Exception as e:
            self.log_message(f"Error updating product state: {str(e)}")

    def _reset_activity_indicator(self, item):
        """Reset the activity indicator after check."""
        try:
            current_values = self.tree.item(item)["values"]
            if current_values:
                self.tree.item(
                    item,
                    values=(
                        current_values[0],
                        current_values[1],
                        current_values[2],
                        "⚪",  # Reset to inactive
                    ),
                )
        except Exception as e:
            self.log_message(f"Error resetting activity indicator: {str(e)}")

    def _batch_update_tree(self, updates: List[Tuple[str, Tuple]]) -> None:
        """Batch update tree items for better performance."""
        try:
            for url, values in updates:
                if item := self.find_tree_item(url):
                    self.tree.item(item, values=values)
        except Exception as e:
            self.log_message(f"Error updating tree: {str(e)}")

    def find_tree_item(self, url: str) -> str:
        """Efficiently find tree item by URL."""
        for item in self.tree.get_children():
            values = self.tree.item(item)["values"]
            if values and values[1] == url:  # URL is in second column
                return item
        return None

    def schedule_next_check(self, url: str, interval_ms: int):
        """Schedule next check with error handling."""
        try:
            self.products[url]["scheduled_check"] = self.after(
                interval_ms, lambda: self.check_product(url)
            )
        except Exception as e:
            self.log_message(f"Error scheduling check for {url}: {str(e)}")

    def notify_stock_available(self, product_name: str, stock_count: int):
        """Send stock availability notification."""
        notification.notify(
            title="Product In Stock!",
            message=f"{product_name} is now available!\n{stock_count} units in stock",
            timeout=10,
        )

    def stop_monitoring(self):
        """Stop monitoring all products."""
        try:
            # Cancel all scheduled checks
            for url in self.products:
                if self.products[url]["scheduled_check"]:
                    self.after_cancel(self.products[url]["scheduled_check"])
                    self.products[url]["scheduled_check"] = None

            # Stop spinner animation
            if self.spinner_after_id:
                self.after_cancel(self.spinner_after_id)
                self.spinner_after_id = None

            # Update all items to show stopped state
            for item in self.tree.get_children():
                values = self.tree.item(item)["values"]
                if values:
                    self.tree.item(
                        item,
                        values=(
                            values[0],
                            values[1],
                            values[2],
                            "⏹",  # Stopped indicator
                        ),
                    )

            self.products.clear()
            self.active = False
            self.log_message("Stopped monitoring all products")

        except Exception as e:
            self.log_message(f"Error stopping monitoring: {str(e)}")

    def toggle_pause(self) -> None:
        """Toggle monitoring pause state."""
        self.paused = not self.paused
        self.active = not self.paused
        self.update_activity_indicator()

        if self.paused:
            self._pause_monitoring()
        else:
            self._resume_monitoring()

    def _pause_monitoring(self) -> None:
        """Pause all monitoring."""
        self.pause_button.config(text="▶️ Resume All")
        self.status_label.config(text="Status: Paused")

        # Stop spinner animation
        if self.spinner_after_id:
            self.after_cancel(self.spinner_after_id)
            self.spinner_after_id = None

        # Update all items to show paused state
        for item in self.tree.get_children():
            values = self.tree.item(item)["values"]
            if values:
                self.tree.item(
                    item,
                    values=(values[0], values[1], values[2], "⏸"),  # Paused indicator
                )

        for product in self.products.values():
            if product["scheduled_check"]:
                self.after_cancel(product["scheduled_check"])

        self.log_message("Paused monitoring")

    def _resume_monitoring(self) -> None:
        """Resume all monitoring."""
        self.pause_button.config(text="⏸️ Pause All")
        self.status_label.config(text="Status: Running")

        for url in self.products:
            self.check_product(url)

        self.log_message("Resumed monitoring")

    def add_product(self, product: Dict):
        """Add a product to monitoring."""
        url = product.get("url")
        if not url or url in self.products:
            return

        # Add to products dict first
        self.products[url] = {
            "scheduled_check": None,
            "name": product.get("name", "Unknown"),
            "status": product.get("status", "Not checked"),
            "interval": product.get("interval", self.interval_entry.get()),
        }

        try:
            _, product_name, _ = self.main_app.check_stock(url)
            display_name = self.main_app.format_product_name(product_name)
        except Exception as e:
            self.log_message(f"Error getting initial product info: {str(e)}")
            display_name = product.get("name", "Loading...")

        # Add to tree with initial state indicator
        self.tree.insert(
            "",
            "end",
            values=(display_name, url, "Not checked", "⏹"),  # Initial stopped state
        )

    def _initialize_products(self, products: List[Dict]) -> None:
        """Initialize products and start monitoring if needed."""
        if not products:
            return

        for product in products:
            if url := product.get("url"):  # Using walrus operator for clarity
                self.add_product({"url": url, **product})

        if self.products:
            self.start_monitoring()

    def __del__(self):
        """Ensure cleanup on deletion."""
        self.cleanup()

    def _handle_check_error(self, url: str, error_msg: str) -> None:
        """Enhanced error handling with exponential backoff."""
        self.log_message(f"Error checking {url}: {error_msg}")

        product = self.products[url]
        retry_count = product.get("retry_count", 0)
        retry_delay = min(15 * (2**retry_count), 300)  # Max 5 minutes

        if item := self.find_tree_item(url):
            current_values = self.tree.item(item)["values"]
            self.tree.item(
                item,
                values=(
                    current_values[0],
                    current_values[1],
                    f"Error: Retry in {retry_delay}s",
                    "❌",  # Error indicator
                ),
            )

        product["retry_count"] = retry_count + 1
        product["scheduled_check"] = self.after(
            retry_delay * 1000, lambda: self.check_product(url)
        )

    def log_message(self, message: str) -> None:
        """Log message with optimization."""
        super().log_message(message)

        # Optimize log size
        log_text = self.log_display.get("1.0", tk.END)
        lines = log_text.splitlines()
        if len(lines) > self._max_log_lines:
            self.log_display.delete("1.0", tk.END)
            self.log_display.insert("1.0", "\n".join(lines[-self._max_log_lines :]))

    def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            self.stop_monitoring()
            self._cache.clear()
            self._check_times.clear()
        except Exception as e:
            logging.error(f"Error during cleanup: {str(e)}")

    def update_activity_indicator(self):
        """Update the tab's activity indicator."""
        try:
            # Find our tab
            for i in range(self.main_app.notebook.index("end")):
                if self.main_app.notebook.select(i) == str(self):
                    current_text = self.main_app.notebook.tab(i, "text")
                    # Remove existing indicator if present
                    if current_text.startswith(("⚪", "🟢")):
                        current_text = current_text[2:]
                    # Add appropriate indicator
                    new_text = f"{'🟢' if self.active else '⚪'} {current_text}"
                    self.main_app.notebook.tab(i, text=new_text)
                    break
        except Exception as e:
            self.log_message(f"Error updating activity indicator: {str(e)}")

    def _update_spinner(self):
        """Update the spinner animation for active monitoring."""
        if not self.active or self.paused:
            return

        try:
            self.spinner_index = (self.spinner_index + 1) % len(self.spinner_frames)
            current_frame = self.spinner_frames[self.spinner_index]

            # Update all active items with current spinner frame
            for item in self.tree.get_children():
                values = self.tree.item(item)["values"]
                if values:
                    self.tree.item(
                        item, values=(values[0], values[1], values[2], current_frame)
                    )

            # Schedule next update
            self.spinner_after_id = self.after(100, self._update_spinner)
        except Exception as e:
            self.log_message(f"Error updating spinner: {str(e)}")
