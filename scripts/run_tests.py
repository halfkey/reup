import pytest
import sys
from pathlib import Path


def run_tests():
    """Run all tests with coverage report."""
    project_root = Path(__file__).parent.parent

    # Add arguments for coverage and verbose output
    args = [
        str(project_root / "tests"),
        "-v",
        "--cov=stock_monitor",
        "--cov-report=term-missing",
    ]

    # Run tests
    return pytest.main(args)


if __name__ == "__main__":
    sys.exit(run_tests())
