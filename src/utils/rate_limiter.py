import time
import random
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(
        self,
        min_delay: float = 1.0,
        max_delay: float = 3.0,
        max_requests_per_minute: int = 30,
        burst_size: int = 5
    ):
        """
        Initialize the rate limiter.
        
        Args:
            min_delay: Minimum delay between requests in seconds
            max_delay: Maximum delay between requests in seconds
            max_requests_per_minute: Maximum number of requests allowed per minute
            burst_size: Number of requests allowed in burst mode
        """
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.max_requests_per_minute = max_requests_per_minute
        self.burst_size = burst_size
        
        self.request_timestamps = []
        self.last_request_time = None
        self.consecutive_failures = 0
        self.burst_mode = False
        
    def _clean_old_timestamps(self):
        """Remove timestamps older than 1 minute."""
        one_minute_ago = datetime.now() - timedelta(minutes=1)
        self.request_timestamps = [ts for ts in self.request_timestamps if ts > one_minute_ago]
        
    def _calculate_delay(self) -> float:
        """Calculate the delay needed before the next request."""
        self._clean_old_timestamps()
        
        # If we're in burst mode and have consecutive failures, increase delay
        if self.burst_mode and self.consecutive_failures > 0:
            return self.max_delay * (1.5 ** self.consecutive_failures)
            
        # If we've hit the rate limit, wait until we can make another request
        if len(self.request_timestamps) >= self.max_requests_per_minute:
            oldest_timestamp = min(self.request_timestamps)
            wait_time = 60 - (datetime.now() - oldest_timestamp).total_seconds()
            if wait_time > 0:
                return wait_time
                
        # Normal random delay
        return random.uniform(self.min_delay, self.max_delay)
        
    def wait(self):
        """Wait for the appropriate amount of time before making the next request."""
        if self.last_request_time:
            delay = self._calculate_delay()
            logger.debug(f"Rate limiter: waiting {delay:.2f} seconds")
            time.sleep(delay)
            
        self.last_request_time = datetime.now()
        self.request_timestamps.append(self.last_request_time)
        
    def record_success(self):
        """Record a successful request."""
        self.consecutive_failures = 0
        self.burst_mode = False
        
    def record_failure(self):
        """Record a failed request and adjust rate limiting accordingly."""
        self.consecutive_failures += 1
        
        # If we have multiple consecutive failures, enter burst mode
        if self.consecutive_failures >= 3:
            self.burst_mode = True
            logger.warning(f"Entering burst mode due to {self.consecutive_failures} consecutive failures")
            
    def reset(self):
        """Reset the rate limiter state."""
        self.consecutive_failures = 0
        self.burst_mode = False
        self.request_timestamps = []
        self.last_request_time = None 