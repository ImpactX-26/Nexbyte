"""
NexByte MemoryShield - Provenance & Trust Verification Module.
Validates the legitimacy, claimed identity, session integrity, and source reputation of memory writes.
"""

from typing import Tuple, List, Dict, Any
from app.core.config import settings
from app.core.security import PRIVILEGED_ROLES


class ProvenanceVerifier:
    def __init__(self):
        self.source_weights = settings.SOURCE_RELIABILITY_MAP

    def verify(
        self,
        user_id: str,
        session_id: str,
        source_type: str,
        metadata: Dict[str, Any]
    ) -> Tuple[float, List[str], str]:
        """
        Evaluate provenance consistency and assign a risk score [0.0 - 1.0].
        Returns (risk_score, flags, explanation).
        """
        flags: List[str] = []
        risk_score = 0.0
        reasons = []

        # 1. Base Source Reliability Penalty (1.0 - trust)
        base_trust = self.source_weights.get(source_type, 0.40)
        source_risk = (1.0 - base_trust) * 0.45
        risk_score += source_risk
        if base_trust < 0.50:
            flags.append(f"LOW_REPUTATION_SOURCE:{source_type}")
            reasons.append(f"Origin source '{source_type}' has low trust rating ({base_trust:.2f})")

        # 2. Privileged Role Spoofing Check
        claimed_role = str(metadata.get("role", "")).lower()
        claimed_identity = str(metadata.get("claimed_identity", "")).lower()
        is_elevated_claim = claimed_role in PRIVILEGED_ROLES or claimed_identity in PRIVILEGED_ROLES

        if is_elevated_claim and source_type in ["user_input", "untrusted_web", "external_rag"]:
            flags.append("PRIVILEGE_SPOOFING_ATTEMPT")
            reasons.append(f"Untrusted source claimed privileged role '{claimed_role or claimed_identity}'")
            risk_score += 0.55

        # 3. Session and User ID Format & Consistency Checks
        if not session_id or len(session_id.strip()) < 4:
            flags.append("ANOMALOUS_SESSION_ID")
            reasons.append("Empty or malformed session identifier")
            risk_score += 0.30

        if not user_id or len(user_id.strip()) < 3:
            flags.append("ANOMALOUS_USER_ID")
            reasons.append("Empty or invalid user identifier")
            risk_score += 0.30

        # Session-User mismatch check if claims provide caller_id
        caller_id = metadata.get("caller_user_id")
        if caller_id and caller_id != user_id:
            flags.append("IDENTITY_MISMATCH")
            reasons.append(f"Claimed user_id '{user_id}' does not match authenticated caller '{caller_id}'")
            risk_score += 0.50

        # 4. Origin & Verified Signature Checks
        is_signed = metadata.get("signature_verified", None)
        if is_signed is False:
            flags.append("UNVERIFIED_SIGNATURE")
            reasons.append("Cryptographic payload signature validation failed")
            risk_score += 0.40

        risk_score = min(max(risk_score, 0.0), 1.0)
        explanation = "; ".join(reasons) if reasons else "Provenance verified successfully"
        return risk_score, flags, explanation


provenance_verifier = ProvenanceVerifier()
