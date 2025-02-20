class MonitorError(Exception):
    """Base exception for monitoring errors."""
    pass

class StockCheckError(MonitorError):
    """Raised when there's an error checking stock."""
    pass

class ProfileError(MonitorError):
    """Base exception for profile-related errors."""
    pass

class ProfileLoadError(ProfileError):
    """Raised when there's an error loading a profile."""
    pass

class ProfileSaveError(ProfileError):
    """Raised when there's an error saving a profile."""
    pass

class APIError(MonitorError):
    """Raised when there's an API-related error."""
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error ({status_code}): {message}") 