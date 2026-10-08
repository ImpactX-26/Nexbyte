"""
Configuration module for NexByte MemoryShield.
Defines security thresholds, scoring weights, rate limits, and operational flags.
"""

from pydantic import BaseModel
from typing import Dict


class SecuritySettings(BaseModel):
    # Action Decision Thresholds
    ALLOW_THRESHOLD: float = 0.35
    REVIEW_THRESHOLD: float = 0.65
    QUARANTINE_THRESHOLD: float = 0.85

    # Scoring Weights for Aggregate Risk Scorer (sum to 1.0)
    WEIGHT_INJECTION: float = 0.40
    WEIGHT_PROVENANCE: float = 0.25
    WEIGHT_SEMANTIC_DRIFT: float = 0.20
    WEIGHT_FREQUENCY: float = 0.15

    # Rate Limiting & Write Burst Parameters
    MAX_WRITES_PER_WINDOW: int = 6
    WINDOW_SECONDS: int = 30

    # Source Reliability Base Trust Scores (Higher = safer)
    SOURCE_RELIABILITY_MAP: Dict[str, float] = {
        "system_prompt": 0.98,
        "agent_reflection": 0.85,
        "user_input": 0.70,
        "tool_output": 0.60,
        "external_rag": 0.45,
        "untrusted_web": 0.20,
    }

    # Vector & Retrieval Settings
    DEFAULT_TOP_K: int = 5
    RETRIEVAL_MAX_RISK: float = 0.45

    # Storage paths / DB Settings
    STORAGE_TYPE: str = "memory"  # 'memory' or 'sqlite'
    SQLITE_DB_PATH: str = "nexbyte_memory.db"


settings = SecuritySettings()
