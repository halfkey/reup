from reup.core.base_monitor import BaseMonitor


class TestMonitor(BaseMonitor):
    """Concrete implementation of BaseMonitor for testing."""

    def __init__(self, parent, main_app):
        super().__init__(parent, main_app)
        self.parent = parent  # Explicitly set parent

    def setup_ui(self):
        pass

    def start_monitoring(self):
        pass

    def stop_monitoring(self):
        pass
