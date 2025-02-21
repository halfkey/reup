from typing import Optional, Dict
from .base_monitor import BaseMonitor
import tkinter as tk
from tkinter import ttk
from ..config.constants import DEFAULT_INTERVAL, MIN_INTERVAL
from ..config.styles import STYLES
from ..utils.helpers import check_stock, get_timestamp, parse_url
from ..utils.exceptions import StockCheckError, APIError, URLError
from plyer import notification

class ProductMonitor(BaseMonitor):
    def __init__(self, notebook, url, parent, test_mode=False):
        # Pass both notebook and parent as main_app to BaseMonitor
        super().__init__(notebook, parent)  # parent will serve as main_app
        self.notebook = notebook
        self.url = url
        self.parent = parent
        self.test_mode = test_mode
        self.scheduled_check = None
        self.paused = False
        
        # Initialize UI components as None
        self.interval_entry = None
        self.status_label = None
        self.start_button = None
        self.pause_button = None
        self.log_display = None
        
        # Create UI
        self.setup_ui()
        
        # Initialize monitoring status
        self.status = {
            'last_check': None,
            'last_status': None,
            'error_count': 0
        }

    def setup_ui(self):
        """Initialize the UI components."""
        # Control panel
        self.control_frame = self.create_control_frame()
        
        # Activity log
        self.log_frame = self.create_log_frame()

    def create_control_frame(self) -> ttk.Frame:
        """Create the control panel frame."""
        frame = ttk.LabelFrame(self, text=" Controls ", style='Custom.TLabelframe')
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        controls = ttk.Frame(frame, style='Custom.TFrame')
        controls.pack(fill=tk.X, padx=10, pady=10)
        
        # Left side - Control buttons
        buttons_frame = ttk.Frame(controls, style='Custom.TFrame')
        buttons_frame.pack(side=tk.LEFT)
        
        # Start/Stop button
        self.start_button = ttk.Button(
            buttons_frame,
            text="▶ Start",
            style='Custom.TButton',
            command=self.start_monitoring  # Direct connection to start_monitoring
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # Pause button
        self.pause_button = ttk.Button(
            buttons_frame,
            text="⏸️ Pause",
            style='Custom.TButton',
            command=self.toggle_pause  # Direct connection to toggle_pause
        )
        self.pause_button.pack(side=tk.LEFT, padx=5)
        
        # Right side - Interval and status
        right_frame = ttk.Frame(controls, style='Custom.TFrame')
        right_frame.pack(side=tk.RIGHT)
        
        # Interval control
        interval_frame = ttk.Frame(right_frame, style='Custom.TFrame')
        interval_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(
            interval_frame,
            text="Check Interval (sec):",
            style='Status.TLabel'
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.interval_entry = ttk.Entry(interval_frame, width=5)
        self.interval_entry.insert(0, str(DEFAULT_INTERVAL))
        self.interval_entry.pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_label = ttk.Label(
            right_frame,
            text="Status: Ready",
            style='Status.TLabel'
        )
        self.status_label.pack(side=tk.RIGHT, padx=5)
        
        return frame

    def create_log_frame(self) -> ttk.Frame:
        """Create the log frame."""
        frame = ttk.LabelFrame(self, text=" Activity Log ", style='Custom.TLabelframe')
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_display = tk.Text(
            frame,
            height=10,
            font=('Consolas', 10),
            background='#ffffff',
            wrap=tk.WORD
        )
        self.log_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        return frame

    def start_monitoring(self):
        """Start the monitoring process."""
        try:
            print("Starting monitoring...")
            self.validate_interval()
            self.monitor_product()  # Start the monitoring loop
            self.log_message(f"Started monitoring: {self.url}")
            
            # Update button text
            self.start_button.config(text="⏹ Stop", command=self.stop_monitoring)
            
            # Update status in main window's product tree
            if hasattr(self.parent, 'product_tree'):
                for item in self.parent.product_tree.get_children():
                    values = self.parent.product_tree.item(item)['values']
                    if values[1] == self.url:  # Match URL
                        self.parent.product_tree.item(item, values=(
                            values[0],  # Keep existing name
                            self.url,
                            'Monitoring',
                            '⏹',  # Stop button
                            values[4]  # Keep existing cart status
                        ))
                        break
                    
        except ValueError as e:
            self.log_message(f"⚠️ {str(e)}")
            self.use_default_interval()
            self.monitor_product()

    def validate_interval(self) -> int:
        """Validate and return the check interval in seconds.
        
        Returns:
            int: The validated interval in seconds, using defaults for invalid input
        """
        try:
            interval_str = self.interval_entry.get().strip()
            if not interval_str:
                return DEFAULT_INTERVAL
            
            interval = int(interval_str)
            if interval <= 0:
                return MIN_INTERVAL
            
            return max(interval, MIN_INTERVAL)
        
        except ValueError:
            return DEFAULT_INTERVAL

    def use_default_interval(self):
        """Reset to default interval."""
        self.interval_entry.delete(0, tk.END)
        self.interval_entry.insert(0, str(DEFAULT_INTERVAL))

    def monitor_product(self):
        """Check product stock status."""
        if self.paused:
            return
            
        try:
            print("Starting monitor_product check...")
            success, name, status = self.check_stock()
            
            if success and status:
                self.handle_stock_status(success, name, status)
                
                # Update status in main window's product tree
                if hasattr(self.parent, 'product_tree'):
                    for item in self.parent.product_tree.get_children():
                        values = self.parent.product_tree.item(item)['values']
                        if values[1] == self.url:  # Match URL
                            self.parent.product_tree.item(item, values=(
                                name,
                                self.url,
                                status.get('status', 'Unknown'),
                                '⏹',  # Stop button
                                '🛒 Add to Cart' if status.get('purchasable') == 'Yes' else ''
                            ))
                            break
                
            # Schedule next check
            interval = self.validate_interval() * 1000  # Convert to milliseconds
            self.scheduled_check = self.after(interval, self.monitor_product)
            
        except Exception as e:
            self.handle_monitoring_error(e)
            # Ensure next check is scheduled even after error
            interval = self.validate_interval() * 1000
            self.scheduled_check = self.after(interval, self.monitor_product)

    def handle_stock_status(self, is_available: bool, product_name: str, status_details: Dict):
        """Handle the stock status response."""
        self.log_status(status_details)
        self.update_status_label(status_details)
        
        if is_available and self.status['last_status'] != is_available:
            self.notify_stock_available(product_name, status_details['stock'])
        
        self.status['last_status'] = is_available
        self.status['last_check'] = get_timestamp()

    def handle_monitoring_error(self, error: Exception):
        """Handle monitoring errors."""
        self.status['error_count'] += 1
        self.log_message(f"❌ Error monitoring: {str(error)}")
        
        if self.status['error_count'] >= 3:
            self.log_message("⚠️ Multiple errors occurred, consider checking the connection")

    def toggle_pause(self):
        """Toggle pause state."""
        self.paused = not self.paused
        
        if self.paused:
            self.pause_button.config(text="▶️ Resume")
            self.status_label.config(text="Status: Paused")
            if self.scheduled_check:
                self.after_cancel(self.scheduled_check)
            self.log_message("⏸️ Monitoring paused")
        else:
            self.pause_button.config(text="⏸️ Pause")
            self.status_label.config(text="Status: Running")
            self.log_message("▶️ Monitoring resumed")
            self.monitor_product()

    def stop_monitoring(self):
        """Stop monitoring and cleanup."""
        if self.scheduled_check:
            self.after_cancel(self.scheduled_check)
            self.scheduled_check = None
        
        # Update button text back to Start
        self.start_button.config(text="▶ Start", command=self.start_monitoring)
        
        self.log_message("⏹ Stopped monitoring")
        
        # Update status in main window's product tree
        if hasattr(self.parent, 'product_tree'):
            for item in self.parent.product_tree.get_children():
                values = self.parent.product_tree.item(item)['values']
                if values[1] == self.url:
                    self.parent.product_tree.item(item, values=(
                        values[0],
                        self.url,
                        'Stopped',
                        '▶',
                        values[4]
                    ))
                    break
        
        # Don't call cleanup here - let the user close the tab manually
        self.status_label.config(text="Status: Stopped")

    def cleanup(self):
        """Perform cleanup operations."""
        try:
            tab_name = f"Monitor_{self.url.split('/')[-1]}"
            self.notebook.forget(tab_name)
        except Exception as e:
            self.log_error(f"Error during cleanup: {str(e)}")

    def log_status(self, status_details: Dict):
        """Log the current stock status."""
        status_text = (
            f"Name: {status_details['name']}\n"
            f"Stock: {status_details['stock']} units\n"
            f"Status: {status_details['status']}\n"
            f"Purchasable: {status_details['purchasable']}"
        )
        self.log_message(f"📊 Stock Status:\n{status_text}")

    def update_status_label(self, status_details):
        """Update status label with current information."""
        if not status_details:
            status_text = "Status: Unknown (0 units)"
        else:
            status = status_details.get('status', 'Unknown')
            if status is None:
                status = 'Unknown'
            stock = status_details.get('stock', 0)
            if not isinstance(stock, (int, float)):
                stock = 0
            status_text = f"Status: {status} ({stock} units)"
        self.status_label.config(text=status_text)
        
        # Update status indicator in tab
        if hasattr(self.notebook, 'tabs'):
            tabs = self.notebook.tabs()
            if isinstance(tabs, list):
                for i, tab in enumerate(tabs):
                    if self.notebook.select(i) == str(self):
                        current_text = self.notebook.tab(i, "text")
                        # Remove existing indicator if present
                        if current_text.startswith(("⚪", "🟢")):
                            current_text = current_text[2:]
                        # Add appropriate indicator
                        purchasable = status_details.get('purchasable', 'No') if status_details else 'No'
                        new_text = f"{'🟢' if purchasable == 'Yes' else '⚪'} {current_text}"
                        self.notebook.tab(i, text=new_text)
                        break

    def notify_stock_available(self, product_name: str, stock_count: int):
        """Send notification for stock availability."""
        message = f"{product_name} is now available!\n{stock_count} units in stock"
        self.log_message(f"🔔 ALERT: {message}")
        
        try:
            notification.notify(
                title='Product In Stock!',
                message=message,
                timeout=10
            )
        except Exception as e:
            self.log_message(f"⚠️ Could not send notification: {str(e)}")

    def check_stock(self):
        """Check stock status for the product.
        
        Returns:
            tuple: (success, name, info) where:
                - success (bool): Whether the check was successful
                - name (str): Product name or None if check failed
                - info (dict): Product info or None if check failed
        """
        try:
            print(f"Checking stock for URL: {self.url}")
            from ..utils.helpers import check_stock, parse_url
            
            product_id = parse_url(self.url)
            success, name, info = check_stock(product_id)
            
            # Update status based on success and validity
            if success:
                self.last_check_status = "In Stock"
            elif info and 'error' in info:
                self.last_check_status = f"Error: {info['error']}"
            else:
                self.last_check_status = "Error: Invalid response"
            
            self.update_status({'status': self.last_check_status})
            
            # If check_stock returned error info, convert to None
            if not success and isinstance(info, dict) and 'error' in info:
                info = None
            
            return success, name, info
            
        except ValueError as e:
            # Handle invalid URL or parsing errors
            error_msg = str(e)
            self.last_check_status = f"Error: {error_msg}"
            self.update_status({'status': self.last_check_status})
            self.log_error(error_msg)
            return False, None, None
            
        except Exception as e:
            # Handle other errors
            error_msg = f"Error checking stock: {str(e)}"
            self.last_check_status = "Error"
            self.update_status({'status': self.last_check_status})
            self.log_error(error_msg)
            return False, None, None 