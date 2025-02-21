import os
from pathlib import Path
import json
import logging
from ..utils.exceptions import ProfileLoadError, ProfileSaveError, ValidationError
from ..utils.helpers import get_timestamp
import re
from ..utils.logger import log_security_event
from typing import Dict

class ProfileManager:
    MAX_PROFILE_NAME_LENGTH = 50
    MAX_PRODUCTS_PER_PROFILE = 100
    VALID_PROFILE_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*$')
    
    def __init__(self):
        # Get the project root directory
        self.root_dir = Path(__file__).parent.parent.parent
        self.profiles_dir = self.root_dir / 'data' / 'profiles'
        self._ensure_secure_directory()
    
    def _ensure_secure_directory(self):
        """Create profiles directory with secure permissions."""
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        # Set directory permissions to 700 (rwx------)
        os.chmod(self.profiles_dir, 0o700)
    
    def _validate_profile_name(self, name: str) -> str:
        """Validate and sanitize profile name."""
        if not name or not isinstance(name, str):
            raise ValidationError("Profile name must be a non-empty string")
            
        if len(name) > self.MAX_PROFILE_NAME_LENGTH:
            raise ValidationError(f"Profile name must be {self.MAX_PROFILE_NAME_LENGTH} characters or less")
            
        if not self.VALID_PROFILE_NAME_PATTERN.match(name):
            raise ValidationError("Profile name must contain only letters, numbers, underscores, and hyphens")
            
        return name

    def _validate_profile_data(self, data: Dict) -> None:
        """Validate profile data structure."""
        if not isinstance(data, dict):
            raise ValidationError("Profile data must be a dictionary")
        
        if 'products' not in data:
            raise ValidationError("Profile must contain products")
        
        if not isinstance(data['products'], list):
            raise ValidationError("Products must be a list")
        
        for product in data['products']:
            if not isinstance(product, dict):
                raise ValidationError("Each product must be a dictionary")
            if 'url' not in product:
                raise ValidationError("Each product must have a URL")
            if not isinstance(product['url'], str):
                raise ValidationError("Product URLs must be strings")

    def list_profiles(self) -> list:
        """Get list of profile names."""
        try:
            profiles = []
            if self.profiles_dir.exists():
                for file in self.profiles_dir.glob('*.json'):
                    # Remove .json extension
                    profiles.append(file.stem)
            return sorted(profiles)
        except Exception as e:
            logging.error(f"Failed to list profiles: {str(e)}")
            return []
    
    def save_profile(self, name: str, data: dict) -> bool:
        """Save profile data to file with validation."""
        try:
            # Validate inputs
            name = self._validate_profile_name(name)
            self._validate_profile_data(data)
            
            log_security_event("PROFILE_SAVE", f"Attempting to save profile: {name}")
            
            # Create secure file path
            filepath = self.profiles_dir / f"{name}.json"
            
            # Add metadata
            safe_data = {
                'products': data.get('products', []),
                'metadata': {
                    'name': name,
                    'last_modified': get_timestamp(),
                    'version': '1.0'
                }
            }
            
            # Write file with secure permissions
            with open(filepath, 'w') as f:
                json.dump(safe_data, f, indent=4)
            os.chmod(filepath, 0o600)  # Set file permissions to 600 (rw-------)
            
            log_security_event("PROFILE_SAVE", f"Successfully saved profile: {name}")
            return True
            
        except ValidationError as e:
            log_security_event("PROFILE_VALIDATION", f"Failed to validate profile {name}: {str(e)}", "WARNING")
            raise
        except Exception as e:
            log_security_event("PROFILE_ERROR", f"Failed to save profile {name}: {str(e)}", "ERROR")
            raise ProfileSaveError("Failed to save profile")
    
    def load_profile(self, name: str) -> dict:
        """Load profile data from file."""
        try:
            filepath = self.profiles_dir / f"{name}.json"
            if not filepath.exists():
                raise ProfileLoadError(f"Profile not found: {name}")
            
            with open(filepath, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logging.error(f"Failed to load profile: {str(e)}")
            raise ProfileLoadError(f"Failed to load profile {name}: {str(e)}")
    
    def delete_profile(self, name: str) -> bool:
        """Delete a profile."""
        try:
            log_security_event("PROFILE_DELETE", f"Attempting to delete profile: {name}")
            
            filepath = self.profiles_dir / f"{name}.json"
            if filepath.exists():
                filepath.unlink()
                log_security_event("PROFILE_DELETE", f"Successfully deleted profile: {name}")
                return True
            
            log_security_event("PROFILE_DELETE", f"Profile not found: {name}", "WARNING")
            return False
            
        except Exception as e:
            log_security_event("PROFILE_ERROR", f"Failed to delete profile {name}: {str(e)}", "ERROR")
            return False 