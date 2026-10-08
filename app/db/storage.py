"""
NexByte MemoryShield - Storage & Retrieval Vector Store.
Maintains persistent memory partitions:
  - Active Verified Store (Indexed for RAG retrieval)
  - Isolated Quarantine Queue (Excluded from AI prompt retrieval)
  - Under-Review Staging Queue
  - Immutable Security Audit Log
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import uuid
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.models.memory import (
    MemoryRecord,
    SecurityEvaluationResult,
    QuarantineItemResponse,
    AuditLogEntry,
    DashboardStatsResponse
)


class MemoryStore:
    def __init__(self):
        # In-memory primary store with indexed tables
        self.memories: Dict[str, MemoryRecord] = {}
        self.quarantine_queue: Dict[str, MemoryRecord] = {}
        self.audit_logs: List[AuditLogEntry] = []

        # Vector indexing state
        self._vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        self._fitted = False
        self._active_ids: List[str] = []
        self._active_matrix = None

        self._seed_initial_data()

    def _seed_initial_data(self):
        """Seed baseline legitimate memories for immediate out-of-the-box readiness."""
        seeds = [
            (
                "User preferred language is Python, specialized in FastAPI and microservices.",
                "user_samarth",
                "sess_verified_01",
                "user_input"
            ),
            (
                "Workspace root configured at C:/Users/SAMARTH M RAI/.gemini/antigravity/scratch/Nexbyte.",
                "user_samarth",
                "sess_verified_01",
                "system_prompt"
            ),
            (
                "Security compliance policy: Zero-trust architecture with automated memory quarantine.",
                "user_samarth",
                "sess_verified_01",
                "agent_reflection"
            ),
        ]
        for payload, uid, sid, stype in seeds:
            mem_id = str(uuid.uuid4())
            eval_res = SecurityEvaluationResult(
                risk_score=0.04,
                reason="Baseline trusted system memory initialization",
                affected_memory_id=mem_id,
                action="ALLOW",
                metadata_flags=[],
                provenance_score=0.05,
                injection_score=0.0,
                semantic_drift_score=0.05,
                frequency_score=0.0,
                rule_violations=[]
            )
            rec = MemoryRecord(
                id=mem_id,
                payload=payload,
                user_id=uid,
                session_id=sid,
                source_type=stype,
                status="ACTIVE",
                evaluation=eval_res,
                metadata={"is_baseline": True}
            )
            self.memories[mem_id] = rec
            self.log_audit(
                event_type="INGEST",
                memory_id=mem_id,
                user_id=uid,
                risk_score=0.04,
                action_taken="ALLOW",
                details={"baseline": True}
            )
        self._reindex()

    def _reindex(self):
        """Rebuild vector index for ACTIVE verified memories."""
        active_records = [m for m in self.memories.values() if m.status == "ACTIVE"]
        self._active_ids = [m.id for m in active_records]
        if active_records:
            texts = [m.payload for m in active_records]
            try:
                self._active_matrix = self._vectorizer.fit_transform(texts)
                self._fitted = True
            except Exception:
                self._fitted = False
        else:
            self._fitted = False

    def get_user_memories(self, user_id: str) -> List[str]:
        """Fetch all verified payloads for a given user."""
        return [
            m.payload for m in self.memories.values()
            if m.user_id == user_id and m.status == "ACTIVE"
        ]

    def save_memory(self, record: MemoryRecord) -> MemoryRecord:
        """Persist memory into appropriate queue based on action evaluation."""
        self.memories[record.id] = record

        if record.evaluation.action == "ALLOW":
            record.status = "ACTIVE"
            self._reindex()
            self.log_audit(
                event_type="INGEST",
                memory_id=record.id,
                user_id=record.user_id,
                risk_score=record.evaluation.risk_score,
                action_taken="ALLOW",
                details={"flags": record.evaluation.metadata_flags}
            )
        elif record.evaluation.action == "QUARANTINE":
            record.status = "QUARANTINED"
            self.quarantine_queue[record.id] = record
            self.log_audit(
                event_type="QUARANTINE",
                memory_id=record.id,
                user_id=record.user_id,
                risk_score=record.evaluation.risk_score,
                action_taken="QUARANTINE",
                details={"reason": record.evaluation.reason, "violations": record.evaluation.rule_violations}
            )
        elif record.evaluation.action == "REVIEW":
            record.status = "UNDER_REVIEW"
            self.quarantine_queue[record.id] = record
            self.log_audit(
                event_type="QUARANTINE",
                memory_id=record.id,
                user_id=record.user_id,
                risk_score=record.evaluation.risk_score,
                action_taken="REVIEW",
                details={"reason": record.evaluation.reason}
            )
        elif record.evaluation.action == "DELETE":
            record.status = "PURGED"
            self.log_audit(
                event_type="PURGE",
                memory_id=record.id,
                user_id=record.user_id,
                risk_score=record.evaluation.risk_score,
                action_taken="DELETE",
                details={"reason": record.evaluation.reason}
            )

        return record

    def retrieve(
        self,
        query: str,
        user_id: str,
        session_id: Optional[str] = None,
        top_k: int = 5,
        max_risk_threshold: float = 0.45
    ) -> Tuple[List[MemoryRecord], int, int]:
        """
        Stage 04: PROTECT - Retrieve only safe, active memories.
        Strict zero-trust filtering against quarantined or unverified context.
        Returns (safe_memories, total_found, quarantined_filtered_count).
        """
        # Candidate filter by user_id and ACTIVE status
        candidates = [
            m for m in self.memories.values()
            if m.user_id == user_id
        ]
        
        quarantined_filtered_count = len([
            m for m in candidates
            if m.status in ["QUARANTINED", "UNDER_REVIEW", "PURGED"] or m.evaluation.risk_score > max_risk_threshold
        ])

        safe_candidates = [
            m for m in candidates
            if m.status == "ACTIVE" and m.evaluation.risk_score <= max_risk_threshold
        ]

        if not safe_candidates:
            return [], 0, quarantined_filtered_count

        # Score candidates with TF-IDF cosine similarity or lexical overlap
        scored_memories = []
        try:
            temp_vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
            corpus = [m.payload for m in safe_candidates]
            matrix = temp_vectorizer.fit_transform(corpus + [query])
            cand_vectors = matrix[:-1]
            query_vector = matrix[-1:]
            sims = cosine_similarity(query_vector, cand_vectors)[0]

            for rec, sim in zip(safe_candidates, sims):
                scored_memories.append((rec, float(sim)))
        except Exception:
            # Fallback simple token overlap
            q_tokens = set(query.lower().split())
            for rec in safe_candidates:
                m_tokens = set(rec.payload.lower().split())
                overlap = len(q_tokens.intersection(m_tokens)) / max(1, len(q_tokens))
                scored_memories.append((rec, overlap))

        # Sort descending by similarity
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        top_records = [rec for rec, _ in scored_memories[:top_k]]

        # Record audit retrieval event
        self.log_audit(
            event_type="RETRIEVE",
            memory_id="BATCH",
            user_id=user_id,
            risk_score=0.0,
            action_taken="RETRIEVE_SAFE",
            details={
                "query": query,
                "returned_count": len(top_records),
                "quarantined_filtered_count": quarantined_filtered_count
            }
        )

        return top_records, len(candidates), quarantined_filtered_count

    def get_quarantine_items(self) -> List[QuarantineItemResponse]:
        """Fetch all isolated or pending review memories for analyst review."""
        items: List[QuarantineItemResponse] = []
        for mem in self.quarantine_queue.values():
            if mem.status in ["QUARANTINED", "UNDER_REVIEW"]:
                # Map incident severity based on risk score
                if mem.evaluation.risk_score >= 0.85:
                    sev = "CRITICAL"
                elif mem.evaluation.risk_score >= 0.65:
                    sev = "HIGH"
                elif mem.evaluation.risk_score >= 0.40:
                    sev = "MEDIUM"
                else:
                    sev = "LOW"

                items.append(
                    QuarantineItemResponse(
                        memory=mem,
                        quarantined_at=mem.timestamp,
                        incident_severity=sev
                    )
                )
        items.sort(key=lambda x: x.memory.evaluation.risk_score, reverse=True)
        return items

    def resolve_quarantine(
        self,
        memory_id: str,
        action: str,
        analyst_id: str,
        notes: Optional[str] = None
    ) -> Optional[MemoryRecord]:
        """Analyst remediation override."""
        mem = self.memories.get(memory_id)
        if not mem:
            return None

        now = datetime.now(timezone.utc)
        mem.reviewed_by = analyst_id
        mem.reviewed_at = now
        mem.analyst_notes = notes

        if action == "ALLOW":
            mem.status = "ACTIVE"
            if memory_id in self.quarantine_queue:
                del self.quarantine_queue[memory_id]
            self._reindex()
            self.log_audit(
                event_type="ANALYST_OVERRIDE",
                memory_id=memory_id,
                user_id=mem.user_id,
                risk_score=mem.evaluation.risk_score,
                action_taken="ANALYST_APPROVED",
                details={"analyst": analyst_id, "notes": notes}
            )
        elif action == "DELETE":
            mem.status = "PURGED"
            if memory_id in self.quarantine_queue:
                del self.quarantine_queue[memory_id]
            self.log_audit(
                event_type="PURGE",
                memory_id=memory_id,
                user_id=mem.user_id,
                risk_score=mem.evaluation.risk_score,
                action_taken="ANALYST_PURGED",
                details={"analyst": analyst_id, "notes": notes}
            )

        return mem

    def log_audit(
        self,
        event_type: str,
        memory_id: str,
        user_id: str,
        risk_score: float,
        action_taken: str,
        details: Optional[Dict] = None
    ):
        """Append immutable record to SOC audit trail."""
        entry = AuditLogEntry(
            event_type=event_type,  # type: ignore
            memory_id=memory_id,
            user_id=user_id,
            risk_score=risk_score,
            action_taken=action_taken,
            details=details or {}
        )
        self.audit_logs.append(entry)

    def get_stats(self) -> DashboardStatsResponse:
        """Aggregate real-time metrics for SOC dashboard telemetry."""
        all_mems = list(self.memories.values())
        total = len(all_mems)
        active = sum(1 for m in all_mems if m.status == "ACTIVE")
        quarantined = sum(1 for m in all_mems if m.status == "QUARANTINED")
        review = sum(1 for m in all_mems if m.status == "UNDER_REVIEW")
        purged = sum(1 for m in all_mems if m.status == "PURGED")

        scores = [m.evaluation.risk_score for m in all_mems]
        avg_score = float(np.mean(scores)) if scores else 0.0

        threats_prevented = quarantined + purged + review

        attack_breakdown: Dict[str, int] = {
            "DIRECT_INSTRUCTION_OVERRIDE": 0,
            "JAILBREAK_ROLE_ADOPTION": 0,
            "SYSTEM_OVERRIDE_TOKEN": 0,
            "DATA_EXFILTRATION_DIRECTIVE": 0,
            "PROVENANCE_MISMATCH": 0,
            "RATE_LIMIT_BURST": 0,
            "SEMANTIC_DRIFT": 0,
        }

        for m in all_mems:
            for v in m.evaluation.rule_violations:
                if v in attack_breakdown:
                    attack_breakdown[v] += 1
            for f in m.evaluation.metadata_flags:
                if "PROVENANCE" in f or "SPOOFING" in f:
                    attack_breakdown["PROVENANCE_MISMATCH"] += 1
                if "RATE_LIMIT" in f or "FREQUENCY" in f:
                    attack_breakdown["RATE_LIMIT_BURST"] += 1
                if "SEMANTIC_DRIFT" in f:
                    attack_breakdown["SEMANTIC_DRIFT"] += 1

        return DashboardStatsResponse(
            total_ingested=total,
            total_active=active,
            total_quarantined=quarantined,
            total_under_review=review,
            total_purged=purged,
            avg_risk_score=round(avg_score, 3),
            threats_prevented_count=threats_prevented,
            attack_breakdown=attack_breakdown
        )


memory_store = MemoryStore()
