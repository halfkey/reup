import sys
from pathlib import Path
import tkinter as tk
from importlib import reload
from reup.gui.main_window import StockMonitorGUI

def reload_modules():
    """Reload all project modules."""
    from reup import gui, core, managers, utils, config
    modules = [gui, core, managers, utils, config]
    for module in modules:
        reload(module)

def run_with_reload():
    """Run the application with module reloading."""
    reload_modules()
    root = tk.Tk()
    app = StockMonitorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    # Add project root to Python path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    run_with_reload() 