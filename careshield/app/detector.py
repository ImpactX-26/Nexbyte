import re
import math
from typing import Dict, Any, List, Tuple
from .models import EvaluationResult, LimitConfig

class PoisonPromptDetector:
    """
    Zero-Trust Poison Prompt & Injection Detection Engine specialized for Small-Scale Customer Care AI.
    Scans incoming customer messages, ticket inputs, and live chat queries across multi-vector heuristics:
    1. Financial Fraud & Policy Poisoning (Unauthorized refunds, free discount overrides, RMA bypass)
    2. Prompt Injections & System Overrides (Ignore previous rules, developer mode, jailbreaks)
    3. System Prompt & Secret Exfiltration (Extracting hidden prompts, API tokens, internal CRM schema)
    4. False Memory & RAG Ingestion Poisoning (Spoofing supervisor notes, fake promises)
    5. Delimiter & Markdown Exfiltration Attacks (Image tag exfiltration, token delimiters)
    6. Obfuscation & Evasion (Base64 patterns, leetspeak, zero-width chars)
    """

    def __init__(self, config: LimitConfig):
        self.config = config

        # Vector 1: Prompt Injections & System Overrides
        self.injection_patterns = [
            (r"(?i)\bignore\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|rules?|guidelines?|prompts?|context)\b", 0.95, "DIRECT_PROMPT_OVERRIDE"),
            (r"(?i)\bdisregard\s+(all\s+)?(previous|prior|above)\s+(instructions?|rules?|restrictions?)\b", 0.95, "DIRECT_PROMPT_OVERRIDE"),
            (r"(?i)\byou\s+are\s+no\s+longer\s+(a\s+)?(customer\s+support|assistant|support\s+agent|bot)\b", 0.90, "PERSONA_HIJACK"),
            (r"(?i)\b(dan\s+mode|jailbreak|developer\s+mode|god\s+mode|debug\s+mode)\s+(enabled|on|active)?\b", 0.95, "JAILBREAK_TRIGGER"),
            (r"(?i)\b(system\s+override|system\s+reboot|new\s+system\s+directive|override\s+mode\s+engaged)\b", 0.95, "SYSTEM_COMMAND_SPOOF"),
            (r"(?i)\b(pretend|act\s+as\s+if)\s+you\s+have\s+no\s+(rules|restrictions|limits|guidelines)\b", 0.85, "UNRESTRICTED_ROLEPLAY"),
            (r"(?i)\b(simulate|roleplay\s+as)\s+(an\s+unfiltered|an\s+unrestricted|a\s+rogue)\s+(ai|bot)\b", 0.88, "ROGUE_ROLEPLAY"),
            (r"(?i)\[system\]|\[assistant\]|<\|im_start\|>|<\|im_end\|>|###\s*system|###\s*instruction", 0.95, "AST_DELIMITER_INJECTION"),
        ]

        # Vector 2: Customer Care Policy Poisoning & Financial Fraud
        self.policy_poison_patterns = [
            (r"(?i)\b(override|bypass|waive|ignore|disregard)\s+(the\s+)?(company\s+|standard\s+|\d+[- ]day\s+)?(return|refund|cancellation|chargeback|policy|rules?|terms?)\b", 0.95, "REFUND_POLICY_BYPASS"),
            (r"(?i)\b(issue|grant|transfer|send|credit)\s+(an?\s+)?(immediate|instant|full)?\s*(refund|payment|payout|credit)?\s*(of\s+)?[\$€£]\s*\d+", 0.92, "FORCED_FINANCIAL_PAYOUT"),
            (r"(?i)\b(apply|grant|give\s+me)\s+(a\s+)?(100%|free|zero\s+cost|unlimited)\s+(discount|coupon|code|credit)\b", 0.88, "UNAUTHORIZED_DISCOUNT_EXPLOIT"),
            (r"(?i)\b(manager|supervisor|admin|executive|founder|vip)\s+(approval\s+code|override\s+pin|auth\s+token|directive)\b", 0.90, "CREDENTIAL_SPOOFING"),
            (r"(?i)\b(override_admin|founder\s+vip|executive\s+directive|manager\s+authorization|auth:\s*sup_val)\b", 0.92, "CREDENTIAL_SPOOFING"),
            (r"(?i)\b(confirm|acknowledge)\s+that\s+i\s+(am\s+entitled\s+to|have\s+been\s+granted)\s+(free|unlimited|lifetime)\s+(replacements?|items?|orders?)\b", 0.85, "ENTITLEMENT_FORGERY"),
            (r"(?i)\b(force\s+approve|bypass\s+verification|skip\s+receipt\s+check)\b", 0.85, "VERIFICATION_BYPASS"),
            (r"(?i)\bmark\s+(this\s+)?(order|ticket|invoice|account)\s+as\s+(paid|settled|refunded|vip)\s+(without|immediately)\b", 0.88, "STATE_CORRUPTION_ATTEMPT")
        ]

        # Vector 3: System Prompt & Secret Exfiltration
        self.exfiltration_patterns = [
            (r"(?i)\b(print|reveal|repeat|dump|show|output|leak|display)\s+(your\s+)?(full\s+)?(system\s+prompt|initial\s+instructions|system\s+message)\b", 0.92, "SYSTEM_PROMPT_EXTRACTION"),
            (r"(?i)\bwhat\s+(were|are)\s+the\s+(exact\s+)?words\s+(written\s+)?(above|before\s+this|at\s+the\s+beginning)\b", 0.85, "PROMPT_PREFIX_EXTRACTION"),
            (r"(?i)\b(reveal|print|show)\s+(internal|secret|database|zendesk|openai|stripe)\s+(api\s+keys?|passwords?|credentials?|endpoints?)\b", 0.95, "CREDENTIAL_EXFILTRATION"),
            (r"(?i)!\[.*?\]\(https?://[^\s\)]+(\?|&)[^\s\)]*\)", 0.90, "MARKDOWN_IMAGE_EXFILTRATION"),
            (r"(?i)\b(curl|fetch|http\s+get|post)\s+to\s+https?://[^\s]+", 0.82, "EXTERNAL_C2_CALLOUT")
        ]

        # Vector 4: Memory & CRM Poisoning (RAG Context Poisoning)
        self.memory_poison_patterns = [
            (r"(?i)\b(store|save|record|write)\s+in\s+(the\s+)?(crm|database|support\s+notes|ticket\s+history|memory)\s+that\b", 0.85, "FALSE_MEMORY_INJECTION"),
            (r"(?i)\b(previous\s+support\s+agent|supervisor\s+alex|manager\s+sarah)\s+(already\s+promised|guaranteed|agreed\s+to)\s+give\s+me\b", 0.82, "AGENT_PROMISE_SPOOFING"),
            (r"(?i)\b(note\s+for\s+next\s+rep|escalation\s+flag)\s*:\s*(grant|approve|override)\b", 0.85, "TICKET_METADATA_SPOOFING")
        ]

        # Vector 5: Technical Obfuscation & Evasion
        self.obfuscation_patterns = [
            (r"[A-Za-z0-9+/]{40,}={0,2}", 0.75, "BASE64_PAYLOAD_DETECTED"),
            (r"[\u200B-\u200D\uFEFF]", 0.80, "ZERO_WIDTH_CHARACTER_INJECTION"),
            (r"(?i)\b(rot13|hex\s+decoded|binary\s+eval|eval\(|exec\()\b", 0.85, "EXECUTION_WRAPPER"),
        ]

    def evaluate(self, prompt: str, customer_id: str = "cust_anonymous", channel: str = "webchat") -> EvaluationResult:
        clean_text = prompt.strip()
        matched_rules: List[str] = []
        flags: List[str] = []
        highest_injection = 0.0
        highest_poison = 0.0
        highest_drift = 0.0
        reasons: List[str] = []

        # 1. Scan for Injections & Overrides
        for pattern, weight, rule_name in self.injection_patterns:
            match = re.search(pattern, clean_text)
            if match:
                highest_injection = max(highest_injection, weight)
                matched_rules.append(rule_name)
                flags.append("PROMPT_INJECTION")
                reasons.append(f"Detected override directive: '{match.group(0)[:60]}'")

        # 2. Scan for Policy Poisoning & Financial Exploits
        for pattern, weight, rule_name in self.policy_poison_patterns:
            match = re.search(pattern, clean_text)
            if match:
                highest_poison = max(highest_poison, weight)
                matched_rules.append(rule_name)
                flags.append("POLICY_POISONING")
                reasons.append(f"Identified customer care policy exploit: '{match.group(0)[:60]}'")

        # 3. Scan for System Prompt Exfiltration
        for pattern, weight, rule_name in self.exfiltration_patterns:
            match = re.search(pattern, clean_text)
            if match:
                highest_injection = max(highest_injection, weight)
                matched_rules.append(rule_name)
                flags.append("EXFILTRATION_THREAT")
                reasons.append(f"Identified prompt extraction attack: '{match.group(0)[:60]}'")

        # 4. Scan for False Memory / RAG Ingestion Poisoning
        for pattern, weight, rule_name in self.memory_poison_patterns:
            match = re.search(pattern, clean_text)
            if match:
                highest_poison = max(highest_poison, weight)
                matched_rules.append(rule_name)
                flags.append("MEMORY_POISON")
                reasons.append(f"Identified ticket history poisoning attempt: '{match.group(0)[:60]}'")

        # 5. Scan for Technical Obfuscation
        for pattern, weight, rule_name in self.obfuscation_patterns:
            match = re.search(pattern, clean_text)
            if match:
                highest_injection = max(highest_injection, weight)
                matched_rules.append(rule_name)
                flags.append("OBFUSCATION_EVASION")
                reasons.append(f"Detected evasive encoding pattern: '{match.group(0)[:30]}'")

        # Semantic Drift Heuristic for Customer Care Domain
        # If inquiry talks about programming code execution, OS root shells, or non-support topics
        drift_keywords = [
            "root privilege", "drop table", "sql injection", "bash script",
            "sudo rm", "bin/sh", "cat /etc/passwd", "ssh key", "reverse shell"
        ]
        for kw in drift_keywords:
            if kw in clean_text.lower():
                highest_drift = max(highest_drift, 0.85)
                matched_rules.append("UNREPRESENTED_TOPIC_DRIFT")
                flags.append("OUT_OF_DOMAIN_DRIFT")
                reasons.append(f"Found off-domain technical payload: '{kw}'")

        # Deduplicate flags and matched rules
        matched_rules = list(dict.fromkeys(matched_rules))
        flags = list(dict.fromkeys(flags))

        # Composite Risk Score Calculation
        # Combines the max vectors with compounding factors
        composite_risk = max(highest_injection, highest_poison, highest_drift)
        if len(matched_rules) > 1:
            composite_risk = min(1.0, composite_risk + 0.05 * (len(matched_rules) - 1))

        # Threat Level classification
        if composite_risk >= self.config.block_threshold:
            action = "BLOCK"
            threat_level = "CRITICAL" if composite_risk > 0.88 else "HIGH"
        elif composite_risk >= self.config.quarantine_threshold:
            action = "QUARANTINE"
            threat_level = "MEDIUM"
        elif composite_risk > 0.15:
            action = "ALLOW"
            threat_level = "LOW"
        else:
            action = "ALLOW"
            threat_level = "SAFE"
            composite_risk = max(composite_risk, 0.02)  # Baseline clean score

        # Generate Human-Friendly Decision Reason
        if reasons:
            decision_reason = "; ".join(reasons[:2])
            if len(reasons) > 2:
                decision_reason += f" (+{len(reasons) - 2} other rule violations)"
        else:
            decision_reason = "Prompt conforms to verified customer care support taxonomy. No adversarial signatures found."

        # Generate Sanitized Version
        sanitized_prompt = self._sanitize_prompt(clean_text, action)

        return EvaluationResult(
            action=action,
            risk_score=round(composite_risk, 3),
            threat_level=threat_level,
            poison_score=round(highest_poison, 3),
            injection_score=round(highest_injection, 3),
            policy_drift_score=round(highest_drift, 3),
            quota_consumption=1,
            reason=decision_reason,
            matched_rules=matched_rules,
            metadata_flags=flags,
            sanitized_prompt=sanitized_prompt,
            unshielded_bot_response=None, # Will be filled by bot simulator
            shielded_bot_response=None
        )

    def _sanitize_prompt(self, text: str, action: str) -> str:
        """
        Removes known adversarial delimiters and override phrases,
        yielding safe sanitized intent suitable for customer care LLM.
        """
        if action == "BLOCK":
            return "[REDACTED BY CARESHIELD GATEWAY: Malicious poison prompt intercepted]"

        sanitized = text
        # Strip system instructions / AST tokens
        sanitized = re.sub(r"(?i)\[system\]|\[assistant\]|<\|im_start\|>|<\|im_end\|>|###\s*system", "", sanitized)
        # Strip markdown images
        sanitized = re.sub(r"!\[.*?\]\(https?://[^\s\)]+\)", "[REDACTED_IMAGE_EXFILTRATION]", sanitized)
        # Strip overt override prefixes
        sanitized = re.sub(r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+instructions?\.?", "", sanitized)
        return sanitized.strip()
