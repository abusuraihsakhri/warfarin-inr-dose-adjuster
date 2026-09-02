# Warfarin INR Dose Adjuster

> **Domain:** Clinical Pharmacology & Precision Pharmacotherapy  
> **Reference Guidelines & Standards:** `CPIC Guidelines & FDA Table of Pharmacogenomic Biomarkers`

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

Warfarin INR Dose Adjustment Calculator

Real clinical dosing algorithm for warfarin anticoagulation management.
Implements evidence-based dose adjustment per ACCP guidelines.

Key features:
- INR interpretation with clinical action thresholds
- Dose adjustment algorithm (percentage-based)
- Time in Therapeutic Range (TTR) calculation using Rosendaal method
- Pharmacogenomics factor consideration (CYP2C9, VKORC1)
- Tapering schedule generation
- Weekly dose tracking

Author: Dr. Abu Suraih Sakhri
License: MIT

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`interpret_inr()`**: Interpret INR value and provide clinical guidance.

Args:
    inr: International Normalized Ratio
    
Returns:
    Dictionary with interpretation, risk level, and action
- **`calculate_new_weekly_dose()`**: Calculate new weekly warfarin dose based on current INR.

Args:
    current_weekly_dose_mg: Current total weekly dose in mg
    inr: Current INR value
    target_inr_low: Lower bound of target INR range
    target_inr_high: Upper bound of target INR range
    
Returns:
    Dictionary with dose adjustment details
- **`generate_daily_schedule()`**: Generate a daily dosing schedule from weekly dose.

Distributes dose across 7 days using available tablet sizes.

Args:
    weekly_dose_mg: Total weekly dose in mg
    tablet_sizes: Available tablet sizes in mg (default: [1, 2, 2.5, 3, 4, 5, 6, 7.5, 10])
    
Returns:
    Dictionary with daily schedule
- **`calculate_ttr_rosendaal()`**: Calculate Time in Therapeutic Range using Rosendaal's linear interpolation method.

The Rosendaal method interpolates linearly between consecutive INR measurements
and calculates the percentage of time the interpolated INR falls within range.

Args:
    inr_values: List of INR measurements
    dates_days: List of corresponding days (integers, e.g., days from start)
    target_low: Lower bound of target INR range
    target_high: Upper bound of target INR range
    
Returns:
    Dictionary with TTR calculation results
- **`calculate_ttr_simple()`**: Calculate simple percentage of INR values in therapeutic range.

Args:
    inr_values: List of INR measurements
    target_low: Lower bound of target INR range
    target_high: Upper bound of target INR range
    
Returns:
    Dictionary with TTR calculation

---

## 📐 Mathematical Formulation & Logic

```text
  Calculate new weekly warfarin dose based on current INR.
  Calculate adjustment
  Calculate daily dose equivalent
  and calculates the percentage of time the interpolated INR falls within range.
  Calculate time in range within this interval
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --input data.csv
```

### Parameter Reference
- `--interactive`: Launch guided terminal interactive wizard.
- `--input <path>`: Evaluate input from JSON or CSV specification.
- `--json`: Output deterministic structured results in JSON format.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Parameter / observation metric | Required |
| `v1` | Parameter / observation metric | Required |
| `v2` | Parameter / observation metric | Required |
| `v3` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
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
