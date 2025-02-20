from typing import Dict, List, Optional
import os
import json
from datetime import datetime
from exceptions import ProfileLoadError, ProfileSaveError
from utils import get_timestamp
import logging

class ProfileManager:
    """Handles profile management operations."""
    
    def __init__(self, profiles_dir: str = 'profiles'):
        self.profiles_dir = 'profiles'  # Always use 'profiles' as the base directory
        self.ensure_profile_directory()
        
    def ensure_profile_directory(self):
        """Ensure profiles directory exists."""
        os.makedirs(self.profiles_dir, exist_ok=True)
    
    def save_profile(self, name: str, data: Dict) -> str:
        """Save profile with timestamp."""
        try:
            # Sanitize the filename
            safe_name = "".join(c for c in name if c.isalnum() or c in ('-', '_'))
            filename = f'{safe_name}.json'  # Remove timestamp for simpler management
            
            # Build the correct path
            filepath = os.path.join(self.profiles_dir, filename)
            
            logging.debug(f"Saving profile to: {filepath}")
            
            # Add metadata
            data['metadata'] = {
                'name': name,
                'last_modified': get_timestamp(),
                'version': '1.0'
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)
            
            return filename
            
        except Exception as e:
            logging.error(f"Failed to save profile: {str(e)}")
            raise ProfileSaveError(f"Failed to save profile {name}: {str(e)}")
    
    def load_profile(self, name: str) -> Dict:
        """Load a profile by name."""
        try:
            # Sanitize the name
            safe_name = "".join(c for c in name if c.isalnum() or c in ('-', '_'))
            filename = f'{safe_name}.json'
            filepath = os.path.join(self.profiles_dir, filename)
            
            if not os.path.exists(filepath):
                raise ProfileLoadError(f"Profile not found: {name}")
            
            logging.debug(f"Loading profile from: {filepath}")
            
            with open(filepath, 'r') as f:
                data = json.load(f)
            return data
            
        except Exception as e:
            logging.error(f"Failed to load profile: {str(e)}")
            raise ProfileLoadError(f"Failed to load profile {name}: {str(e)}")
    
    def get_latest_profile(self, name: str) -> Optional[str]:
        """Get the filename of the most recent version of a profile."""
        try:
            # Ensure we're looking in the correct directory
            files = [f for f in os.listdir(self.profiles_dir) 
                    if f.startswith(name) and f.endswith('.json')]
            
            if not files:
                return None
            
            # Sort by timestamp (newest first)
            files.sort(reverse=True)
            return files[0]
            
        except Exception as e:
            logging.error(f"Error getting latest profile: {str(e)}")
            return None
    
    def list_profiles(self) -> List[str]:
        """Get list of profile names."""
        try:
            profiles = []
            for filename in os.listdir(self.profiles_dir):
                if filename.endswith('.json'):
                    # Remove .json extension
                    name = filename[:-5]
                    profiles.append(name)
            return sorted(profiles)
        except Exception as e:
            logging.error(f"Failed to list profiles: {str(e)}")
            return []
    
    def cleanup_old_profiles(self, name: str, keep: int = 5):
        """Keep only the most recent versions of a profile."""
        pattern = f'{name}_*.json'
        files = [f for f in os.listdir(self.profiles_dir) 
                if f.startswith(name) and f.endswith('.json')]
        
        # Sort by timestamp (newest first)
        files.sort(reverse=True)
        
        # Remove old versions
        for old_file in files[keep:]:
            try:
                os.remove(os.path.join(self.profiles_dir, old_file))
            except Exception:
                pass
    
    def delete_profile(self, name: str) -> bool:
        """Delete a profile."""
        try:
            # Sanitize the name
            safe_name = "".join(c for c in name if c.isalnum() or c in ('-', '_'))
            filename = f'{safe_name}.json'
            filepath = os.path.join(self.profiles_dir, filename)
            
            if os.path.exists(filepath):
                os.remove(filepath)
                logging.info(f"Deleted profile: {name}")
                return True
            return False
            
        except Exception as e:
            logging.error(f"Failed to delete profile: {str(e)}")
            return False
    
    def export_profile(self, name: str, export_dir: str) -> bool:
        """Export a profile to a different location."""
        try:
            data = self.load_profile(name)
            export_path = os.path.join(export_dir, f'{name}_export.json')
            
            with open(export_path, 'w') as f:
                json.dump(data, f, indent=4)
            
            return True
        except Exception:
            return False
    
    def import_profile(self, filepath: str) -> Optional[str]:
        """Import a profile from a file."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Extract name from filename or generate new one
            name = os.path.basename(filepath).split('_')[0]
            
            # Save as new profile
            return self.save_profile(name, data)
        except Exception:
            return None 