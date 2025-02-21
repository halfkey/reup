# Create a centralized config manager
from pathlib import Path
import json
import os
from typing import Any, Dict, Optional


class Config:
    """Centralized configuration management"""

    DEFAULT_CONFIG = {
        "check_interval": 15,
        "min_interval": 5,
        "max_products": 100,
        "notification_timeout": 10,
        "enable_notifications": True,
        "log_level": "INFO",
        "rate_limit": 1.0,
        "api": {"max_retries": 3, "timeout": 20, "backoff_factor": 1.0},
        "security": {
            "file_permissions": "0600",
            "dir_permissions": "0700",
            "enable_ssl_verify": True,
        },
        "cache": {
            "enable": True,
            "max_age": 300,  # 5 minutes
            "max_size": 1000,  # entries
        },
    }

    def __init__(self):
        self.config_dir = Path.home() / ".reup"
        self.config_file = self.config_dir / "config.json"
        self.config: Dict[str, Any] = {}
        self._ensure_config_dir()
        self.load_config()

    def _ensure_config_dir(self) -> None:
        """Create and secure config directory."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(self.config_dir, 0o700)

    def load_config(self) -> None:
        """Load or create configuration."""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    user_config = json.load(f)
                # Deep merge with defaults
                self.config = self._deep_merge(self.DEFAULT_CONFIG.copy(), user_config)
            else:
                self.config = self.DEFAULT_CONFIG.copy()
                self.save_config()
        except Exception as e:
            raise ConfigError(f"Failed to load config: {str(e)}")

    def _deep_merge(self, base: Dict, update: Dict) -> Dict:
        """Deep merge two dictionaries."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                base[key] = self._deep_merge(base[key], value)
            else:
                base[key] = value
        return base

    def save_config(self):
        """Save the current configuration to file."""
        with open(self.config_file, "w") as f:
            json.dump(self.config)

    def get_config(self):
        """Return the current configuration."""
        return self.config

    def update_config(self, new_config: Dict):
        """Update the current configuration with new values."""
        self.config = self._deep_merge(self.config, new_config)
        self.save_config()

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get a value from the configuration."""
        return self.config.get(key, default)

    def set_value(self, key: str, value: Any):
        """Set a value in the configuration."""
        self.config[key] = value
        self.save_config()

    def remove_value(self, key: str):
        """Remove a value from the configuration."""
        self.config.pop(key, None)
        self.save_config()

    def get_api_config(self):
        """Return the API configuration."""
        return self.config.get("api", {})

    def get_security_config(self):
        """Return the security configuration."""
        return self.config.get("security", {})

    def get_cache_config(self):
        """Return the cache configuration."""
        return self.config.get("cache", {})

    def get_check_interval(self):
        """Return the check interval."""
        return self.config.get("check_interval")

    def get_min_interval(self):
        """Return the minimum interval."""
        return self.config.get("min_interval")

    def get_max_products(self):
        """Return the maximum number of products."""
        return self.config.get("max_products")

    def get_notification_timeout(self):
        """Return the notification timeout."""
        return self.config.get("notification_timeout")

    def get_enable_notifications(self):
        """Return whether notifications are enabled."""
        return self.config.get("enable_notifications")

    def get_log_level(self):
        """Return the log level."""
        return self.config.get("log_level")

    def get_rate_limit(self):
        """Return the rate limit."""
        return self.config.get("rate_limit")

    def get_api_max_retries(self):
        """Return the maximum number of API retries."""
        return self.get_api_config().get("max_retries")

    def get_api_timeout(self):
        """Return the API timeout."""
        return self.get_api_config().get("timeout")

    def get_api_backoff_factor(self):
        """Return the API backoff factor."""
        return self.get_api_config().get("backoff_factor")

    def get_security_file_permissions(self):
        """Return the file permissions for security."""
        return self.get_security_config().get("file_permissions")

    def get_security_dir_permissions(self):
        """Return the directory permissions for security."""
        return self.get_security_config().get("dir_permissions")

    def get_security_enable_ssl_verify(self):
        """Return whether SSL verification is enabled for security."""
        return self.get_security_config().get("enable_ssl_verify")

    def get_cache_enable(self):
        """Return whether caching is enabled."""
        return self.get_cache_config().get("enable")

    def get_cache_max_age(self):
        """Return the maximum age for cache entries."""
        return self.get_cache_config().get("max_age")

    def get_cache_max_size(self):
        """Return the maximum size for cache entries."""
        return self.get_cache_config().get("max_size")

    def update_api_config(self, new_config: Dict):
        """Update the API configuration with new values."""
        self.update_config({"api": new_config})

    def update_security_config(self, new_config: Dict):
        """Update the security configuration with new values."""
        self.update_config({"security": new_config})

    def update_cache_config(self, new_config: Dict):
        """Update the cache configuration with new values."""
        self.update_config({"cache": new_config})

    def update_check_interval(self, new_interval: int):
        """Update the check interval."""
        self.update_config({"check_interval": new_interval})

    def update_min_interval(self, new_interval: int):
        """Update the minimum interval."""
        self.update_config({"min_interval": new_interval})

    def update_max_products(self, new_max: int):
        """Update the maximum number of products."""
        self.update_config({"max_products": new_max})

    def update_notification_timeout(self, new_timeout: int):
        """Update the notification timeout."""
        self.update_config({"notification_timeout": new_timeout})

    def update_enable_notifications(self, new_enable: bool):
        """Update whether notifications are enabled."""
        self.update_config({"enable_notifications": new_enable})

    def update_log_level(self, new_level: str):
        """Update the log level."""
        self.update_config({"log_level": new_level})

    def update_rate_limit(self, new_limit: float):
        """Update the rate limit."""
        self.update_config({"rate_limit": new_limit})

    def update_api_max_retries(self, new_retries: int):
        """Update the maximum number of API retries."""
        self.update_api_config({"max_retries": new_retries})

    def update_api_timeout(self, new_timeout: int):
        """Update the API timeout."""
        self.update_api_config({"timeout": new_timeout})

    def update_api_backoff_factor(self, new_factor: float):
        """Update the API backoff factor."""
        self.update_api_config({"backoff_factor": new_factor})

    def update_security_file_permissions(self, new_permissions: str):
        """Update the file permissions for security."""
        self.update_security_config({"file_permissions": new_permissions})

    def update_security_dir_permissions(self, new_permissions: str):
        """Update the directory permissions for security."""
        self.update_security_config({"dir_permissions": new_permissions})

    def update_security_enable_ssl_verify(self, new_enable: bool):
        """Update whether SSL verification is enabled for security."""
        self.update_security_config({"enable_ssl_verify": new_enable})

    def update_cache_enable(self, new_enable: bool):
        """Update whether caching is enabled."""
        self.update_cache_config({"enable": new_enable})

    def update_cache_max_age(self, new_age: int):
        """Update the maximum age for cache entries."""
        self.update_cache_config({"max_age": new_age})

    def update_cache_max_size(self, new_size: int):
        """Update the maximum size for cache entries."""
        self.update_cache_config({"max_size": new_size})

    def update_config(self, new_config: Dict):
        """Update the current configuration with new values."""
        self.config = self._deep_merge(self.config, new_config)
        self.save_config()

    def create_default_config(self):
        """Create a default configuration."""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save_config()

    def create_config(self, config: Dict):
        """Create a new configuration."""
        self.config = config
        self.save_config()

    def delete_config(self):
        """Delete the current configuration."""
        self.config = {}
        self.save_config()

    def delete_config_file(self):
        """Delete the configuration file."""
        self.config_file.unlink(missing_ok=True)

    def delete_config_dir(self):
        """Delete the configuration directory."""
        self.config_dir.rmdir()

    def delete_all_configs(self):
        """Delete all configurations."""
        self.delete_config()
        self.delete_config_file()
        self.delete_config_dir()

    def load_config(self):
        """Load or create default configuration"""
        if not self.config_file.exists():
            self.create_default_config()
        # ... config loading logic
