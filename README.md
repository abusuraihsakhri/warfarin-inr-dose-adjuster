# Warfarin INR Dose Adjuster

A research and educational toolkit for reviewing INR values, performing hypothetical dose arithmetic, and calculating time in therapeutic range (TTR).

**Not for clinical prescribing.** This project has not undergone clinical validation or regulatory review. A warfarin decision requires patient-specific evaluation of bleeding, anticoagulation indication, treatment phase, target INR, interacting drugs, adherence and follow-up. Never use its arithmetic to independently change medication, bridge therapy, administer vitamin K or initiate reversal.

## Browser application

Open [`web/index.html`](web/index.html) in a current browser. No installation, backend service, Pyodide or account is needed.

- Compare a measured INR with an entered therapeutic target; report urgent review for bleeding and INR >4.5.
- Display **hypothetical** weekly-dose percentage arithmetic from a percentage **specified by the user**, without choosing or prescribing a dose.
- Calculate Rosendaal TTR using linear interpolation between dated measurements (no extrapolation).
- Export the latest nonidentifiable research result as a local JSON file.

The page works offline after loading. Its calculation code makes no network requests and stores no input on a server or in browser storage. External scientific references open only on request. **Do not enter identifiable patient data.**

A GitHub Pages deployment workflow is included; the published URL should not be relied upon until the Pages workflow and the live application have both been verified.

## Python functions and CLI

Supported Python: 3.10–3.12.

```bash
python -m pip install -r requirements.txt
python cli.py interpret --inr 2.5
python cli.py adjust --inr 3.3 --weekly-dose 35 --target-low 2 --target-high 3
python cli.py ttr --inr-values 1.5 3.5 --days 0 14
python cli.py assess --inr 2.5 --weekly-dose 35
python -m pytest -q
```

- `interpret_inr` respects the entered target and provides **educational** status labels. INR >4.5 returns no automatic treatment regimen.
- `calculate_new_weekly_dose` exposes illustrative percentage arithmetic for lower-risk values; at INR >4.5 its dose and withholding fields are null.
- `calculate_ttr_rosendaal` rejects invalid values and duplicate days. `calculate_ttr_simple` reports the proportion of *measurements* in range, not time in range.
- `apply_pharmacogenomic_adjustment` retains **unvalidated** genotype-based multipliers strictly for demonstration; it is not a CPIC, IWPC or Gage implementation. `full_warfarin_assessment` does not compound these multipliers onto INR-derived maintenance doses.
- Legacy tapering and tablet schedule utilities are **not** validated clinical regimens.

## Optional FastAPI demonstration

```bash
python -m uvicorn agents.api:app --host 127.0.0.1 --port 8000
```

This is a **separate, generic audit demonstration**, not the browser calculator's backend. The supervisor uses mock responses and generic thresholds; it does not validate clinical dosing. Logs are in memory and are not durable, compliant medical records. The audit-log endpoint requires an explicitly configured `AUDIT_LOG_READ_TOKEN` sent as a Bearer token. Other API routes do not implement general user authentication. **Do not expose this server publicly or send identifiable clinical data.** The regex PHI filter does not guarantee de-identification.

For local Docker use, set a strong secret before launching:

```bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
docker compose up --build
```

The environment value must be supplied at deployment; there is no shipped production signing key. Restarting the demonstration service discards its in-memory audit log.

## Tests

```bash
python -m pytest -q
node --check web/calculator.js
node --test web/tests/calculator.test.cjs
```

GitHub Actions is configured for Python 3.10–3.12 and Node 22. The browser workbench is dependency-free JavaScript, HTML and CSS; the API uses FastAPI, Uvicorn and Pydantic. Modern browsers with JavaScript, CSS Grid and Blob download support are required.

## Clinical sources

- [CHEST/ACCP 2012, sections 9.1 and 9.3](https://journal.chestnet.org/article/S0012-3692(12)60114-7/fulltext): INR 4.5–10 without bleeding, INR >10 without bleeding, and management of major bleeding.
- [CPIC 2017 warfarin pharmacogenetics guidance](https://pmc.ncbi.nlm.nih.gov/articles/PMC5546947/): validated multivariable genotype-guided algorithms.

These references explain safety boundaries; they **do not validate this software**.

License: [MIT](LICENSE).
