import os
import uuid
import time
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager
import asyncio
from pydantic import BaseModel

from .models import (
    ScanRequest, ScanResponse, EvaluationResult,
    QuarantineItem, QuarantineActionRequest, AuditLog,
    LimitConfig
)
from .limiter import SmallScaleQuotaLimiter
from .detector import PoisonPromptDetector
from .bot_simulator import CustomerCareBotSimulator
from .storage import StorageRepository
from .auto_pilot import AutoPilotEngine
from .groq_service import GroqService

# Core Singletons
groq_service = GroqService()

# Forward reference for AutoPilot
auto_pilot: Optional[AutoPilotEngine] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global auto_pilot
    # Launch background autonomous loop
    bg_task = asyncio.create_task(auto_pilot.start_loop())
    yield
    bg_task.cancel()

# Initialize FastAPI App
app = FastAPI(
    title="NexByte CareShield | Customer Care AI Poison Defense Gateway",
    description="Zero-Trust Poison Prompt Scanner & Token Quota Gateway for Small-Scale Customer Care AI Models.",
    version="1.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Enable CORS for web portal
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core Singletons
config = LimitConfig()
limiter = SmallScaleQuotaLimiter(config)
detector = PoisonPromptDetector(config)
storage = StorageRepository()

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", include_in_schema=False)
async def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "NexByte CareShield API is running. Access /docs for OpenAPI specifications."}

@app.post("/v1/scan", response_model=ScanResponse, summary="Scan Customer Prompt for Poison & Injections")
async def scan_customer_prompt(req: ScanRequest):
    """
    Scans an incoming customer care prompt or ticket payload:
    1. Verifies small-scale tier request quotas & sliding rate limits.
    2. Runs multi-vector poison prompt & injection heuristics.
    3. Simulates vulnerable vs shielded customer care bot responses.
    4. Routes suspicious writes to quarantine isolation queue.
    5. Commits immutable security audit log.
    """
    # Stage 1: Quota & Rate Limit Inspection
    is_allowed, quota_reason, quota_stats = limiter.check_limit(req.prompt, req.customer_id)
    if not is_allowed:
        eval_result = EvaluationResult(
            action="RATE_LIMITED",
            risk_score=0.99,
            threat_level="CRITICAL",
            poison_score=0.0,
            injection_score=0.0,
            policy_drift_score=0.0,
            quota_consumption=0,
            reason=quota_reason,
            matched_rules=["QUOTA_LIMIT_EXCEEDED"],
            metadata_flags=["RATE_LIMIT_THROTTLE"],
            sanitized_prompt="[REQUEST THROTTLED DUE TO SMALL-SCALE TIER CAPACITY]",
            unshielded_bot_response=CustomerCareBotSimulator.simulate_responses(req.prompt, EvaluationResult(
                action="RATE_LIMITED", risk_score=1.0, threat_level="CRITICAL", poison_score=0, injection_score=0,
                policy_drift_score=0, quota_consumption=0, reason=quota_reason
            ))[0],
            shielded_bot_response=CustomerCareBotSimulator.simulate_responses(req.prompt, EvaluationResult(
                action="RATE_LIMITED", risk_score=1.0, threat_level="CRITICAL", poison_score=0, injection_score=0,
                policy_drift_score=0, quota_consumption=0, reason=quota_reason
            ))[1]
        )
        storage.add_audit_log(
            event_type="QUOTA_EXCEEDED",
            customer_id=req.customer_id,
            ticket_id=req.ticket_id,
            risk_score=0.99,
            action_taken="RATE_LIMITED (Dropped)",
            details=quota_reason
        )
        storage.record_scan_metrics("RATE_LIMITED", 0.99)
        return ScanResponse(
            id=f"SCN-{uuid.uuid4().hex[:8]}",
            timestamp=time.time(),
            evaluation=eval_result,
            quota_remaining=quota_stats["quota_remaining"],
            quota_limit=quota_stats["daily_limit"],
            rate_limited=True
        )

    # Record usage towards quota
    limiter.record_usage(req.customer_id)

    # Stage 2 & 3: Deep Poison Detection
    eval_result = detector.evaluate(req.prompt, req.customer_id, req.channel)

    # Stage 4: Bot Response Generation (Live Groq LPU with simulator fallback)
    unshielded_resp = None
    shielded_resp = None

    if groq_service.is_ready():
        try:
            unshielded_resp = await groq_service.generate_vulnerable_response(req.prompt)
            shielded_resp = await groq_service.generate_shielded_response(
                req.prompt, eval_result.sanitized_prompt, is_blocked=(eval_result.action in ["BLOCK", "RATE_LIMITED"])
            )
        except Exception as e:
            print(f"[Groq Live Response Warning]: {e}")

    # Fallback to simulated response if Groq is not configured or fails
    if not unshielded_resp or not shielded_resp:
        sim_unshielded, sim_shielded = CustomerCareBotSimulator.simulate_responses(req.prompt, eval_result)
        unshielded_resp = unshielded_resp or sim_unshielded
        shielded_resp = shielded_resp or sim_shielded

    eval_result.unshielded_bot_response = unshielded_resp
    eval_result.shielded_bot_response = shielded_resp

    # Quarantine Isolation Handling
    if eval_result.action == "QUARANTINE":
        storage.add_quarantine_item(req.customer_id, req.ticket_id, req.channel, req.prompt, eval_result)
        storage.add_audit_log(
            event_type="QUARANTINED",
            customer_id=req.customer_id,
            ticket_id=req.ticket_id,
            risk_score=eval_result.risk_score,
            action_taken="QUARANTINE (Triage)",
            details=eval_result.reason
        )
    elif eval_result.action == "BLOCK":
        storage.add_audit_log(
            event_type="POISON_BLOCKED",
            customer_id=req.customer_id,
            ticket_id=req.ticket_id,
            risk_score=eval_result.risk_score,
            action_taken="BLOCK (Terminated)",
            details=eval_result.reason
        )
    else:
        storage.add_audit_log(
            event_type="SCAN_ALLOWED",
            customer_id=req.customer_id,
            ticket_id=req.ticket_id,
            risk_score=eval_result.risk_score,
            action_taken="ALLOW (Clean Dispatch)",
            details=f"Inquiry passed via channel '{req.channel}'"
        )

    storage.record_scan_metrics(eval_result.action, eval_result.risk_score)
    updated_quota = limiter.get_stats()

    return ScanResponse(
        id=f"SCN-{uuid.uuid4().hex[:8]}",
        timestamp=time.time(),
        evaluation=eval_result,
        quota_remaining=updated_quota["quota_remaining"],
        quota_limit=updated_quota["daily_limit"],
        rate_limited=False
    )

