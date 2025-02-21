# Reup

A desktop application for monitoring Best Buy Canada product stock with real-time notifications.

## Features
- 🔍 Real-time stock monitoring
- 🔔 Desktop notifications
- 💾 Profile management for saving product lists
- 🔒 Secure file handling and logging
- ⚡ Rate limiting to prevent API abuse
- 🖥️ Modern GUI interface

## Installation

```bash
# Clone the repository
git clone https://github.com/halfkey/reup.git
cd reup

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Run the application
python run.py
```

### Creating a Profile
1. Click "New Profile"
2. Enter profile name
3. Add product URLs
4. Click "Save Profile"

### Monitoring Products
1. Select a profile or add individual URLs
2. Set check interval (minimum 5 seconds)
3. Click "Start Monitoring"

## Development

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Format code
black .

# Run linting
flake8
```

## Requirements
- Python 3.8+
- Operating System: Windows, macOS, or Linux
- Internet connection

## Security Features
- Secure file permissions
- Rate limiting
- Input validation
- Security event logging
- HTTPS-only connections

## Contributing
Pull requests are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments
- Best Buy Canada for their product API
- Contributors and testers

## Support
For support, please open an issue on GitHub.
