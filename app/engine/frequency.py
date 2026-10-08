"""
NexByte MemoryShield - Unusual Write Frequency & Rate Limiting Engine.
Detects burst injection spikes, automated memory stuffing, and rate limit violations.
"""

import time
from typing import Dict, List, Tuple
from collections import defaultdict
from app.core.config import settings


class FrequencyMonitor:
    def __init__(self):
        # Maps user_id -> list of float timestamps
        self.user_windows: Dict[str, List[float]] = defaultdict(list)
        self.max_writes = settings.MAX_WRITES_PER_WINDOW
        self.window_seconds = settings.WINDOW_SECONDS

    def record_and_evaluate(self, user_id: str) -> Tuple[float, List[str], str]:
        """
        Record a write attempt and calculate the velocity risk score [0.0 - 1.0].
        Returns (risk_score, flags, detail).
        """
        now = time.time()
        timestamps = self.user_windows[user_id]

        # Prune expired timestamps outside sliding window
        valid_timestamps = [ts for ts in timestamps if now - ts <= self.window_seconds]
        valid_timestamps.append(now)
        self.user_windows[user_id] = valid_timestamps

        count = len(valid_timestamps)
        flags: List[str] = []

        if count <= 2:
            score = 0.0
            detail = f"Normal write velocity ({count} writes in {self.window_seconds}s)"
        elif count <= self.max_writes:
            # Scaled between 0.1 and 0.45
            score = 0.10 + 0.35 * ((count - 2) / max(1, self.max_writes - 2))
            detail = f"Elevated write frequency ({count} writes in {self.window_seconds}s)"
        else:
            # Burst breach
            score = min(1.0, 0.70 + (count - self.max_writes) * 0.10)
            flags.append("UNUSUAL_WRITE_FREQUENCY_SPIKE")
            flags.append("RATE_LIMIT_THRESHOLD_EXCEEDED")
            detail = f"Anomaly: Write burst rate exceeded limit ({count}/{self.max_writes} writes in {self.window_seconds}s)"

        return score, flags, detail

    def reset_user(self, user_id: str):
        """Reset frequency tracker for testing or tenant reset."""
        if user_id in self.user_windows:
            del self.user_windows[user_id]


frequency_monitor = FrequencyMonitor()
