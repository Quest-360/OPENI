"""
Rate Limiter Module
-----------------
Implements rate limiting, request throttling, and proxy rotation
to avoid HTTP 429 errors and website blocking.
"""
import time
import random
import logging
from typing import List, Dict, Any, Optional, Union
from collections import deque
import threading

# Set up logging
logger = logging.getLogger("ZeptoScraper.RateLimiter")

class RateLimiter:
    """
    Manages request rate limiting and prevention of 429 errors.
    Implements various strategies like delays, user-agent rotation, and exponential backoff.
    """
    
    def __init__(self):
        """Initialize the rate limiter with default settings"""
        # Configuration
        self.config = {
            "min_delay": 1.0,       # Minimum delay between requests in seconds
            "max_delay": 3.0,       # Maximum delay between requests in seconds
            "rpm_limit": 20,        # Requests per minute limit
            "browser": "chrome",    # Default browser type
            "headless": False,      # Default headless mode
            "use_proxies": False,   # Whether to use proxies
            "initial_backoff": 5.0, # Initial backoff time in seconds
            "max_backoff": 300.0,   # Maximum backoff time in seconds
            "backoff_factor": 2.0,  # Exponential backoff factor
        }
        
        # State
        self.last_request_time = 0.0
        self.request_times = deque(maxlen=60)  # Rolling window of request times
        self.error_count = 0
        self.current_backoff = self.config["initial_backoff"]
        
        # Resources
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/91.0.4472.80 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/91.0.4472.80 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0"
        ]
        self.current_user_agent_idx = 0
        
        # Optional proxy support
        self.proxies: List[str] = []
        self.current_proxy_idx = 0
        
        # Thread safety
        self.lock = threading.RLock()
    
    def configure(self, **kwargs):
        """
        Configure the rate limiter
        
        Args:
            **kwargs: Configuration parameters to update
        """
        with self.lock:
            for key, value in kwargs.items():
                if key in self.config:
                    self.config[key] = value
                    logger.debug(f"Rate limiter config: {key} = {value}")
            
            # Reset state if configuration changes
            self.current_backoff = self.config["initial_backoff"]
            self.error_count = 0
    
    def wait_if_needed(self):
        """
        Wait if rate limits are being approached
        
        This method checks if recent request rates are approaching limits and
        adds appropriate delays to stay under the limits.
        """
        with self.lock:
            current_time = time.time()
            
            # Calculate time since last request
            time_since_last = current_time - self.last_request_time
            
            # Check RPM limit
            minute_ago = current_time - 60
            recent_requests = sum(1 for t in self.request_times if t > minute_ago)
            
            # Determine if we need to wait
            if recent_requests >= self.config["rpm_limit"]:
                # Calculate how long to wait for RPM to drop
                oldest_in_window = min(self.request_times) if self.request_times else minute_ago
                wait_time = 61 - (current_time - oldest_in_window)
                if wait_time > 0:
                    logger.info(f"Rate limit approaching - waiting {wait_time:.2f}s to stay under RPM limit")
                    time.sleep(wait_time)
            
            # Always ensure minimum delay between requests
            if time_since_last < self.config["min_delay"]:
                wait_time = self.config["min_delay"] - time_since_last
                logger.debug(f"Ensuring minimum delay - waiting {wait_time:.2f}s")
                time.sleep(wait_time)
            
            # Occasionally add a longer random delay to appear more human-like
            if random.random() < 0.2:  # 20% chance
                random_delay = random.uniform(
                    self.config["min_delay"],
                    self.config["max_delay"]
                )
                logger.debug(f"Adding random delay of {random_delay:.2f}s")
                time.sleep(random_delay)
            
            # After possibly waiting, update last request time
            self.last_request_time = time.time()
    
    def record_request(self):
        """Record that a request was made"""
        with self.lock:
            # Add current time to request times
            self.request_times.append(time.time())
            
            # Log request
            logger.debug(f"Request recorded - RPM: {len(self.request_times)}/{self.config['rpm_limit']}")
    
    def handle_rate_limit_error(self):
        """
        Handle a rate limit error (HTTP 429)
        
        This implements an exponential backoff strategy
        """
        with self.lock:
            self.error_count += 1
            
            # Calculate backoff time with some randomness
            backoff = min(
                self.current_backoff * (1.0 + random.uniform(-0.2, 0.2)),
                self.config["max_backoff"]
            )
            
            # Increase backoff for future errors
            self.current_backoff = min(
                self.current_backoff * self.config["backoff_factor"],
                self.config["max_backoff"]
            )
            
            # Rotate user agent and proxy (if used)
            self._rotate_user_agent()
            if self.config["use_proxies"]:
                self._rotate_proxy()
            
            logger.warning(f"Rate limit error detected - backing off for {backoff:.2f}s (error #{self.error_count})")
            
            return backoff
    
    def get_backoff_time(self) -> float:
        """
        Get the current backoff time in seconds
        
        Returns:
            float: Current backoff time
        """
        with self.lock:
            return self.current_backoff
    
    def reset_error_count(self):
        """Reset the error count after successful requests"""
        with self.lock:
            if self.error_count > 0:
                logger.info(f"Resetting error count from {self.error_count} to 0")
                self.error_count = 0
                self.current_backoff = self.config["initial_backoff"]
    
    def get_proxy(self) -> Optional[str]:
        """
        Get the current proxy to use
        
        Returns:
            Optional[str]: Proxy URL or None if not using proxies
        """
        with self.lock:
            if not self.config["use_proxies"] or not self.proxies:
                return None
            
            return self.proxies[self.current_proxy_idx]
    
    def _rotate_proxy(self):
        """Rotate to the next proxy in the list"""
        with self.lock:
            if not self.proxies:
                return
            
            self.current_proxy_idx = (self.current_proxy_idx + 1) % len(self.proxies)
            logger.debug(f"Rotated to proxy #{self.current_proxy_idx}")
    
    def get_user_agent(self) -> str:
        """
        Get a user agent string
        
        Returns:
            str: User agent string
        """
        with self.lock:
            return self.user_agents[self.current_user_agent_idx]
    
    def _rotate_user_agent(self):
        """Rotate to the next user agent in the list"""
        with self.lock:
            self.current_user_agent_idx = (self.current_user_agent_idx + 1) % len(self.user_agents)
            logger.debug(f"Rotated to user agent #{self.current_user_agent_idx}")
    
    def get_request_stats(self) -> Dict[str, Any]:
        """
        Get statistics about recent requests
        
        Returns:
            Dict with request statistics
        """
        with self.lock:
            current_time = time.time()
            minute_ago = current_time - 60
            recent_requests = sum(1 for t in self.request_times if t > minute_ago)
            
            return {
                "requests_last_minute": recent_requests,
                "rpm_limit": self.config["rpm_limit"],
                "error_count": self.error_count,
                "current_backoff": self.current_backoff,
                "last_request_time": self.last_request_time,
                "time_since_last": current_time - self.last_request_time if self.last_request_time else None
            }