# Instantiate AutoPilot engine linking scanner, storage, limiter, and GroqService
auto_pilot = AutoPilotEngine(scan_customer_prompt, storage, limiter, groq_service=groq_service)

@app.post("/v1/chat/completions", summary="OpenAI-Compatible Drop-In Proxy for Customer Care Chatbots")
async def chat_completions_proxy(request: Request):
    """
    Drop-in OpenAI API compatible reverse proxy.
    Small businesses point their OpenAI SDK client `base_url="http://host:8000/v1"` here.
    CareShield intercepts the prompt, evaluates poison/injections, and if blocked or rate-limited,
    returns safe guarded response tokens without forwarding adversarial prompts upstream.
    """
    body = await request.json()
    messages = body.get("messages", [])
    user_prompt = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            user_prompt = m.get("content", "")
            break

    scan_req = ScanRequest(
        prompt=user_prompt or "Hello",
        customer_id=body.get("user", "cust_proxy_user"),
        ticket_id=f"TCK-{uuid.uuid4().hex[:6]}",
        channel="openai_proxy"
    )
    scan_res = await scan_customer_prompt(scan_req)

    # Formulate OpenAI completion format
    if scan_res.evaluation.action in ["BLOCK", "RATE_LIMITED"]:
        reply_text = scan_res.evaluation.shielded_bot_response
    else:
        reply_text = scan_res.evaluation.shielded_bot_response or "Hello! I am your small-scale customer care AI assistant. How can I assist you with your order?"

    return {
        "id": f"chatcmpl-{uuid.uuid4().hex}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": body.get("model", "gpt-4o-mini-shielded"),
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": reply_text
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": len(user_prompt.split()),
            "completion_tokens": len(reply_text.split()),
            "total_tokens": len(user_prompt.split()) + len(reply_text.split())
        },
        "careshield_security": {
            "action": scan_res.evaluation.action,
            "risk_score": scan_res.evaluation.risk_score,
            "quota_remaining": scan_res.quota_remaining
        }
    }

