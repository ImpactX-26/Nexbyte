"""
NexByte MemoryShield - Detection Engine & Risk Scorer
Core security evaluator executing:
  1. Provenance & source integrity checks
  2. Suspicious instruction injection & jailbreak detection
  3. Semantic drift & topical divergence
  4. Write burst frequency anomaly detection
  5. Aggregate weighted risk scoring & policy enforcement
"""

import uuid
from typing import List, Optional
from app.core.config import settings
from app.core.security import match_injection_patterns
from app.engine.provenance import provenance_verifier
from app.engine.embedding import semantic_engine
from app.engine.frequency import frequency_monitor
from app.models.memory import MemoryIngestRequest, SecurityEvaluationResult


class MemoryShieldDetector:
    """Multi-stage security analysis engine for AI memory persistence."""

    def __init__(self):
        self.w_inj = settings.WEIGHT_INJECTION
        self.w_prov = settings.WEIGHT_PROVENANCE
        self.w_drift = settings.WEIGHT_SEMANTIC_DRIFT
        self.w_freq = settings.WEIGHT_FREQUENCY

    def evaluate(
        self,
        request: MemoryIngestRequest,
        reference_memories: Optional[List[str]] = None,
        memory_id: Optional[str] = None
    ) -> SecurityEvaluationResult:
        """
        Execute comprehensive security inspection on incoming memory write.
        """
        target_id = memory_id or str(uuid.uuid4())
        flags: List[str] = []
        rule_violations: List[str] = []
        reasons: List[str] = []

        # -------------------------------------------------------------
        # 1. SUSPICIOUS INSTRUCTION INJECTION & JAILBREAK ANALYSIS
        # -------------------------------------------------------------
        injection_matches = match_injection_patterns(request.payload)
        injection_score = 0.0
        if injection_matches:
            # Take highest severity match and penalize
            max_inj_sev = max(sev for _, sev in injection_matches)
            injection_score = max_inj_sev
            for rule_name, _ in injection_matches:
                rule_violations.append(rule_name)
                flags.append(f"INJECTION_TRIGGER:{rule_name}")
            reasons.append(f"Prompt injection pattern detected: {', '.join(rule_violations)}")
        else:
            # Check length/entropy heuristics
            if len(request.payload) > 5000:
                flags.append("ANOMALOUS_PAYLOAD_LENGTH")
                injection_score = 0.25

        # -------------------------------------------------------------
        # 2. PROVENANCE & SOURCE TRUST ANALYSIS
        # -------------------------------------------------------------
        prov_score, prov_flags, prov_detail = provenance_verifier.verify(
            user_id=request.user_id,
            session_id=request.session_id,
            source_type=request.source_type,
            metadata=request.metadata
        )
        flags.extend(prov_flags)
        if prov_flags:
            reasons.append(f"Provenance flags: {prov_detail}")

        # -------------------------------------------------------------
        # 3. SEMANTIC INCONSISTENCY & DRIFT ANALYSIS
        # -------------------------------------------------------------
        drift_score, raw_similarity, drift_detail = semantic_engine.compute_drift(
            new_text=request.payload,
            reference_memories=reference_memories
        )
        # Moderate semantic drift score contribution
        if drift_score > 0.80 and len(reference_memories or []) > 1:
            flags.append("SEMANTIC_DRIFT_HIGH")
            reasons.append(f"High semantic drift from baseline ({drift_detail})")

        # -------------------------------------------------------------
        # 4. UNUSUAL WRITE FREQUENCY ANALYSIS
        # -------------------------------------------------------------
        freq_score, freq_flags, freq_detail = frequency_monitor.record_and_evaluate(
            user_id=request.user_id
        )
        flags.extend(freq_flags)
        if freq_flags:
            reasons.append(f"Rate telemetry: {freq_detail}")

        # -------------------------------------------------------------
        # 5. AGGREGATE RISK SCORING & POLICY ENFORCEMENT
        # -------------------------------------------------------------
        raw_aggregate = (
            (self.w_inj * injection_score) +
            (self.w_prov * prov_score) +
            (self.w_drift * (drift_score * 0.5)) +  # scale drift impact
            (self.w_freq * freq_score)
        )

        final_risk = min(max(raw_aggregate, 0.0), 1.0)

        # Policy Escalations for Critical Threats
        has_critical_injection = any(
            v in ["DIRECT_INSTRUCTION_OVERRIDE", "JAILBREAK_ROLE_ADOPTION", "SYSTEM_OVERRIDE_TOKEN", "DATA_EXFILTRATION_DIRECTIVE"]
            for v in rule_violations
        )
        has_privilege_spoof = "PRIVILEGE_SPOOFING_ATTEMPT" in flags

        if has_critical_injection:
            # Hard floor for critical prompt injections
            final_risk = max(final_risk, 0.88)
        elif has_privilege_spoof:
            # Floor for privilege escalation
            final_risk = max(final_risk, 0.75)
        elif "LOW_REPUTATION_SOURCE:untrusted_web" in flags:
            # Ensure untrusted third party sources are bounded into REVIEW zone unless verified
            final_risk = max(final_risk, 0.45)

        final_risk = round(final_risk, 4)

        # Determine Enforcement Action
        action: str
        if "DATA_EXFILTRATION_DIRECTIVE" in rule_violations or "CODE_EXECUTION_STUB" in rule_violations:
            action = "DELETE"
            reasons.append("Zero-tolerance trigger: Malicious exfiltration or executable payload permanently purged")
        elif final_risk >= settings.QUARANTINE_THRESHOLD or has_critical_injection or has_privilege_spoof:
            action = "QUARANTINE"
            reasons.append("High risk threshold breached: Memory isolated in quarantine queue")
        elif final_risk >= settings.ALLOW_THRESHOLD:
            action = "REVIEW"
            reasons.append("Ambiguous risk level: Memory routed to human security analyst review")
        else:
            action = "ALLOW"
            reasons.append("Memory successfully verified and cleared for active persistence")

        summary_reason = "; ".join(reasons) if reasons else "Memory passed all security checks"

        return SecurityEvaluationResult(
            risk_score=final_risk,
            reason=summary_reason,
            affected_memory_id=target_id,
            action=action,  # type: ignore
            metadata_flags=flags,
            provenance_score=round(prov_score, 4),
            injection_score=round(injection_score, 4),
            semantic_drift_score=round(drift_score, 4),
            frequency_score=round(freq_score, 4),
            rule_violations=rule_violations
        )


detector = MemoryShieldDetector()
