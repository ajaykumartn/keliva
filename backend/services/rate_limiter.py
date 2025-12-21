"""
Rate Limiter Service
Tracks and enforces API rate limits for Groq models.
- Groq 70B: 1,000 requests/day (Grammar Guardian)
- Groq 8B: 14,000 requests/day (Polyglot Engine, Vani Persona, Knowledge Vault)
"""
from typing import Optional, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json
import os


class GroqModel(str, Enum):
    """Groq model types with different rate limits"""
    LLAMA_70B = "llama-3.3-70b-versatile"  # 1,000 requests/day
    LLAMA_8B = "llama-3.3-8b-instant"      # 14,000 requests/day


@dataclass
class RateLimitInfo:
    """Information about current rate limit status"""
    model: GroqModel
    current_count: int
    limit: int
    reset_time: datetime
    remaining: int
    
    @property
    def is_exceeded(self) -> bool:
        """Check if rate limit is exceeded"""
        return self.current_count >= self.limit
    
    @property
    def percentage_used(self) -> float:
        """Calculate percentage of limit used"""
        return (self.current_count / self.limit) * 100 if self.limit > 0 else 0


class RateLimitExceededError(Exception):
    """Raised when API rate limit is exceeded"""
    def __init__(self, model: GroqModel, limit: int, reset_time: datetime):
        self.model = model
        self.limit = limit
        self.reset_time = reset_time
        super().__init__(
            f"Rate limit exceeded for {model.value}. "
            f"Limit: {limit} requests/day. "
            f"Resets at: {reset_time.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )


class RateLimiter:
    """
    Rate limiter for Groq API calls.
    Tracks usage per model and enforces daily limits.
    """
    
    # Rate limits per model (requests per day)
    RATE_LIMITS = {
        GroqModel.LLAMA_70B: 1000,   # Grammar Guardian
        GroqModel.LLAMA_8B: 14000     # Polyglot, Vani, Knowledge Vault
    }
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize rate limiter.
        
        Args:
            storage_path: Path to store rate limit data (defaults to ./rate_limits.json)
        """
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(__file__),
            "..",
            "rate_limits.json"
        )
        
        # In-memory counters
        self._counters: Dict[str, int] = {}
        self._reset_times: Dict[str, datetime] = {}
        
        # Load existing data
        self._load_state()
    
    def _get_counter_key(self, model: GroqModel) -> str:
        """Generate storage key for model counter"""
        return f"{model.value}"
    
    def _get_reset_time_key(self, model: GroqModel) -> str:
        """Generate storage key for reset time"""
        return f"{model.value}_reset"
    
    def _load_state(self) -> None:
        """Load rate limit state from storage"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    
                    # Load counters
                    self._counters = data.get("counters", {})
                    
                    # Load reset times
                    reset_times_data = data.get("reset_times", {})
                    self._reset_times = {
                        key: datetime.fromisoformat(value)
                        for key, value in reset_times_data.items()
                    }
                    
                    # Check if we need to reset (new day)
                    self._check_and_reset()
            else:
                # Initialize with empty state
                self._initialize_state()
                
        except Exception as e:
            print(f"Error loading rate limit state: {e}")
            self._initialize_state()
    
    def _initialize_state(self) -> None:
        """Initialize rate limit state for all models"""
        for model in GroqModel:
            key = self._get_counter_key(model)
            reset_key = self._get_reset_time_key(model)
            
            self._counters[key] = 0
            self._reset_times[reset_key] = self._get_next_reset_time()
    
    def _save_state(self) -> None:
        """Save rate limit state to storage"""
        try:
            data = {
                "counters": self._counters,
                "reset_times": {
                    key: value.isoformat()
                    for key, value in self._reset_times.items()
                }
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving rate limit state: {e}")
    
    def _get_next_reset_time(self) -> datetime:
        """Calculate next reset time (midnight UTC)"""
        now = datetime.utcnow()
        tomorrow = now + timedelta(days=1)
        return datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0)
    
    def _check_and_reset(self) -> None:
        """Check if it's time to reset counters (new day)"""
        now = datetime.utcnow()
        
        for model in GroqModel:
            reset_key = self._get_reset_time_key(model)
            
            if reset_key in self._reset_times:
                reset_time = self._reset_times[reset_key]
                
                # If current time is past reset time, reset counter
                if now >= reset_time:
                    counter_key = self._get_counter_key(model)
                    self._counters[counter_key] = 0
                    self._reset_times[reset_key] = self._get_next_reset_time()
                    self._save_state()
    
    def check_limit(self, model: GroqModel) -> RateLimitInfo:
        """
        Check current rate limit status for a model.
        
        Args:
            model: Groq model to check
            
        Returns:
            RateLimitInfo with current status
        """
        self._check_and_reset()
        
        counter_key = self._get_counter_key(model)
        reset_key = self._get_reset_time_key(model)
        
        current_count = self._counters.get(counter_key, 0)
        limit = self.RATE_LIMITS[model]
        reset_time = self._reset_times.get(reset_key, self._get_next_reset_time())
        remaining = max(0, limit - current_count)
        
        return RateLimitInfo(
            model=model,
            current_count=current_count,
            limit=limit,
            reset_time=reset_time,
            remaining=remaining
        )
    
    def increment(self, model: GroqModel) -> None:
        """
        Increment the counter for a model after making an API call.
        
        Args:
            model: Groq model that was called
        """
        self._check_and_reset()
        
        counter_key = self._get_counter_key(model)
        self._counters[counter_key] = self._counters.get(counter_key, 0) + 1
        self._save_state()
    
    def check_and_increment(self, model: GroqModel) -> RateLimitInfo:
        """
        Check rate limit and increment counter if not exceeded.
        
        Args:
            model: Groq model to check and increment
            
        Returns:
            RateLimitInfo with updated status
            
        Raises:
            RateLimitExceededError: If rate limit is exceeded
        """
        # Check current status
        info = self.check_limit(model)
        
        # Raise error if limit exceeded
        if info.is_exceeded:
            raise RateLimitExceededError(
                model=model,
                limit=info.limit,
                reset_time=info.reset_time
            )
        
        # Increment counter
        self.increment(model)
        
        # Return updated info
        return self.check_limit(model)
    
    def get_all_limits(self) -> Dict[str, RateLimitInfo]:
        """
        Get rate limit info for all models.
        
        Returns:
            Dictionary mapping model names to RateLimitInfo
        """
        self._check_and_reset()
        
        return {
            model.value: self.check_limit(model)
            for model in GroqModel
        }
    
    def reset_all(self) -> None:
        """
        Manually reset all counters (for testing/admin purposes).
        """
        for model in GroqModel:
            counter_key = self._get_counter_key(model)
            reset_key = self._get_reset_time_key(model)
            
            self._counters[counter_key] = 0
            self._reset_times[reset_key] = self._get_next_reset_time()
        
        self._save_state()
    
    def reset_model(self, model: GroqModel) -> None:
        """
        Manually reset counter for a specific model.
        
        Args:
            model: Model to reset
        """
        counter_key = self._get_counter_key(model)
        reset_key = self._get_reset_time_key(model)
        
        self._counters[counter_key] = 0
        self._reset_times[reset_key] = self._get_next_reset_time()
        
        self._save_state()


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """
    Get or create global rate limiter instance.
    
    Returns:
        RateLimiter instance
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
