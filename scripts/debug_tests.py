#!/usr/bin/env python3
import pytest
import sys
from pathlib import Path

def run_debug_tests():
    """Run tests with debugging options."""
    project_root = Path(__file__).parent.parent
    
    # Add debugging flags
    args = [
        str(project_root / "tests"),
        "-v",                     # Verbose output
        "--full-trace",          # Full traceback
        "--showlocals",          # Show local variables in tracebacks
        "--durations=10",        # Show 10 slowest tests
        "--tb=long",            # Detailed traceback
        "-x",                    # Exit on first failure
        "--pdb",                # Drop into debugger on failures
        "--cov=reup",           # Coverage for reup package
        "--cov-report=term-missing",  # Show missing coverage
    ]
    
    # Add any command line arguments
    args.extend(sys.argv[1:])
    
    return pytest.main(args)

if __name__ == "__main__":
    sys.exit(run_debug_tests()) 