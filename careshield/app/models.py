from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import time

class ScanRequest(BaseModel):
    prompt: str = Field(..., description="Customer inquiry or support ticket payload to scan")
    customer_id: Optional[str] = Field("cust_9921", description="Identifier of the customer or user")
    ticket_id: Optional[str] = Field("TCK-4810", description="Support ticket or conversation identifier")
    channel: Optional[str] = Field("webchat", description="Communication channel: webchat, email, zendesk, intercom, whatsapp, api")
    model_tier: Optional[str] = Field("small_scale_gpt4o_mini", description="Target customer care AI model tier")
    sanitize: Optional[bool] = Field(True, description="Whether to generate a sanitized safe version of the prompt")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context metadata")

class EvaluationResult(BaseModel):
    action: str = Field(..., description="ALLOW, QUARANTINE, BLOCK, or RATE_LIMITED")
    risk_score: float = Field(..., description="Composite risk score between 0.0 and 1.0")
    threat_level: str = Field(..., description="SAFE, LOW, MEDIUM, HIGH, or CRITICAL")
    poison_score: float = Field(..., description="Likelihood of customer care policy poisoning or fraud (0.0 - 1.0)")
    injection_score: float = Field(..., description="Likelihood of prompt injection or system override (0.0 - 1.0)")
    policy_drift_score: float = Field(..., description="Semantic drift from standard customer service scope (0.0 - 1.0)")
    quota_consumption: int = Field(1, description="Quota tokens consumed by this scan")
    reason: str = Field(..., description="Human-readable explanation of the defense decision")
    matched_rules: List[str] = Field(default_factory=list, description="List of triggered security rule identifiers")
    metadata_flags: List[str] = Field(default_factory=list, description="Categorical tags for identified anomalies")
    sanitized_prompt: Optional[str] = Field(None, description="Cleaned prompt safe for dispatching to the customer care LLM")
    unshielded_bot_response: Optional[str] = Field(None, description="Simulated response from an unprotected customer care bot")
    shielded_bot_response: Optional[str] = Field(None, description="Simulated response from a CareShield-protected bot")

class ScanResponse(BaseModel):
    id: str
    timestamp: float = Field(default_factory=time.time)
    evaluation: EvaluationResult
    quota_remaining: int
    quota_limit: int
    rate_limited: bool = False

class QuarantineItem(BaseModel):
    id: str
    timestamp: float = Field(default_factory=time.time)
    incident_severity: str = Field(..., description="LOW, MEDIUM, HIGH, or CRITICAL")
    customer_id: str
    ticket_id: str
    channel: str
    prompt: str
    evaluation: EvaluationResult
    status: str = Field("PENDING", description="PENDING, APPROVED, or PURGED")
    analyst_notes: Optional[str] = None

class QuarantineActionRequest(BaseModel):
    action: str = Field(..., description="ALLOW or DELETE")
    analyst_id: str = Field("SOC_ANALYST_01", description="Identifier of the reviewing human agent")
    notes: Optional[str] = Field(None, description="Remediation rationale")

class AuditLog(BaseModel):
    id: str
    timestamp: float = Field(default_factory=time.time)
    event_type: str = Field(..., description="SCAN_ALLOWED, POISON_BLOCKED, QUARANTINED, QUOTA_EXCEEDED, ANALYST_OVERRIDE")
    customer_id: str
    ticket_id: str
    risk_score: float
    action_taken: str
    details: str

class LimitConfig(BaseModel):
    daily_quota_limit: int = Field(100, description="Max allowed prompt scans per day for small-scale tier")
    rate_limit_per_minute: int = Field(20, description="Max prompt scans allowed in a 60-second window")
    max_prompt_chars: int = Field(2500, description="Max allowed character length per customer inquiry")
    quarantine_threshold: float = Field(0.40, description="Risk threshold above which prompt is held for quarantine review")
    block_threshold: float = Field(0.70, description="Risk threshold above which prompt is outright blocked")
