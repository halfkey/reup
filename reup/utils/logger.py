import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os
import logging.config
import yaml


def setup_security_logging():
    """Setup security-specific logging."""
    log_dir = Path(__file__).parent.parent.parent / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Secure the log directory
    os.chmod(log_dir, 0o700)

    # Create security logger
    security_logger = logging.getLogger("security")
    security_logger.setLevel(logging.INFO)

    # Create rotating file handler for security logs
    security_log = log_dir / "security.log"
    handler = RotatingFileHandler(
        security_log, maxBytes=1024 * 1024, backupCount=5  # 1MB
    )

    # Set secure permissions for log file
    os.chmod(security_log, 0o600)

    # Add formatter
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    security_logger.addHandler(handler)
    return security_logger


# Create security logger instance
security_logger = setup_security_logging()


def log_security_event(event_type: str, details: str, level: str = "INFO"):
    """Log security-related events."""
    log_levels = {
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    message = f"{event_type}: {details}"
    security_logger.log(log_levels.get(level, logging.INFO), message)


def setup_logging():
    """Setup application logging from config file"""
    config_path = Path(__file__).parent.parent / "config" / "logging.yaml"

    if config_path.exists():
        with open(config_path) as f:
            config = yaml.safe_load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=logging.INFO)