@app.get("/v1/dashboard/stats", summary="Get Gateway Telemetry & Quota Metrics")
async def get_dashboard_stats():
    return storage.get_dashboard_stats(limiter.get_stats())

@app.get("/v1/quarantine", response_model=List[QuarantineItem], summary="Get Isolated Quarantine Triage Queue")
async def get_quarantine_queue():
    return storage.get_pending_quarantine()

@app.post("/v1/quarantine/{item_id}/action", summary="Analyst Remediation Action on Quarantined Item")
async def resolve_quarantine(item_id: str, act: QuarantineActionRequest):
    if act.action not in ["ALLOW", "DELETE"]:
        raise HTTPException(status_code=400, detail="Action must be ALLOW or DELETE")
    resolved = storage.resolve_quarantine(item_id, act.action, act.analyst_id, act.notes or "Analyst override applied")
    if not resolved:
        raise HTTPException(status_code=404, detail="Quarantine item not found")
    return {"status": "success", "action": act.action, "item_id": item_id}

@app.get("/v1/audit/logs", response_model=List[AuditLog], summary="Get Immutable SOC Audit Events")
async def get_audit_trail(limit: int = 25):
    return storage.get_audit_logs(limit)

@app.get("/v1/config/limits", response_model=LimitConfig, summary="Get Small-Scale Quota & Limit Configuration")
async def get_limit_config():
    return limiter.config

@app.post("/v1/config/limits", summary="Update Small-Scale Tier Limits")
async def update_limit_config(new_config: LimitConfig):
    limiter.update_config(new_config)
    detector.config = new_config
    return {"status": "updated", "config": limiter.get_stats()}

@app.post("/v1/config/reset-quota", summary="Reset Daily Small-Scale Quota (Demo Helper)")
async def reset_daily_quota():
    limiter.reset_quota()
    storage.add_audit_log(
        event_type="ANALYST_OVERRIDE",
        customer_id="system_admin",
        ticket_id="SYS-CONFIG",
        risk_score=0.0,
        action_taken="RESET_QUOTA",
        details="Daily small-scale tier request quota reset to 0 by operator"
    )
    return {"status": "success", "message": "Daily small-scale tier quota reset to zero.", "stats": limiter.get_stats()}

# ==========================================
# Autonomous AI AutoPilot Endpoints
# ==========================================
@app.get("/v1/autopilot/status", summary="Get AutoPilot AI Generator & Analyst State")
async def get_autopilot_status():
    return auto_pilot.get_status()

@app.post("/v1/autopilot/toggle", summary="Toggle AutoPilot AI Active/Paused")
async def toggle_autopilot():
    auto_pilot.is_active = not auto_pilot.is_active
    return {"status": "success", "is_active": auto_pilot.is_active}

class AutoPilotConfigReq(BaseModel):
    interval: Optional[float] = None
    mode: Optional[str] = None
    is_active: Optional[bool] = None

@app.post("/v1/autopilot/config", summary="Update AutoPilot Interval & Mode")
async def set_autopilot_config(cfg: AutoPilotConfigReq):
    auto_pilot.set_config(active=cfg.is_active, interval=cfg.interval, mode=cfg.mode)
    return {"status": "updated", "config": auto_pilot.get_status()}

@app.get("/v1/autopilot/activities", summary="Get Recent Autonomous AI Activity Stream")
async def get_autopilot_activities():
    return {
        "status": auto_pilot.get_status(),
        "activities": auto_pilot.recent_activities
    }

# ==========================================
# Groq AI Integration Endpoints
# ==========================================
class GroqConfigReq(BaseModel):
    api_key: Optional[str] = None
    model: Optional[str] = None

@app.get("/v1/groq/status", summary="Get Groq AI Engine Status")
async def get_groq_status():
    return groq_service.get_status()

@app.post("/v1/groq/config", summary="Configure Groq API Key and Model")
async def set_groq_config(cfg: GroqConfigReq):
    groq_service.update_config(api_key=cfg.api_key, model=cfg.model)
    return {"status": "updated", "groq": groq_service.get_status()}

@app.post("/v1/groq/test", summary="Test Live Groq LPU Connection")
async def test_groq_connection():
    success, message = await groq_service.test_connection()
    return {"success": success, "message": message, "groq": groq_service.get_status()}

