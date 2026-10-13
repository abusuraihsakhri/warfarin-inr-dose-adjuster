# Warfarin INR Dose Adjuster

A research and teaching toolkit for warfarin INR range review, hypothetical weekly-dose arithmetic, and time in therapeutic range (TTR) calculation.

**For research/education only. Not a validated clinical decision-support device or a prescribing protocol.** INR interpretation requires bleeding assessment, indication, target range, adherence, concomitant medication review and clinician judgment. Do not use outputs to prescribe, withhold medication, bridge anticoagulation or administer vitamin K.

## Browser workbench

Open `web/index.html` in a current desktop or mobile browser. No build, server, Python, Pyodide or account is needed. The interface provides:

- INR assessment relative to a **user-defined** therapeutic target, with escalation messages for reported bleeding and INR above 4.5.
- Hypothetical weekly/daily dose arithmetic from a **percentage entered by the user**. It does not choose an adjustment or issue dosing instructions.
- Rosendaal interpolated TTR from pairs of measurement day and INR, without extrapolating beyond recorded observations.
- Local export of the latest result as JSON.

The browser implementation performs no network requests, does not persist measurements, and does not ask for identifiers. Do not enter identifiable patient information. External references and GitHub links open only if explicitly selected.

**GitHub Pages:** The repository has Pages metadata, but public deployment must be separately verified; do not rely on the repository homepage until it has been checked. Source: [browser workbench](web/index.html).

## Python CLI

Python 3.10–3.12:

```bash
python -m pip install -r requirements.txt
python cli.py interpret --inr 2.5
python cli.py adjust --inr 3.3 --weekly-dose 35 --target-low 2 --target-high 3
python cli.py ttr --inr-values 1.5 3.5 --days 0 14
python cli.py pgx --dose 35 --cyp2c9 normal --vkorc1 normal
python cli.py assess --inr 2.5 --weekly-dose 35
python -m pytest -q
```

`interpret_inr` and `calculate_new_weekly_dose` are **illustrative**, not patient-specific instructions. At INR > 4.5, the calculator deliberately returns no automatic dose, dose hold, or vitamin K order. If bleeding is present, follow the appropriate urgent management pathway independently of this tool.

`calculate_ttr_rosendaal` interpolates between recorded INR values and rejects duplicate days or nonfinite measurements. Single-measurement percentages computed by `calculate_ttr_simple` are *not* a Rosendaal time estimate.

`apply_pharmacogenomic_adjustment` contains **unvalidated sensitivity multipliers for research illustration only**, not CPIC/IWPC/Gage genotype dosing. The combined assessment does not automatically apply these multipliers to an INR-titrated maintenance dose. The legacy tapering and daily-tablet helpers are not validated for use as clinical regimens.

## Optional backend

The repository also includes a FastAPI demonstration supervisor and generic audit service (not a medical dosing API):

```bash
python cli.py serve
```

**Note:** The legacy CLI does not implement `serve`; run the server directly instead:

```bash
python -m uvicorn agents.api:app --host 127.0.0.1 --port 8000
```

Docker:

```bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
docker compose up --build
```

Audit records are in-memory, not a durable compliant clinical record. `GET /api/audit/logs` is disabled unless `AUDIT_LOG_READ_TOKEN` is configured and provided as `Authorization: Bearer <token>`. This demonstration server has no general user authentication and must **not** be exposed publicly or used for identifiable patient information. The heuristic PHI filter cannot guarantee de-identification.

## Test and implementation notes

```bash
python -m pytest -q
node --check web/calculator.js
node --test web/tests/calculator.test.cjs
```

The browser code uses dependency-free JavaScript. The backend uses Python, FastAPI, Uvicorn and Pydantic. The GitHub Actions pipeline tests Python 3.10–3.12 and Node 22. Current browsers supporting standard JavaScript, Blob downloads and CSS Grid should work. MIT license: [LICENSE](LICENSE).

## Clinical references

- CHEST/ACCP antithrombotic guideline (2012), section 9: INR 4.5–10 without bleeding and INR >10 without bleeding. <https://journal.chestnet.org/article/S0012-3692(12)60114-7/fulltext>
- CPIC guideline for pharmacogenetics-guided warfarin dosing (2017): published validated multivariable algorithms, rather than simple genotype multipliers. <https://pmc.ncbi.nlm.nih.gov/articles/PMC5546947/>

**Validation status:** Automated regression tests do not establish clinical validation, medical regulatory approval or patient safety.
