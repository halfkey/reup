"""Custom exceptions for the stock monitor."""

class MonitorError(Exception):
    """Base exception for monitoring errors."""
    pass

class ValidationError(MonitorError):
    """Base exception for validation errors."""
    pass

class StockCheckError(MonitorError):
    """Base exception for stock checking errors."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class ProfileError(MonitorError):
    """Base exception for profile-related errors."""
    pass

class ProfileLoadError(ProfileError):
    """Exception raised when loading a profile fails."""
    pass

class ProfileSaveError(ProfileError):
    """Exception raised when saving a profile fails."""
    pass

class APIError(Exception):
    """Exception raised for API errors."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class URLError(StockCheckError):
    """Exception raised for invalid URLs."""
    def __init__(self, url, message=None):
        self.url = url
        msg = f"Invalid URL: {url}"
        if message:
            msg += f" - {message}"
        super().__init__(msg)

class URLParseError(ValidationError):
    """Exception raised for URL parsing errors."""
    pass

class ConfigError(MonitorError):
    """Exception raised for configuration errors."""
    pass

class CacheError(MonitorError):
    """Exception raised for caching errors."""
    pass

class SecurityError(MonitorError):
    """Exception raised for security-related errors."""
    pass 