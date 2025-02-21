# User configurable settings
class Settings:
    # Monitoring settings
    CHECK_INTERVAL = 15  # seconds
    MIN_INTERVAL = 5    # minimum seconds
    
    # Notification settings
    ENABLE_NOTIFICATIONS = True
    NOTIFICATION_TIMEOUT = 10  # seconds
    
    # UI settings
    WINDOW_SIZE = (1200, 800)
    MAX_LOG_LINES = 1000
    
    # File paths
    LOG_FILENAME = "reup.log" 