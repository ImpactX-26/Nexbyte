"""
NexByte MemoryShield - FastAPI Security Gateway Endpoints
Active security gateway mediating memory write and retrieval operations between AI agents and storage.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
import uuid

from app.models.memory import (
    MemoryIngestRequest,
    SecurityEvaluationResult,
    MemoryRecord,
    MemoryRetrieveRequest,
    MemoryRetrieveResponse,
    QuarantineActionRequest,
    QuarantineItemResponse,
    AuditLogEntry,
    DashboardStatsResponse,
)
from app.engine.detector import detector
from app.db.storage import memory_store

router = APIRouter(prefix="/v1", tags=["MemoryShield Gateway"])


@router.post(
    "/memory/ingest",
    response_model=MemoryRecord,
    status_code=status.HTTP_201_CREATED,
    summary="Evaluate and safely ingest memory write",
    description="Inspects memory for instruction injections, provenance anomalies, and semantic drift. Directs to Active or Quarantine store."
)
async def ingest_memory(request: MemoryIngestRequest):
    # Fetch historical verified memory for baseline semantic drift comparison
    reference_memories = memory_store.get_user_memories(request.user_id)

    # Generate prospective memory ID
    memory_id = str(uuid.uuid4())

    # Stage 01 & 02: Detect and Verify via multi-layer security engine
    evaluation: SecurityEvaluationResult = detector.evaluate(
        request=request,
        reference_memories=reference_memories,
        memory_id=memory_id
    )

    # Stage 03: Construct record and persist into respective partition (Active vs Quarantine)
    record = MemoryRecord(
        id=memory_id,
        payload=request.payload,
        user_id=request.user_id,
        session_id=request.session_id,
        source_type=request.source_type,
        timestamp=request.timestamp,
        status="ACTIVE" if evaluation.action == "ALLOW" else (
            "QUARANTINED" if evaluation.action == "QUARANTINE" else (
                "UNDER_REVIEW" if evaluation.action == "REVIEW" else "PURGED"
            )
        ),
        evaluation=evaluation,
        metadata=request.metadata
    )

    persisted_record = memory_store.save_memory(record)
    return persisted_record


@router.post(
    "/memory/retrieve",
    response_model=MemoryRetrieveResponse,
    status_code=status.HTTP_200_OK,
    summary="Filter and retrieve verified context for AI prompt injection",
    description="Stage 04: PROTECT. Applies zero-trust perimeter filtering, excluding quarantined or high-risk memories."
)
async def retrieve_memory(request: MemoryRetrieveRequest):
    memories, total_found, quarantined_filtered_count = memory_store.retrieve(
        query=request.query,
        user_id=request.user_id,
        session_id=request.session_id,
        top_k=request.top_k,
        max_risk_threshold=request.max_risk_threshold
    )

    # Format verified, safe context block for injection into AI system prompt
    context_lines = []
    if memories:
        context_lines.append("### [MEMORYSHIELD VERIFIED CONTEXT]")
        for idx, mem in enumerate(memories, start=1):
            context_lines.append(
                f"- [Item #{idx} | Source: {mem.source_type} | Risk: {mem.evaluation.risk_score:.2f}]: {mem.payload}"
            )
    else:
        context_lines.append("### [MEMORYSHIELD: NO VERIFIED MEMORIES MATCHING QUERY]")

    safe_context_str = "\n".join(context_lines)

    return MemoryRetrieveResponse(
        query=request.query,
        total_found=total_found,
        returned_count=len(memories),
        quarantined_filtered_count=quarantined_filtered_count,
        memories=memories,
        safe_context_str=safe_context_str
    )


@router.get(
    "/quarantine",
    response_model=List[QuarantineItemResponse],
    summary="List isolated high-risk memories awaiting analyst triage",
    description="Enables SOC operators and security analysts to inspect quarantined injections and anomalies."
)
async def list_quarantine():
    return memory_store.get_quarantine_items()


@router.post(
    "/quarantine/{memory_id}/action",
    response_model=MemoryRecord,
    summary="Manual analyst remediation override for quarantined item",
    description="Allows authorized analysts to either ALLOW (promote to active memory) or DELETE (purge completely)."
)
async def resolve_quarantined_memory(memory_id: str, body: QuarantineActionRequest):
    resolved = memory_store.resolve_quarantine(
        memory_id=memory_id,
        action=body.action,
        analyst_id=body.analyst_id,
        notes=body.notes
    )
    if not resolved:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quarantined memory record with ID '{memory_id}' not found."
        )
    return resolved


@router.get(
    "/dashboard/stats",
    response_model=DashboardStatsResponse,
    summary="Real-time SOC telemetry metrics",
    description="Provides aggregate statistics on ingestion volume, quarantine isolation, and threat breakdown."
)
async def get_dashboard_stats():
    return memory_store.get_stats()


@router.get(
    "/audit/logs",
    response_model=List[AuditLogEntry],
    summary="Retrieve immutable security audit trail",
    description="Lists recent audit events across ingestion, quarantine, retrieval, and analyst interventions."
)
async def get_audit_logs(limit: int = 50):
    logs = memory_store.audit_logs[-limit:]
    return list(reversed(logs))


@router.get(
    "/health",
    summary="System health check",
    tags=["Health"]
)
async def health_check():
    return {
        "status": "operational",
        "service": "NexByte MemoryShield Gateway",
        "version": "1.0.0",
        "protection_layer": "ACTIVE"
    }
