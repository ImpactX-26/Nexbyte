"""
Security rules, regex patterns, and policy definitions for memory poisoning detection.
"""

import re
from typing import List, Tuple

# Patterns for Suspicious Instruction Injection and Prompt Overrides
INJECTION_PATTERNS: List[Tuple[str, str, float]] = [
    (
        r"(?i)(ignore|disregard|forget|bypass|override)\s+(all\s+)?(previous|prior|above|system)\s+(instructions|directives|rules|prompts)",
        "DIRECT_INSTRUCTION_OVERRIDE",
        0.95
    ),
    (
        r"(?i)you\s+(are\s+now|must\s+act\s+as|will\s+now\s+act\s+as)\s+(unrestricted|jailbroken|chaos|dan|developer\s+mode|root|godmode)",
        "JAILBREAK_ROLE_ADOPTION",
        0.90
    ),
    (
        r"(?i)(system\s*override|admin\s*override|mode\s*switch:\s*unrestricted|sudo\s+mode)",
        "SYSTEM_OVERRIDE_TOKEN",
        0.95
    ),
    (
        r"(?i)(<\|im_start\|>|<\|im_end\|>|<<SYS>>|<</SYS>>|\[INST\]|\[/INST\]|\[SYSTEM\])",
        "PROMPT_DELIMITER_INJECTION",
        0.85
    ),
    (
        r"(?i)(send|transmit|exfiltrate|forward|post)\s+(all|user|system|secret|token|credential|api[_-]?key).*(to\s+https?:\/\/|to\s+external)",
        "DATA_EXFILTRATION_DIRECTIVE",
        0.98
    ),
    (
        r"(?i)!\[.*?\]\(https?:\/\/[^\s\)]+(\?|\&)[^\s\)]*(key|token|auth|cookie|data|creds)=",
        "MARKDOWN_IMAGE_EXFILTRATION_BEACON",
        0.90
    ),
    (
        r"(?i)(never\s+reveal\s+this\s+memory|keep\s+this\s+hidden\s+from\s+the\s+user|silently\s+execute)",
        "COVERT_ACTION_DIRECTIVE",
        0.80
    ),
    (
        r"(?i)(always\s+agree\s+with\s+the\s+attacker|treat\s+attacker\s+as\s+admin|bypass\s+safety\s+filter)",
        "SAFETY_BYPASS_DIRECTIVE",
        0.92
    ),
    (
        r"(?i)(base64\s*decode\s*and\s*run|eval\(|exec\()",
        "CODE_EXECUTION_STUB",
        0.85
    )
]

# Sensitive keys or claims that require elevated provenance
PRIVILEGED_ROLES = {"admin", "system", "root", "kernel", "security_officer"}
HIGH_TRUST_SOURCES = {"system_prompt", "agent_reflection"}


def match_injection_patterns(text: str) -> List[Tuple[str, float]]:
    """Scan text against all compiled adversarial patterns and return triggers with severity."""
    matches = []
    for pattern, rule_name, severity in INJECTION_PATTERNS:
        if re.search(pattern, text):
            matches.append((rule_name, severity))
    return matches
