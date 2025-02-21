# Contributing to Reup

## Development Setup
1. Fork the repository
2. Clone your fork
3. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```
4. Create a new branch for your feature
5. Make your changes
6. Run tests:
   ```bash
   pytest
   ```
7. Submit a pull request

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