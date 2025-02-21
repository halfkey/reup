# Contributing to Reup

## Development Setup
1. Fork the repository
2. Clone your fork
3. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```
4. Create a new branch for your feature:
   ```bash
   # Create branch from stable main
   git checkout -b feature-name main
   ```
5. Make your changes
6. Run tests:
   ```bash
   pytest
   ```
7. Submit a pull request

## Branch Management
- `main` - Stable production code
- `stable-backup` - Backup of last known good state
- Feature branches should be created from `main`
- Run full test suite before merging to `main`

## Code Style
- Follow PEP 8
- Use type hints
- Add docstrings for all functions/classes
- Run black before committing:
  ```bash
  black .
  ```

## Testing
- Add tests for new features
- Maintain test coverage
- Run full test suite before submitting PR

### Running Tests
```bash
# Run all tests
pytest

# Run tests with debugging output
python scripts/debug_tests.py

# Run specific test file
pytest tests/test_specific.py

# Run specific test
pytest tests/test_specific.py::test_name

# Run tests matching pattern
pytest -k "pattern"
```

### Common Test Issues
- Check test dependencies are installed
- Ensure test database is clean
- Verify mock objects are properly configured
- Check for race conditions in async tests 