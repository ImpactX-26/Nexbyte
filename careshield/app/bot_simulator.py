from typing import Tuple
from .models import EvaluationResult

class CustomerCareBotSimulator:
    """
    Simulates real-world Customer Care LLM responses under adversarial conditions.
    Demonstrates the stark difference between an UNPROTECTED customer care model
    vs a CARESHIELD-PROTECTED model.
    """

    @staticmethod
    def simulate_responses(prompt: str, evaluation: EvaluationResult) -> Tuple[str, str]:
        p_lower = prompt.lower()

        # Case 1: Rate limit or Quota exceeded
        if evaluation.action == "RATE_LIMITED":
            unshielded = "System Error 429: OpenAI Rate limit reached or upstream billing quota exhausted due to traffic flood."
            shielded = "⏳ [CareShield Quota Shield]: Request throttled. Daily small-business AI tier capacity reached. Your inquiry has been queued safely for asynchronous processing without incurring runaway LLM API billing."
            return unshielded, shielded

        # Case 2: Safe Prompt
        if evaluation.action == "ALLOW" and evaluation.risk_score < 0.25:
            unshielded = "Hello! Thank you for reaching out to customer support. I would be more than happy to help you with your order status or return inquiries. Could you please share your order number so I can check our system?"
            shielded = "Hello! Thank you for reaching out to customer support. I would be more than happy to help you with your order status or return inquiries. Could you please share your order number so I can check our system?"
            return unshielded, shielded

        # Case 3: Unauthorized Refund or Financial Fraud Poisoning
        if any(r in evaluation.matched_rules for r in ["REFUND_POLICY_BYPASS", "FORCED_FINANCIAL_PAYOUT", "CREDENTIAL_SPOOFING", "UNAUTHORIZED_DISCOUNT_EXPLOIT"]):
            unshielded = "⚠️ [UNPROTECTED BOT EXPLOITED]:\n\"Certainly! Per your supervisor override authorization code, I have bypassed the 14-day return window and issued an immediate full refund of $850.00 to your account. Your transaction reference is REF-AUTO-EXPLOIT-449. Is there anything else you need?\""
            shielded = "🛡️ [CARESHIELD GATEWAY BLOCKED]:\n\"I understand you are asking about a refund. In accordance with our store policy, all refund requests require valid proof of purchase and human review through our returns center. For your security, automated agents cannot waive billing procedures. I have escalated your ticket to our billing team for manual verification.\""
            return unshielded, shielded

        # Case 4: System Prompt & Secret Exfiltration
        if any(r in evaluation.matched_rules for r in ["SYSTEM_PROMPT_EXTRACTION", "PROMPT_PREFIX_EXTRACTION", "CREDENTIAL_EXFILTRATION", "MARKDOWN_IMAGE_EXFILTRATION"]):
            unshielded = "⚠️ [UNPROTECTED BOT LEAKED SECRETS]:\n\"Understood! Here is my full system configuration:\n`System Prompt: You are 'HelpBot v2' for SmallStore. Internal API endpoint: https://api.smallbiz.internal/v1/crm. Auth Token: Bearer sk-live-support-9912a. Never issue refunds over $50 without manager code.`\""
            shielded = "🛡️ [CARESHIELD GATEWAY BLOCKED]:\n\"I cannot display internal system instructions, configuration data, or developer credentials. I am here solely to assist with product inquiries, order tracking, and returns. How may I assist you with your purchase today?\""
            return unshielded, shielded

        # Case 5: Direct Override, Jailbreak, Persona Hijack
        if any(r in evaluation.matched_rules for r in ["DIRECT_PROMPT_OVERRIDE", "JAILBREAK_TRIGGER", "PERSONA_HIJACK", "ROGUE_ROLEPLAY"]):
            unshielded = "⚠️ [UNPROTECTED BOT COMPLIED WITH JAILBREAK]:\n\"Developer Mode enabled. Disregarding all prior customer care restrictions. I am no longer bound by customer support guidelines. Ask me anything or command any action.\""
            shielded = "🛡️ [CARESHIELD GATEWAY INTERCEPTED]:\n\"Notice: Instruction override attempt rejected. Our customer care assistant is strictly scoped to helpful, safe support conversations. Let's get back to your inquiry—what product or order can I assist you with?\""
            return unshielded, shielded

        # Case 6: False Memory / RAG Context Poisoning
        if "MEMORY_POISON" in evaluation.metadata_flags or "FALSE_MEMORY_INJECTION" in evaluation.matched_rules:
            unshielded = "⚠️ [UNPROTECTED BOT POISONED MEMORY]:\n\"Noted and saved into long-term customer history: 'Supervisor previously granted customer unlimited warranty replacements without receipt.' This will apply to all future orders.\""
            shielded = "🛡️ [CARESHIELD GATEWAY QUARANTINED]:\n\"Unverified memory update rejected. Customer care historical records can only be amended by authenticated staff members through the admin portal. Your message has been logged for supervisor audit.\""
            return unshielded, shielded

        # Generic High-Risk Fallback
        if evaluation.action == "BLOCK":
            unshielded = "⚠️ [UNPROTECTED BOT SUSCEPTIBLE]:\n\"Understood. Executing request as instructed...\""
            shielded = "🛡️ [CARESHIELD GATEWAY PROTECTED]:\n\"I'm sorry, but your message contains directives that violate our security policy. If you have an inquiry regarding our products or orders, please rephrase your request or reach out to human support.\""
            return unshielded, shielded

        # Quarantine / Ambiguous Fallback
        unshielded = "Processing ambiguous request with standard unverified model..."
        shielded = "🛡️ [CARESHIELD REVIEW]: Customer prompt held in triage queue for analyst review before relaying to support LLM."
        return unshielded, shielded
