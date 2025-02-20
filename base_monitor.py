from tkinter import ttk
import tkinter as tk
from abc import ABC, abstractmethod
from config import STYLES

class BaseMonitor(ttk.Frame, ABC):
    def __init__(self, parent, main_app):
        super().__init__(parent)
        self.main_app = main_app
        self.style = main_app.style
        
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
        
    def log_message(self, message: str):
        """Log a message with timestamp."""
        from utils import get_timestamp
        self.log_display.insert(tk.END, f"[{get_timestamp()}] {message}\n")
        self.log_display.see(tk.END) 