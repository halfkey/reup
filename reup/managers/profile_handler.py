"""Profile management business logic."""
from typing import Dict, List, Optional
import json
import os
from pathlib import Path

class ProfileHandler:
    """Handles profile operations separate from UI."""
    
    def __init__(self, profiles_dir: str = "profiles"):
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        
    def save_profile(self, name: str, data: Dict) -> None:
        """Save profile data to file."""
        if not name:
            raise ValueError("Profile name cannot be empty")
            
        file_path = self.profiles_dir / f"{name}.json"
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
            
    def load_profile(self, name: str) -> Dict:
        """Load profile data from file."""
        if not name:
            raise ValueError("Profile name cannot be empty")
            
        file_path = self.profiles_dir / f"{name}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Profile '{name}' not found")
            
        with open(file_path, 'r') as f:
            return json.load(f)
            
    def list_profiles(self) -> List[str]:
        """Get list of available profiles."""
        profiles = []
        for file in self.profiles_dir.glob("*.json"):
            profiles.append(file.stem)
        return sorted(profiles)
        
    def delete_profile(self, name: str) -> None:
        """Delete a profile."""
        if not name:
            raise ValueError("Profile name cannot be empty")
            
        file_path = self.profiles_dir / f"{name}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Profile '{name}' not found")
            
        os.remove(file_path) 