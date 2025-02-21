from typing import Any, Optional, Union, Dict
from urllib.parse import urlparse
import re
from ..utils.exceptions import ValidationError

class Validator:
    """Input validation utilities."""
    
    @staticmethod
    def validate_url(url: str) -> str:
        """Validate URL format and security."""
        if not url:
            raise ValidationError("URL cannot be empty")
            
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                raise ValidationError("Invalid URL format")
            if result.scheme not in ('http', 'https'):
                raise ValidationError("URL must use HTTP(S) protocol")
            return url
        except Exception as e:
            raise ValidationError(f"URL validation failed: {str(e)}")
    
    @staticmethod
    def validate_profile_name(name: str, max_length: int = 50) -> str:
        """Validate profile name."""
        if not name or not isinstance(name, str):
            raise ValidationError("Profile name must be a non-empty string")
            
        if len(name) > max_length:
            raise ValidationError(f"Profile name must be {max_length} characters or less")
            
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*$', name):
            raise ValidationError("Profile name must contain only letters, numbers, underscores, and hyphens")
            
        return name 