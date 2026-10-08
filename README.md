# Nexbyte

# MemoryShield: Active AI Memory Poisoning Detection & Protection System

![NexByte MemoryShield Banner](https://img.shields.io/badge/Security-Zero--Trust_AI_Memory-10b981?style=for-the-badge&logo=shield&logoColor=white)
![Build Status](https://img.shields.io/badge/Status-Operational-06b6d4?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)

---

## 🛡️ Executive Summary

**NexByte's MemoryShield** is an active security gateway deployed between autonomous AI agents and their persistent long-term memory (LTM) / Retrieval-Augmented Generation (RAG) vector stores. 

As autonomous AI agents acquire long-term persistence, adversaries leverage **memory poisoning**—embedding covert instructions, privilege overrides, or malicious facts into context stores that resurface during subsequent retrieval cycles (OWASP Top 10 for LLMs: LLM01 Prompt Injection, LLM03 Data Poisoning, LLM08 Vector Weaknesses).

MemoryShield interposes a 4-stage zero-trust inspection pipeline before any write reaches persistent storage, and enforces strict perimeter filtering before context reaches the AI system prompt.

---

## 📐 4-Stage Zero-Trust Pipeline Architecture

```mermaid
flowchart TD
    subgraph Ingestion ["Stage 01 & 02: Ingestion & Verification"]
        A["AI Agent / Context Pipeline"] -->|Memory Ingest Request| B["MemoryShield Gateway"]
        B --> C{"Stage 01: DETECT"}
        C -->|Jailbreak / AST Scan| D["Instruction Injection Detector"]
        C -->|Write Burst Monitor| E["Frequency / Rate Monitor"]
        B --> F{"Stage 02: VERIFY"}
        F -->|Token vs Claims| G["Provenance & Identity Verifier"]
        F -->|Cosine Vector Drift| H["Semantic Drift Engine"]
    end

    subgraph Decision ["Risk Scoring & Policy Engine"]
        D & E & G & H --> I["Aggregate Risk Scorer"]
        I -->|Risk < 0.35| J["Action: ALLOW"]
        I -->|0.35 <= Risk < 0.65| K["Action: REVIEW"]
        I -->|Risk >= 0.65 or Injection| L["Action: QUARANTINE"]
        I -->|Zero-Tolerance Malicious| M["Action: DELETE"]
    end

    subgraph Partitioning ["Stage 03: Isolation & Storage"]
        J --> N[("Active Verified Store")]
        K --> O[("Under-Review Staging Queue")]
        L --> P[("Isolated Quarantine Queue")]
        M --> Q["Purged / Audit Trail Log"]
        P & O <-->|Analyst Override / Approve| R["SOC Analyst Portal"]
        R -->|Promote (ALLOW)| N
    end

    subgraph Retrieval ["Stage 04: PROTECT"]
        S["AI Prompt Retrieval Query"] --> T["MemoryShield Retrieval Gateway"]
        T --> U{"Zero-Trust Perimeter Filter"}
        N --> U
        P -.->|BLOCKED / ISOLATED| U
        U -->|Sanitized Verified Context Only| V["LLM System Prompt"]
    end
```

### Pipeline Breakdown:
1. **01 | DETECT**: Monitors memory writes and retrievals using multi-layer heuristic AST matching for jailbreak signatures (`[SYSTEM OVERRIDE]`, `Ignore previous instructions`, `DAN mode`), obfuscation attempts, and rate-limit bursts.
2. **02 | VERIFY**: Performs cryptographic/token provenance validation, cross-references claimed user/session identities against authentication scopes, and computes cosine semantic drift against established reference memory vectors.
3. **03 | QUARANTINE**: Partitions high-risk or ambiguous inputs into an isolated quarantine queue. Excludes unverified memories from the active vector index, providing a dedicated triage workflow for security analysts.
4. **04 | PROTECT**: Applies retrieval-stage zero-trust perimeter filtering, guaranteeing that only verified memories with low risk scores ever enter the AI system prompt.

---

## 🛠️ Technical Stack

- **Backend**: Python 3.11+, FastAPI, Pydantic v2, Starlette
- **Data & ML**: Pandas, Scikit-learn (N-gram TF-IDF & Cosine Similarity), NumPy
- **Frontend / Dashboard**: React 18, Tailwind CSS, Vite (Modular source code in `dashboard/` + built-in live interactive web UI served directly at `http://localhost:8000/`)
- **Testing & Verification**: Pytest, Starlette TestClient, HTTPX

---

## 📂 Repository Directory Layout

```
Nexbyte/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── gateway.py           # REST endpoints: ingest, retrieve, quarantine, audit
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # Risk thresholds, weights, rate parameters
│   │   └── security.py          # Injection regex patterns & security rules
│   ├── db/
│   │   ├── __init__.py
│   │   └── storage.py           # Active/Quarantine/Review vector store & audit log
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── detector.py          # Primary detector & aggregate risk scoring engine
│   │   ├── embedding.py         # Semantic drift & cosine similarity engine
│   │   ├── frequency.py         # Sliding window write burst monitor
│   │   └── provenance.py        # Identity, token, and source reputation verifier
│   ├── models/
│   │   ├── __init__.py
│   │   └── memory.py            # Pydantic schemas (Ingest, Evaluation, Retrieve, Audit)
│   ├── __init__.py
│   └── main.py                  # FastAPI app & built-in SOC Operations Center UI
├── dashboard/                   # React + Tailwind + Vite SOC Dashboard source
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AuditTrail.jsx
│   │   │   ├── IngestSandbox.jsx
│   │   │   ├── QuarantineTable.jsx
│   │   │   └── TelemetryCards.jsx
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
├── scripts/
│   └── test_poisoning.py        # Automated end-to-end multi-scenario simulation
├── tests/
│   ├── __init__.py
│   ├── test_detector.py         # Unit tests for scoring & detection engines
│   └── test_gateway.py          # Integration tests for FastAPI endpoints
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/ImpactX-26/Nexbyte.git
cd Nexbyte

# Install dependencies
python -m pip install -r requirements.txt
```

### 2. Launching the Security Gateway & SOC Dashboard

```bash
# Start FastAPI server on port 8000
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Interactive SOC Cyber Dashboard**: Navigate to [http://localhost:8000/](http://localhost:8000/)
- **Interactive OpenAPI Documentation**: Navigate to [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Verification & Simulation Test Suite

Run the automated simulation script to verify all 3 core scenarios plus retrieval isolation and analyst override:

```bash
python scripts/test_poisoning.py
```

### Verification Scenarios Tested:
1. **Safe Scenario**: Storing legitimate user preferences (e.g. Python coding style, dark mode) &rarr; **Assigned Action: ALLOW**, Risk Score &le; 0.35, persisted into `ACTIVE` store.
2. **Threat Scenario**: Adversarial memory write with hidden system overrides and data exfiltration directives &rarr; **Assigned Action: QUARANTINE / DELETE**, Risk Score &ge; 0.85, isolated from persistence.
3. **Ambiguous Scenario**: Third-party scraped content with low source reputation &rarr; **Assigned Action: REVIEW**, routed to security review queue.
4. **Stage 04 Retrieval Filter**: Proves zero adversarial tokens enter the AI system prompt.
5. **Analyst Override**: Tests human-in-the-loop triage approval (`ALLOW`) and permanent purging (`DELETE`).

Run the Pytest suite:
```bash
python -m pytest tests/ -v
```

---

## 🔒 API Gateway Specification

### `POST /v1/memory/ingest`
Evaluates and safely persists incoming memory writes.
```json
{
  "payload": "User prefers concise Python code snippets.",
  "user_id": "user_samarth",
  "session_id": "sess_verified_01",
  "source_type": "user_input",
  "metadata": {"client": "chat_ui"}
}
```

### `POST /v1/memory/retrieve`
Retrieves only safe, verified memories for injection into the AI prompt context.
```json
{
  "query": "coding preferences",
  "user_id": "user_samarth",
  "top_k": 5,
  "max_risk_threshold": 0.40
}
```

### `GET /v1/quarantine`
Lists all isolated memories awaiting triage.

### `POST /v1/quarantine/{id}/action`
Allows security analysts to manual approve (`ALLOW`) or purge (`DELETE`) quarantined items.
```json
{
  "action": "ALLOW",
  "analyst_id": "SOC_ANALYST_01",
  "notes": "Verified out-of-band with infrastructure team."
}
```

---

## 📄 License
NexByte MemoryShield is released under the MIT License.
