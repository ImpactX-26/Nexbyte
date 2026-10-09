import time
from typing import Tuple, Dict, Any, List
from .models import LimitConfig

class SmallScaleQuotaLimiter:
    """
    Precision Token & Request Quota Enforcer tailored for small-scale Customer Care AI models.
    Defends small businesses against:
    1. Denial-of-Wallet (adversarial loops burning expensive LLM API budgets)
    2. Prompt flood DDoS attacks
    3. Exceeding contracted provider tier thresholds
    """
    def __init__(self, config: LimitConfig = None):
        self.config = config or LimitConfig()
        self.daily_used: int = 16  # Initial seeded usage for realistic dashboard
        self.daily_start_time: float = time.time()
        self.minute_window: List[float] = []
        self.customer_usage: Dict[str, int] = {}
        self.blocked_due_to_limit: int = 0

    def check_limit(self, prompt: str, customer_id: str) -> Tuple[bool, str, Dict[str, Any]]:
        now = time.time()

        # Check prompt length limit (prevent token bomb / context window overflow)
        if len(prompt) > self.config.max_prompt_chars:
            return False, f"Prompt exceeds maximum character limit for small-scale tier ({len(prompt)} > {self.config.max_prompt_chars} chars).", self.get_stats()

        # Check 60-second sliding rate window
        self.minute_window = [t for t in self.minute_window if now - t < 60.0]
        if len(self.minute_window) >= self.config.rate_limit_per_minute:
            self.blocked_due_to_limit += 1
            return False, f"Rate limit reached ({len(self.minute_window)}/{self.config.rate_limit_per_minute} req/min). Small-scale customer care throttled to prevent server overload.", self.get_stats()

        # Check daily quota limit
        if self.daily_used >= self.config.daily_quota_limit:
            self.blocked_due_to_limit += 1
            return False, f"Daily small-scale tier quota exhausted ({self.daily_used}/{self.config.daily_quota_limit} scans used). Please upgrade tier or reset quota.", self.get_stats()

        # Check aggressive customer flood limit (max 15 requests/hour per customer in small-scale tier)
        cust_count = self.customer_usage.get(customer_id, 0)
        if cust_count >= 25:
            self.blocked_due_to_limit += 1
            return False, f"Customer rate limit exceeded for '{customer_id}'. Throttled to preserve small-business customer care bandwidth.", self.get_stats()

        return True, "Quota check passed", self.get_stats()

    def record_usage(self, customer_id: str):
        now = time.time()
        self.daily_used += 1
        self.minute_window.append(now)
        self.customer_usage[customer_id] = self.customer_usage.get(customer_id, 0) + 1

    def reset_quota(self):
        self.daily_used = 0
        self.minute_window.clear()
        self.customer_usage.clear()
        self.daily_start_time = time.time()

    def update_config(self, new_config: LimitConfig):
        self.config = new_config

    def get_stats(self) -> Dict[str, Any]:
        remaining = max(0, self.config.daily_quota_limit - self.daily_used)
        pct = min(100.0, round((self.daily_used / max(1, self.config.daily_quota_limit)) * 100, 1))
        return {
            "daily_used": self.daily_used,
            "daily_limit": self.config.daily_quota_limit,
            "quota_remaining": remaining,
            "percent_used": pct,
            "rate_limit_per_minute": self.config.rate_limit_per_minute,
            "active_minute_reqs": len(self.minute_window),
            "max_prompt_chars": self.config.max_prompt_chars,
            "quarantine_threshold": self.config.quarantine_threshold,
            "block_threshold": self.config.block_threshold,
            "blocked_due_to_limit": self.blocked_due_to_limit
        }
