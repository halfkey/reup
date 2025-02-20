from typing import Optional, Dict
from base_monitor import BaseMonitor
import tkinter as tk
from tkinter import ttk
from config import STYLES, DEFAULT_INTERVAL, MIN_INTERVAL
from utils import check_stock, get_timestamp
from exceptions import StockCheckError
from plyer import notification

class ProductMonitor(BaseMonitor):
    def __init__(self, parent, url: str, main_app):
        self.url = url
        self.scheduled_check = None
        self.paused = False
        super().__init__(parent, main_app)

    def setup_ui(self):
        """Initialize the UI components."""
        # Control panel
        self.control_frame = self.create_control_frame()
        
        # Activity log
        self.log_frame = self.create_log_frame()
        
        # Initialize monitoring status
        self.status = {
            'last_check': None,
            'last_status': None,
            'error_count': 0
        }

    def create_control_frame(self) -> ttk.Frame:
        """Create the control panel frame."""
        frame = ttk.LabelFrame(self, text=" Controls ", style='Custom.TLabelframe')
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        controls = ttk.Frame(frame, style='Custom.TFrame')
        controls.pack(fill=tk.X, padx=10, pady=10)
        
        # Control buttons
        self.create_control_buttons(controls)
        
        # Interval control
        self.create_interval_control(controls)
        
        return frame

    def create_control_buttons(self, parent: ttk.Frame):
        """Create control buttons."""
        self.stop_button = ttk.Button(
            parent,
            text="⏹ Stop",
            style='Custom.TButton',
            command=self.stop_monitoring
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.pause_button = ttk.Button(
            parent,
            text="⏸️ Pause",
            style='Custom.TButton',
            command=self.toggle_pause
        )
        self.pause_button.pack(side=tk.LEFT, padx=5)

    def create_interval_control(self, parent: ttk.Frame):
        """Create interval control section."""
        ttk.Label(parent, text="Check Interval (sec):", 
                 background='#f0f0f0').pack(side=tk.LEFT, padx=(20, 5))
        
        self.interval_entry = ttk.Entry(parent, width=5)
        self.interval_entry.insert(0, str(DEFAULT_INTERVAL))
        self.interval_entry.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(
            parent,
            text="Status: Starting...",
            background='#f0f0f0',
            font=('Arial', 10, 'bold')
        )
        self.status_label.pack(side=tk.RIGHT, padx=5)

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
            self.validate_interval()
            self.monitor_product()
            self.log_message(f"Started monitoring: {self.url}")
        except ValueError as e:
            self.log_message(f"⚠️ {str(e)}")
            self.use_default_interval()
            self.monitor_product()

    def validate_interval(self) -> int:
        """Validate and return the monitoring interval."""
        try:
            interval = int(self.interval_entry.get())
            if interval < MIN_INTERVAL:
                raise ValueError(f"Interval too short, minimum is {MIN_INTERVAL} seconds")
            return interval
        except ValueError:
            raise ValueError("Invalid interval value")

    def use_default_interval(self):
        """Reset to default interval."""
        self.interval_entry.delete(0, tk.END)
        self.interval_entry.insert(0, str(DEFAULT_INTERVAL))

    def monitor_product(self):
        """Perform one monitoring cycle."""
        if self.paused:
            return
            
        try:
            is_available, product_name, status_details = check_stock(
                self.url,
                {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            
            self.handle_stock_status(is_available, product_name, status_details)
            self.status['error_count'] = 0  # Reset error count on success
            
        except Exception as e:
            self.handle_monitoring_error(e)
        
        finally:
            self.schedule_next_check()

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

    def schedule_next_check(self):
        """Schedule the next monitoring check."""
        if not self.paused:
            try:
                interval = self.validate_interval() * 1000
            except ValueError:
                interval = DEFAULT_INTERVAL * 1000
            
            self.scheduled_check = self.after(interval, self.monitor_product)

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
        
        self.log_message("⏹ Stopped monitoring")
        self.cleanup()

    def cleanup(self):
        """Perform cleanup operations."""
        tab_name = f"Monitor_{self.url.split('/')[-1]}"
        self.main_app.monitor_tabs.pop(tab_name, None)
        self.main_app.notebook.forget(self)

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