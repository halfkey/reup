import os
from pathlib import Path
from typing import Union
import stat
from ..config import Config
from ..utils.logger import log_security_event

class SecurityManager:
    """Manages security-related operations."""
    
    def __init__(self, config: Config):
        self.config = config
    
    def secure_file(self, path: Union[str, Path]) -> None:
        """Apply secure permissions to a file."""
        path = Path(path)
        if not path.exists():
            return
            
        try:
            # Get permissions from config
            perms = int(self.config.get_security_file_permissions(), 8)
            os.chmod(path, perms)
            log_security_event(
                "FILE_SECURE",
                f"Applied secure permissions to {path}"
            )
        except Exception as e:
            log_security_event(
                "FILE_SECURE_ERROR",
                f"Failed to secure {path}: {str(e)}",
                "ERROR"
            )
    
    def secure_directory(self, path: Union[str, Path]) -> None:
        """Apply secure permissions to a directory."""
        path = Path(path)
        if not path.exists():
            return
            
        try:
            # Get permissions from config
            perms = int(self.config.get_security_dir_permissions(), 8)
            os.chmod(path, perms)
            log_security_event(
                "DIR_SECURE",
                f"Applied secure permissions to {path}"
            )
        except Exception as e:
            log_security_event(
                "DIR_SECURE_ERROR",
                f"Failed to secure {path}: {str(e)}",
                "ERROR"
            )
    
    def validate_file_permissions(self, path: Union[str, Path]) -> bool:
        """Check if file has secure permissions."""
        path = Path(path)
        if not path.exists():
            return False
            
        try:
            st = os.stat(path)
            return not (st.st_mode & stat.S_IRWXG or st.st_mode & stat.S_IRWXO)
        except Exception as e:
            log_security_event(
                "PERM_CHECK_ERROR",
                f"Failed to check permissions for {path}: {str(e)}",
                "ERROR"
            )
            return False 