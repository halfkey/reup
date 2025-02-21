import os
from pathlib import Path
import shutil


def cleanup_project():
    """Clean up unnecessary files and directories."""
    project_root = Path(__file__).parent.parent

    # Files to remove (old/duplicate files)
    files_to_remove = [
        "monitor_tab.py",  # Should be in stock_monitor/gui/
        "profile_manager.py",  # Duplicate, should be in stock_monitor/managers/
        "run.py",  # Duplicate, should be in stock_monitor/
        "config.py",  # Old file, now in stock_monitor/config/
        "src/gui/__init__ copy.py",
        "src/gui/__init__.py",
    ]

    # Directories to remove
    dirs_to_remove = [
        "src",  # Everything moved to stock_monitor/
        "__pycache__",
        ".pytest_cache",
        "stock_monitor.egg-info",  # Can be regenerated
    ]

    # Clean up specific files
    for file_path in files_to_remove:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"Removing file: {file_path}")
            full_path.unlink()

    # Clean up directories
    for dir_path in dirs_to_remove:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"Removing directory: {dir_path}")
            shutil.rmtree(full_path)

    # Clean up all __pycache__ directories recursively
    for pycache_dir in project_root.rglob("__pycache__"):
        print(f"Removing Python cache: {pycache_dir}")
        shutil.rmtree(pycache_dir)

    # Clean up all .pyc files recursively
    for pyc_file in project_root.rglob("*.pyc"):
        print(f"Removing compiled Python file: {pyc_file}")
        pyc_file.unlink()


if __name__ == "__main__":
    cleanup_project()
