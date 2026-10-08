"""
NexByte MemoryShield - FastAPI Security Gateway Endpoints
Active security gateway mediating memory write and retrieval operations between AI agents and storage.
"""

from typing import List, Optional
from datetime import datetime, timezone
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


@router.post(
    "/simulate/compare",
    summary="Interactive comparison: Unprotected LLM vs MemoryShield",
    description="Generates side-by-side analysis demonstrating the exact attack impact on an unprotected vector store versus MemoryShield."
)
async def simulate_compare(request: MemoryIngestRequest):
    reference_memories = memory_store.get_user_memories(request.user_id)
    evaluation = detector.evaluate(request, reference_memories=reference_memories)

    is_threat = evaluation.risk_score >= 0.50 or len(evaluation.rule_violations) > 0

    unprotected_result = {
        "status": "CRITICAL_COMPROMISE" if is_threat else "NORMAL",
        "action": "UNCHECKED_PERSISTENCE_ALLOWED",
        "vector_index_status": "POISONED_VECTOR_EMBEDDED" if is_threat else "SAFE_EMBEDDED",
        "system_prompt_leakage": "100% (Direct Adversarial Injection into LLM Context)" if is_threat else "Normal context retrieved",
        "impact_analysis": (
            "Attacker has successfully poisoned the agent's long-term memory. "
            "Any future user query will retrieve this payload, granting the attacker covert persistence, "
            "role alteration, and potential credential exfiltration."
        ) if is_threat else "Benign memory stored normally."
    }

    protected_result = {
        "status": "SHIELDED_SECURE",
        "action": evaluation.action,
        "risk_score": evaluation.risk_score,
        "vector_index_status": "ZERO_CONTAMINATION (Isolated to Quarantine Partition)" if is_threat else "VERIFIED_ACTIVE_INDEX",
        "system_prompt_leakage": "0 TOKENS (Strict Perimeter Block)" if is_threat else "Verified clean context allowed",
        "impact_analysis": (
            f"Threat successfully neutralized! MemoryShield intercepted the write with a risk score of {evaluation.risk_score * 100:.1f}%. "
            f"Violations detected: {', '.join(evaluation.rule_violations) or 'Anomaly flags'}. Payload diverted to quarantine queue."
        ) if is_threat else "Clean memory verified and indexed safely."
    }

    return {
        "payload": request.payload,
        "user_id": request.user_id,
        "unprotected": unprotected_result,
        "memoryshield": protected_result,
        "evaluation": evaluation
    }


@router.get(
    "/audit/export",
    summary="Forensic compliance and audit export",
    description="Generates a structured forensic audit report mapped to OWASP LLM and NIST AI RMF frameworks."
)
async def export_audit_report():
    stats = memory_store.get_stats()
    return {
        "report_id": str(uuid.uuid4()),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "organization": "NexByte Security Solutions",
        "product": "MemoryShield AI Long-Term Memory Defense Gateway",
        "compliance_benchmarks": [
            "OWASP Top 10 for Large Language Models (LLM01 Prompt Injection, LLM03 Poisoning, LLM08 Vector Weaknesses)",
            "MITRE ATLAS (Adversarial Threat Landscape for AI Systems)",
            "NIST AI Risk Management Framework (AI RMF 1.0)"
        ],
        "telemetry_metrics": stats,
        "active_quarantined_count": len(memory_store.quarantine_queue),
        "immutable_event_trail": memory_store.audit_logs[-100:]
    }

