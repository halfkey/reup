from typing import Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from ..config import Config
from ..utils.exceptions import APIError
import time
from functools import lru_cache

class RequestManager:
    """Manages API requests with rate limiting and caching."""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = self._create_session()
        self.last_request_time = 0
        
    def _create_session(self) -> requests.Session:
        """Create session with retry logic."""
        session = requests.Session()
        retry = Retry(
            total=self.config.get("api.max_retries", 3),
            backoff_factor=self.config.get("api.backoff_factor", 1.0),
            status_forcelist=[408, 429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session
    
    def _respect_rate_limit(self) -> None:
        """Ensure minimum time between requests."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        rate_limit = self.config.get("rate_limit", 1.0)
        
        if elapsed < rate_limit:
            time.sleep(rate_limit - elapsed)
        self.last_request_time = time.time()
    
    @lru_cache(maxsize=1000)
    def get(self, url: str, cache_ttl: int = 300) -> Dict[str, Any]:
        """Make GET request with caching."""
        self._respect_rate_limit()
        
        try:
            response = self.session.get(
                url,
                timeout=self.config.get("api.timeout", 20),
                verify=self.config.get("security.enable_ssl_verify", True)
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise APIError(getattr(e.response, 'status_code', 500), str(e)) 