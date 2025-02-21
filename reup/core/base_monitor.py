from tkinter import ttk
import tkinter as tk
from abc import ABC, abstractmethod
from ..config.styles import STYLES
import logging
from ..utils.helpers import get_timestamp


class BaseMonitor(ABC, ttk.Frame):
    """Abstract base class for monitors."""

    def __init__(self, parent, main_app, test_mode=False):
        """Initialize the base monitor."""
        self.main_app = main_app
        self.parent = parent
        if not test_mode:
            super().__init__(parent)  # Only initialize ttk.Frame if not in test mode
        self.style = main_app.style if hasattr(main_app, "style") else None
        self.log_display = None

    @abstractmethod
    def setup_ui(self):
        """Setup the UI components."""
        pass

    @abstractmethod
    def start_monitoring(self):
        """Start monitoring process."""
        pass

    @abstractmethod
    def stop_monitoring(self):
        """Stop monitoring process."""
        pass

    def log_message(self, message):
        """Log a message to both display and parent."""
        timestamp = get_timestamp()
        log_entry = f"{timestamp} {message}\n"

        # Only try to update log_display if it exists
        if hasattr(self, "log_display") and self.log_display is not None:
            self.log_display.insert("1.0", log_entry)
            self.log_display.see("1.0")

        # Always try to log to parent
        if hasattr(self, "parent"):
            self.parent.log_message(message)

    def log_error(self, message: str):
        """Log an error message."""
        if hasattr(self.main_app, "log_message"):
            self.main_app.log_message(f"Error: {message}")
        else:
            logging.error(message)

    def update_status(self, status_info: dict):
        """Update status display."""
        if hasattr(self, "status_label") and self.status_label is not None:
            self.status_label.config(
                text=f"Status: {status_info.get('status', 'Unknown')}"
            )

    def clear_setup_page(self):
        """Clear the setup page."""
        if hasattr(self.parent, "clear_setup_page"):
            self.parent.clear_setup_page()
