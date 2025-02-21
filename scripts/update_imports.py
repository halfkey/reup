#!/usr/bin/env python3
import os
from pathlib import Path


def update_imports():
    """Update imports to use relative paths where appropriate."""
    project_root = Path(__file__).parent.parent

    # Process test files
    tests_dir = project_root / "tests"
    for py_file in tests_dir.rglob("*.py"):
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Replace imports and other references
            updated = content.replace("stock_monitor.", "reup.")
            updated = updated.replace("Stock Monitor", "Reup")  # Update window titles
            updated = updated.replace(
                "stock monitor", "reup"
            )  # Update lowercase references

            if updated != content:
                print(f"Updating imports in {py_file}")
                with open(py_file, "w", encoding="utf-8", newline="") as f:
                    f.write(updated)

        except Exception as e:
            print(f"Error processing {py_file}: {str(e)}")

    # Process main package files
    reup_dir = project_root / "reup"
    for py_file in reup_dir.rglob("*.py"):
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Replace absolute imports with relative ones and update references
            if "from reup." in content or "stock_monitor" in content:
                rel_path = py_file.relative_to(reup_dir)
                dots = ".." * (len(rel_path.parts) - 1)
                updated = content.replace("from reup.", f"from {dots}.")
                updated = updated.replace("stock_monitor", "reup")
                updated = updated.replace("Stock Monitor", "Reup")

                if updated != content:
                    print(f"Converting to relative imports in {py_file}")
                    with open(py_file, "w", encoding="utf-8", newline="") as f:
                        f.write(updated)

        except Exception as e:
            print(f"Error processing {py_file}: {str(e)}")


if __name__ == "__main__":
    update_imports()
