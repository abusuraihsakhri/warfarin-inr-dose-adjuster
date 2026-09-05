# Warfarin INR Dose Adjuster

> **Domain:** Clinical Pharmacology & Precision Pharmacotherapy  
> **Reference Guidelines & Standards:** ACCP Guidelines, CPIC Guidelines & FDA Table of Pharmacogenomic Biomarkers

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

Warfarin INR Dose Adjustment Calculator implementing evidence-based dose adjustment per ACCP guidelines.

Key features:
- INR interpretation with clinical action thresholds
- Dose adjustment algorithm (percentage-based)
- Time in Therapeutic Range (TTR) calculation using Rosendaal method
- Pharmacogenomics factor consideration (CYP2C9, VKORC1)
- Tapering schedule generation
- Weekly dose tracking
- CLI interface for all operations
- FastAPI REST API with audit trail

Author: Dr. Abu Suraih Sakhri
License: MIT

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`interpret_inr()`**: Interpret INR value and provide clinical guidance.
- **`calculate_new_weekly_dose()`**: Calculate new weekly warfarin dose based on current INR.
- **`generate_daily_schedule()`**: Generate a daily dosing schedule from weekly dose.
- **`calculate_ttr_rosendaal()`**: Calculate Time in Therapeutic Range using Rosendaal's linear interpolation method.
- **`calculate_ttr_simple()`**: Calculate simple percentage of INR values in therapeutic range.
- **`apply_pharmacogenomic_adjustment()`**: Apply CYP2C9/VKORC1-based dose adjustments.
- **`generate_taper_schedule()`**: Generate a gradual tapering schedule for dose reduction.
- **`full_warfarin_assessment()`**: Complete warfarin dosing assessment combining all modules.

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/warfarin-inr-dose-adjuster.git
cd warfarin-inr-dose-adjuster

# Install dependencies
pip install -r requirements.txt
```

---

## 💻 CLI Quickstart & Usage

### 1. Interpret INR Value
```bash
python cli.py interpret --inr 2.5
```

### 2. Calculate Dose Adjustment
```bash
python cli.py adjust --inr 3.3 --weekly-dose 35
```

### 3. Calculate Time in Therapeutic Range
```bash
# Simple method
python cli.py ttr --inr-values 2.1 2.5 2.8 2.3 2.7

# Rosendaal method (with days)
python cli.py ttr --inr-values 2.0 3.0 --days 0 14
```

### 4. Pharmacogenomic Adjustment
```bash
python cli.py pgx --dose 35 --cyp2c9 poor --vkorc1 sensitive
```

### 5. Generate Tapering Schedule
```bash
python cli.py taper --current-dose 50 --target-dose 30
```

### 6. Full Assessment
```bash
python cli.py assess --inr 2.5 --weekly-dose 35 --cyp2c9 normal --vkorc1 normal
```

### 7. Run Supervisor Audit
```bash
python cli.py audit --task-id TASK-001 --primary 12.0 --secondary 4.0
```

### 8. Query Supervisory Chat
```bash
python cli.py chat "Explain warfarin dosing"
```

### 9. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances, Claude, GPT-4o, and deterministic test mocks.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t warfarin-inr-dose-adjuster .
docker run -p 8000:8000 warfarin-inr-dose-adjuster
```

Or using docker-compose:

```bash
docker-compose up -d
```

---

## 📁 Project Structure

```
warfarin-inr-dose-adjuster/
├── warfarin_titration.py      # Core algorithm & CLI entry point
├── cli.py                     # CLI wrapper
├── enrichment.py              # Enrichment engine modules
├── simulator.py               # High-throughput simulation
├── agents/                    # Enterprise agent framework
│   ├── base.py               # PHI guard, audit trail, security
│   ├── models.py             # Pydantic data models
│   ├── supervisor.py         # Multi-agent supervisor
│   ├── workers.py            # Specialized domain workers
│   ├── api.py                # FastAPI REST endpoints
│   ├── metrics.py            # Prometheus metrics
│   ├── llm_factory.py        # LLM provider factory
│   ├── learning.py           # Active learning calibration
│   └── streamer.py           # WebSocket telemetry
├── tests/                     # Test suite
├── web/                       # Operations console (HTML)
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container build
├── docker-compose.yml         # Container orchestration
└── benchmark_dataset.json     # Golden benchmark test cases
```

---

## ⚠️ Disclaimer

**FOR EDUCATIONAL/RESEARCH USE ONLY.** This tool is not a substitute for clinical pharmacist review or professional medical judgment. Always verify dosing decisions with qualified healthcare professionals.
