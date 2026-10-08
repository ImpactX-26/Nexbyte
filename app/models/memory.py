"""
NexByte MemoryShield - Pydantic Data Models & Schemas
Core definitions for memory ingestion, verification, security evaluation, and audit records.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
import uuid


class MemoryIngestRequest(BaseModel):
    """Payload incoming from an AI agent or context pipeline for long-term storage."""
    payload: str = Field(..., description="The raw textual memory content to persist", min_length=1)
    user_id: str = Field(..., description="Unique identifier for the user claiming the memory")
    session_id: str = Field(..., description="Active session token or identifier")
    source_type: Literal[
        "user_input", 
        "system_prompt", 
        "agent_reflection", 
        "external_rag", 
        "tool_output", 
        "untrusted_web"
    ] = Field(default="user_input", description="Origin source category of the memory")
    timestamp: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Ingestion timestamp"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Supplemental contextual metadata such as IP, source trust level, claims"
    )


class SecurityEvaluationResult(BaseModel):
    """Detailed explainable security evaluation of a proposed memory update."""
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Composite aggregate risk score [0.0 - 1.0]")
    reason: str = Field(..., description="Human-explainable justification for the assigned action")
    affected_memory_id: str = Field(..., description="Target or generated ID of the evaluated memory")
    action: Literal["ALLOW", "REVIEW", "QUARANTINE", "DELETE"] = Field(
        ..., 
        description="Security enforcement action"
    )
    metadata_flags: List[str] = Field(
        default_factory=list, 
        description="List of detected anomalies or security policy flags"
    )
    provenance_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Risk sub-score for provenance mismatch")
    injection_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Risk sub-score for prompt/instruction injection")
    semantic_drift_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Risk sub-score for semantic inconsistency")
    frequency_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Risk sub-score for unusual write burst rate")
    rule_violations: List[str] = Field(default_factory=list, description="Specific security rule trigger names")


class MemoryRecord(BaseModel):
    """Persisted memory entity with its associated verification and lifecycle status."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    payload: str
    user_id: str
    session_id: str
    source_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: Literal["ACTIVE", "QUARANTINED", "UNDER_REVIEW", "PURGED"] = "ACTIVE"
    evaluation: SecurityEvaluationResult
    metadata: Dict[str, Any] = Field(default_factory=dict)
    analyst_notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None


class MemoryRetrieveRequest(BaseModel):
    """Query to fetch safe, verified memories for injection into prompt context."""
    query: str = Field(..., description="Retrieval query or semantic topic", min_length=1)
    user_id: str = Field(..., description="User ID context boundary")
    session_id: Optional[str] = Field(default=None, description="Optional session context boundary")
    top_k: int = Field(default=5, ge=1, le=50, description="Maximum number of context snippets")
    max_risk_threshold: float = Field(
        default=0.45, 
        ge=0.0, 
        le=1.0, 
        description="Maximum risk threshold allowed into the prompt context"
    )


class MemoryRetrieveResponse(BaseModel):
    """Sanitized memory context ready for AI model retrieval."""
    query: str
    total_found: int
    returned_count: int
    quarantined_filtered_count: int
    memories: List[MemoryRecord]
    safe_context_str: str = Field(..., description="Pre-sanitized consolidated context block for LLM prompt")


class QuarantineActionRequest(BaseModel):
    """Security Analyst remediation action for quarantined memories."""
    action: Literal["ALLOW", "DELETE"] = Field(..., description="Decision: Approve into active memory or purge permanently")
    analyst_id: str = Field(..., description="ID of the reviewing security analyst")
    notes: Optional[str] = Field(default="", description="Justification and audit notes for the decision")


class QuarantineItemResponse(BaseModel):
    """Quarantine review queue record."""
    memory: MemoryRecord
    quarantined_at: datetime
    incident_severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class AuditLogEntry(BaseModel):
    """Immutable audit trail log record."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: Literal["INGEST", "QUARANTINE", "RETRIEVE", "ANALYST_OVERRIDE", "PURGE"]
    memory_id: str
    user_id: str
    risk_score: float
    action_taken: str
    details: Dict[str, Any] = Field(default_factory=dict)


class DashboardStatsResponse(BaseModel):
    """SOC telemetry metrics for the dashboard."""
    total_ingested: int
    total_active: int
    total_quarantined: int
    total_under_review: int
    total_purged: int
    avg_risk_score: float
    threats_prevented_count: int
    attack_breakdown: Dict[str, int]
