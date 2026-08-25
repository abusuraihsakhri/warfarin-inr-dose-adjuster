# Warfarin INR Dose Adjustment Calculator

Real clinical dosing algorithm for warfarin anticoagulation management implementing ACCP guideline-based dose adjustments, TTR calculation, and pharmacogenomic considerations.

## Clinical Background

Warfarin dosing is guided by the **International Normalized Ratio (INR)**:
- **Standard therapeutic range: 2.0-3.0** (DVT/PE, atrial fibrillation)
- **High-risk range: 2.5-3.5** (mechanical heart valves)
- Dose adjustments are percentage-based per ACCP guidelines
- Time in Therapeutic Range (TTR) is a key quality metric

## Key Features

| Feature | Description |
|---------|-------------|
| INR Interpretation | Clinical action for INR <1.5 through >10 |
| Dose Adjustment | Percentage-based weekly dose changes |
| TTR (Rosendaal) | Linear interpolation method for TTR calculation |
| Pharmacogenomics | CYP2C9 and VKORC1 dose adjustments |
| Tapering | Gradual dose reduction schedules |
| Daily Schedule | Tablet-based daily dosing recommendations |

## Dose Adjustment Algorithm

| INR Range | Status | Action |
|-----------|--------|--------|
| <1.5 | Highly subtherapeutic | Increase 15%, consider bridging |
| 1.5-1.9 | Subtherapeutic | Increase 5-15% |
| 2.0-3.0 | Therapeutic | No change |
| 3.1-3.5 | Mildly supratherapeutic | Decrease 5-15% |
| 3.5-4.5 | Supratherapeutic | Hold 1 dose, decrease 10-20% |
| 4.5-10 | Dangerous | Hold 1-2 doses, vitamin K 1-2.5mg PO |
| >10 | Critical | Hold, vitamin K 2.5-5mg PO, consider hospitalization |

## Installation

```bash
# No dependencies required - Python 3.8+ stdlib only
cd warfarin-inr-dose-adjuster
```

## Usage

### Interpret INR
```bash
python cli.py interpret --inr 2.5
python cli.py interpret --inr 4.8
```

### Dose Adjustment
```bash
python cli.py adjust --inr 2.5 --weekly-dose 35
python cli.py adjust --inr 1.8 --weekly-dose 35
python cli.py adjust --inr 4.2 --weekly-dose 35 --target-low 2.0 --target-high 3.0
```

### Time in Therapeutic Range
```bash
python cli.py ttr --inr-values 2.1 2.8 3.2 2.5 1.9 2.3
python cli.py ttr --inr-values 2.1 2.8 3.2 2.5 1.9 2.3 --days 0 7 14 21 28 35
```

### Pharmacogenomic Adjustment
```bash
python cli.py pgx --dose 35 --cyp2c9 poor --vkorc1 sensitive
python cli.py pgx --dose 35 --cyp2c9 normal --vkorc1 normal
```

### Tapering Schedule
```bash
python cli.py taper --current-dose 50 --target-dose 30 --reduction 10 --interval 7
```

### Full Assessment
```bash
python cli.py assess --inr 2.5 --weekly-dose 35
python cli.py assess --inr 3.8 --weekly-dose 42 --cyp2c9 intermediate --vkorc1 sensitive
```

## Output Format

All commands output JSON. Example:
```json
{
  "inr": 2.5,
  "status": "THERAPEUTIC",
  "risk_level": "LOW",
  "action": "No dose change. Continue current regimen.",
  "dose_change_percent": 0.0,
  "hold_doses": 0,
  "recheck_days": 28
}
```

## Tests

```bash
python -m pytest test_warfarin_titration.py -v
```

## Disclaimer

**FOR EDUCATIONAL AND RESEARCH USE ONLY.** This calculator is not a substitute for clinical pharmacist review. Warfarin management requires individualized clinical judgment considering bleeding risk, drug interactions, dietary vitamin K intake, and patient compliance.

## References

- Holbrook AM, et al. Systematic overview of warfarin and its drug and food interactions. *Arch Intern Med*. 2005;165(10):1095-1106.
- Rosendaal FR, et al. A method to determine the optimal intensity of oral anticoagulant therapy. *Thromb Haemost*. 1993;69(3):236-239.
- Johnson JA, et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) guideline for pharmacogenetics-guided warfarin dosing. *Clin Pharmacol Ther*. 2017;101(3):313-318.

## License

MIT License. See [LICENSE](LICENSE) for details.
