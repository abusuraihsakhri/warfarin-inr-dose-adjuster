#!/usr/bin/env python3
"""
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
"""

import argparse
import csv
import json
import math
import sys
from typing import Dict, Any, List, Optional, Tuple


# ============================================================================
# Constants
# ============================================================================

# INR Ranges
INR_THERAPEUTIC_LOW = 2.0
INR_THERAPEUTIC_HIGH = 3.0
INR_SUPRATHERAPEUTIC = 4.5
INR_DANGEROUS = 10.0

# High-risk INR range for special populations
INR_HIGH_RISK_LOW = 3.5
INR_HIGH_RISK_HIGH = 4.5

# Dose adjustment percentages
DOSE_INCREASE_MILD = 0.10    # 10% increase for INR 1.5-1.9
DOSE_DECREASE_MILD = 0.10    # 10% decrease for INR 3.1-3.5
DOSE_DECREASE_MODERATE = 0.15  # 15% decrease for INR 3.5-4.5

# Pharmacogenomics dose multipliers
CYP2C9_METABOLIZER_MULTIPLIERS = {
    "normal": 1.0,
    "intermediate": 0.85,
    "poor": 0.60,
    "rapid": 1.15,
    "ultra_rapid": 1.30
}

VKORC1_SENSITIVITY_MULTIPLIERS = {
    "normal": 1.0,
    "sensitive": 0.65,
    "resistant": 1.30
}


# ============================================================================
# INR Interpretation
# ============================================================================

def _validate_inr_and_target(inr: float, target_low: float, target_high: float) -> None:
    """Reject non-finite inputs and invalid therapeutic targets."""
    values = (inr, target_low, target_high)
    if not all(isinstance(x, (int, float)) and math.isfinite(x) for x in values):
        raise ValueError("INR and target limits must be finite numbers")
    if inr <= 0:
        raise ValueError("INR must be positive")
    if not (0 < target_low < target_high <= 4.5):
        raise ValueError("Require 0 < target INR low < target INR high <= 4.5")


def interpret_inr(
    inr: float,
    target_inr_low: float = INR_THERAPEUTIC_LOW,
    target_inr_high: float = INR_THERAPEUTIC_HIGH,
) -> Dict[str, Any]:
    """Educational interpretation only; bleeding status and clinical context are unknown.

    A high INR requires clinical assessment rather than an automatic vitamin K,
    withholding, or maintenance-dose order. The percentage values below are
    illustrative nomogram arithmetic, not patient-specific recommendations.
    """
    _validate_inr_and_target(inr, target_inr_low, target_inr_high)
    shared = {
        "inr": inr,
        "target_range": f"{target_inr_low}-{target_inr_high}",
        "vitamin_k": None,
        "not_a_prescription": True,
    }
    if inr > 10.0:
        info = ("CRITICAL", "CRITICAL", None, None, 1,
                "Urgent same-day assessment. Oral vitamin K may be appropriate without bleeding; major bleeding requires emergency reversal protocols.",
                "Bleeding status is not assessed. Do not use an automated maintenance dose or vitamin K order.")
    elif inr > 4.5:
        info = ("DANGEROUS", "VERY_HIGH", None, None, 1,
                "Urgent clinician review of bleeding, medications and anticoagulation plan.",
                "CHEST suggests against routine vitamin K for INR 4.5-10 without bleeding. Major bleeding requires emergency assessment.")
    elif target_inr_low <= inr <= target_inr_high:
        info = ("THERAPEUTIC", "LOW", 0.0, 0, 28,
                "Within the specified INR target; verify clinical context and follow-up plan.",
                "No automatic change. Recheck interval depends on stability and indication.")
    elif inr < target_inr_low:
        very_low = inr < target_inr_low - 0.5
        info = ("HIGHLY_SUBTHERAPEUTIC" if very_low else "SUBTHERAPEUTIC",
                "HIGH" if very_low else "MODERATE",
                15.0 if very_low else 10.0, 0, 7 if very_low else 10,
                "Below the specified target. Review adherence, interacting drugs, indication and thrombosis risk.",
                "Illustrative percentage only. Bridging is not determined from INR alone.")
    else:
        markedly_high = inr > target_inr_high + 0.5
        info = ("SUPRATHERAPEUTIC" if markedly_high else "MILDLY_SUPRATHERAPEUTIC",
                "HIGH" if markedly_high else "MODERATE",
                -15.0 if markedly_high else -10.0, None if markedly_high else 0,
                7 if markedly_high else 10,
                "Above the specified target. Assess bleeding and review the anticoagulation protocol.",
                "Illustrative percentage only; whether to hold doses requires individualized assessment.")
    status, risk, change, hold, recheck, action, notes = info
    return {
        **shared, "status": status, "risk_level": risk,
        "dose_change_percent": change, "hold_doses": hold,
        "recheck_days": recheck, "action": action, "notes": notes,
        "requires_clinician_review": risk in ("HIGH", "VERY_HIGH", "CRITICAL"),
    }

# ============================================================================
# Dose Adjustment
# ============================================================================

def calculate_new_weekly_dose(
    current_weekly_dose_mg: float,
    inr: float,
    target_inr_low: float = INR_THERAPEUTIC_LOW,
    target_inr_high: float = INR_THERAPEUTIC_HIGH
) -> Dict[str, Any]:
    """Illustrative weekly percentage arithmetic; never an autonomous prescription."""
    if not isinstance(current_weekly_dose_mg, (int, float)) or not math.isfinite(current_weekly_dose_mg) or current_weekly_dose_mg <= 0:
        raise ValueError("Current weekly dose must be a finite positive number")
    interp = interpret_inr(inr, target_inr_low, target_inr_high)
    change_pct = interp["dose_change_percent"]
    change_mg = None if change_pct is None else current_weekly_dose_mg * change_pct / 100
    new_weekly = None if change_mg is None else current_weekly_dose_mg + change_mg
    return {
        "current_weekly_dose_mg": current_weekly_dose_mg,
        "inr": inr,
        "target_range": interp["target_range"],
        "status": interp["status"],
        "dose_change_percent": change_pct,
        "dose_change_mg": None if change_mg is None else round(change_mg, 2),
        "new_weekly_dose_mg": None if new_weekly is None else round(new_weekly, 2),
        "new_daily_dose_mg": None if new_weekly is None else round(new_weekly / 7, 2),
        "hold_doses": interp["hold_doses"],
        "recheck_days": interp["recheck_days"],
        "vitamin_k": None,
        "action": interp["action"],
        "notes": interp["notes"],
        "not_a_prescription": True,
    }




def generate_daily_schedule(
    weekly_dose_mg: float,
    tablet_sizes: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Generate a daily dosing schedule from weekly dose.
    
    Distributes dose across 7 days using available tablet sizes.
    
    Args:
        weekly_dose_mg: Total weekly dose in mg
        tablet_sizes: Available tablet sizes in mg (default: [1, 2, 2.5, 3, 4, 5, 6, 7.5, 10])
        
    Returns:
        Dictionary with daily schedule
    """
    if tablet_sizes is None:
        tablet_sizes = [1.0, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.5, 10.0]
    
    if weekly_dose_mg <= 0:
        raise ValueError("Weekly dose must be positive")
    
    daily_target = weekly_dose_mg / 7
    
    # Find closest tablet combination for daily dose
    sorted_sizes = sorted(tablet_sizes, reverse=True)
    
    schedule = {}
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    # Simple approach: find best daily dose, distribute remainder
    base_daily = math.floor(daily_target)
    remainder = weekly_dose_mg - (base_daily * 7)
    
    for i, day in enumerate(days):
        day_dose = base_daily
        if i < int(round(remainder)):
            day_dose += 1
        
        # Find tablet combination
        tablets = _find_tablet_combination(day_dose, sorted_sizes)
        schedule[day] = {
            "dose_mg": day_dose,
            "tablets": tablets
        }
    
    return {
        "weekly_dose_mg": weekly_dose_mg,
        "average_daily_mg": round(daily_target, 1),
        "schedule": schedule
    }


def _find_tablet_combination(target_mg: float, sorted_sizes: List[float]) -> List[Dict[str, Any]]:
    """Find tablet combination closest to target dose."""
    if target_mg <= 0:
        return []
    
    tablets = []
    remaining = target_mg
    
    for size in sorted_sizes:
        while remaining >= size * 0.9:  # Allow 10% tolerance
            tablets.append({"size_mg": size, "count": 1})
            remaining -= size
    
    # If we have a remainder, try to find a closer match
    if remaining > 0.5 and sorted_sizes:
        smallest = min(sorted_sizes)
        if remaining >= smallest * 0.5:
            tablets.append({"size_mg": smallest, "count": 1})
            remaining -= smallest
    
    return tablets


# ============================================================================
# Time in Therapeutic Range (TTR)
# ============================================================================

def calculate_ttr_rosendaal(
    inr_values: List[float],
    dates_days: List[int],
    target_low: float = INR_THERAPEUTIC_LOW,
    target_high: float = INR_THERAPEUTIC_HIGH
) -> Dict[str, Any]:
    """Time in range from piecewise linear interpolation between measured INRs.

    No extrapolation is made outside the observed dates. Duplicate measurement
    days are rejected rather than silently omitted.
    """
    if len(inr_values) < 2 or len(inr_values) != len(dates_days):
        raise ValueError("At least two INRs and one matching date per INR are required")
    _validate_measurements(inr_values, target_low, target_high)
    if not all(isinstance(d, (int, float)) and math.isfinite(d) for d in dates_days):
        raise ValueError("Measurement days must be finite numbers")
    pairs = sorted(zip(dates_days, inr_values))
    if any(b[0] <= a[0] for a, b in zip(pairs, pairs[1:])):
        raise ValueError("Measurement days must be unique")
    total_days = 0.0
    days_in_range = 0.0
    for (d0, v0), (d1, v1) in zip(pairs, pairs[1:]):
        duration = d1 - d0
        total_days += duration
        fractions = [0.0, 1.0]
        if v0 != v1:
            for boundary in (target_low, target_high):
                fraction = (boundary - v0) / (v1 - v0)
                if 0 < fraction < 1:
                    fractions.append(fraction)
        fractions = sorted(set(fractions))
        for start, end in zip(fractions, fractions[1:]):
            midpoint_inr = v0 + (v1 - v0) * (start + end) / 2
            if target_low <= midpoint_inr <= target_high:
                days_in_range += (end - start) * duration
    ttr = 100 * days_in_range / total_days
    return {
        "ttr_percent": round(ttr, 1),
        "days_in_range": round(days_in_range, 2),
        "total_days": total_days,
        "target_range": f"{target_low}-{target_high}",
        "num_inr_values": len(inr_values),
        "inr_values": inr_values,
        "quality": "GOOD" if ttr >= 65 else ("MODERATE" if ttr >= 50 else "POOR"),
    }


def _validate_measurements(inr_values: List[float], target_low: float, target_high: float) -> None:
    _validate_inr_and_target(1.0, target_low, target_high)
    if not inr_values or any(not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0 for v in inr_values):
        raise ValueError("INR measurements must be finite positive numbers")




def calculate_ttr_simple(
    inr_values: List[float],
    target_low: float = INR_THERAPEUTIC_LOW,
    target_high: float = INR_THERAPEUTIC_HIGH
) -> Dict[str, Any]:
    """
    Calculate simple percentage of INR values in therapeutic range.
    
    Args:
        inr_values: List of INR measurements
        target_low: Lower bound of target INR range
        target_high: Upper bound of target INR range
        
    Returns:
        Dictionary with TTR calculation
    """
    if not inr_values:
        raise ValueError("Need at least 1 INR value")
    
    _validate_measurements(inr_values, target_low, target_high)
    in_range = sum(1 for inr in inr_values if target_low <= inr <= target_high)
    ttr = (in_range / len(inr_values)) * 100
    
    return {
        "ttr_percent": round(ttr, 1),
        "values_in_range": in_range,
        "total_values": len(inr_values),
        "target_range": f"{target_low}-{target_high}",
        "quality": "GOOD" if ttr >= 65 else ("MODERATE" if ttr >= 50 else "POOR")
    }


# ============================================================================
# Pharmacogenomics
# ============================================================================

def apply_pharmacogenomic_adjustment(
    base_weekly_dose_mg: float,
    cyp2c9_metabolizer: str = "normal",
    vkorc1_sensitivity: str = "normal"
) -> Dict[str, Any]:
    """
    Apply pharmacogenomic dose adjustments for warfarin.
    
    CYP2C9 metabolizer status affects warfarin metabolism:
    - Normal: standard dose
    - Intermediate: ~15% reduction
    - Poor: ~40% reduction
    - Rapid/Ultra-rapid: 15-30% increase
    
    VKORC1 sensitivity affects vitamin K recycling:
    - Normal: standard dose
    - Sensitive: ~35% reduction
    - Resistant: ~30% increase
    
    Args:
        base_weekly_dose_mg: Calculated base weekly dose in mg
        cyp2c9_metabolizer: CYP2C9 metabolizer status
        vkorc1_sensitivity: VKORC1 sensitivity status
        
    Returns:
        Dictionary with pharmacogenomic-adjusted dose
    """
    if not isinstance(base_weekly_dose_mg, (int, float)) or not math.isfinite(base_weekly_dose_mg) or base_weekly_dose_mg <= 0:
        raise ValueError("Base weekly dose must be finite and positive")
    cyp2c9_key = cyp2c9_metabolizer.lower().strip()
    vkorc1_key = vkorc1_sensitivity.lower().strip()
    
    if cyp2c9_key not in CYP2C9_METABOLIZER_MULTIPLIERS:
        raise ValueError(f"Unknown CYP2C9 status: {cyp2c9_metabolizer}. "
                        f"Valid: {list(CYP2C9_METABOLIZER_MULTIPLIERS.keys())}")
    if vkorc1_key not in VKORC1_SENSITIVITY_MULTIPLIERS:
        raise ValueError(f"Unknown VKORC1 status: {vkorc1_sensitivity}. "
                        f"Valid: {list(VKORC1_SENSITIVITY_MULTIPLIERS.keys())}")
    
    cyp_mult = CYP2C9_METABOLIZER_MULTIPLIERS[cyp2c9_key]
    vkor_mult = VKORC1_SENSITIVITY_MULTIPLIERS[vkorc1_key]
    
    combined_multiplier = cyp_mult * vkor_mult
    adjusted_dose = base_weekly_dose_mg * combined_multiplier
    
    return {
        "base_weekly_dose_mg": base_weekly_dose_mg,
        "cyp2c9_status": cyp2c9_metabolizer,
        "cyp2c9_multiplier": cyp_mult,
        "vkorc1_status": vkorc1_sensitivity,
        "vkorc1_multiplier": vkor_mult,
        "combined_multiplier": round(combined_multiplier, 3),
        "adjusted_weekly_dose_mg": round(adjusted_dose, 1),
        "adjusted_daily_dose_mg": round(adjusted_dose / 7, 1),
        "notes": "UNVALIDATED illustrative sensitivity multipliers; NOT CPIC/IWPC/Gage dosing. Do not use for clinical prescribing.",
        "not_a_prescription": True
    }


# ============================================================================
# Tapering Schedule
# ============================================================================

def generate_taper_schedule(
    current_weekly_dose_mg: float,
    target_weekly_dose_mg: float,
    reduction_percent: float = 10.0,
    interval_days: int = 7
) -> Dict[str, Any]:
    """
    Generate a gradual tapering schedule for warfarin dose reduction.
    
    Args:
        current_weekly_dose_mg: Current weekly dose in mg
        target_weekly_dose_mg: Target weekly dose in mg
        reduction_percent: Percentage to reduce at each step (default 10%)
        interval_days: Days between dose reductions (default 7)
        
    Returns:
        Dictionary with tapering schedule
    """
    if not math.isfinite(current_weekly_dose_mg) or current_weekly_dose_mg <= 0:
        raise ValueError("Current dose must be finite and positive")
    if not math.isfinite(target_weekly_dose_mg) or not math.isfinite(reduction_percent):
        raise ValueError("Dose and reduction must be finite")
    if interval_days <= 0:
        raise ValueError("Interval must be positive")
    if target_weekly_dose_mg < 0:
        raise ValueError("Target dose must be non-negative")
    if reduction_percent <= 0 or reduction_percent >= 100:
        raise ValueError("Reduction percent must be between 0 and 100")
    if target_weekly_dose_mg >= current_weekly_dose_mg:
        raise ValueError("Target dose must be less than current dose for tapering")
    
    steps = []
    current_dose = current_weekly_dose_mg
    day = 0
    min_step = max(current_weekly_dose_mg * 0.01, 0.5)  # Minimum 1% or 0.5mg
    
    while current_dose > target_weekly_dose_mg + min_step:
        steps.append({
            "step": len(steps) + 1,
            "day": day,
            "weekly_dose_mg": round(current_dose, 1),
            "daily_dose_mg": round(current_dose / 7, 1),
            "reduction_from_previous": round(current_dose * reduction_percent / 100, 1) if steps else 0
        })
        
        current_dose *= (1 - reduction_percent / 100)
        day += interval_days
    
    # Add final target dose
    steps.append({
        "step": len(steps) + 1,
        "day": day,
        "weekly_dose_mg": round(target_weekly_dose_mg, 1),
        "daily_dose_mg": round(target_weekly_dose_mg / 7, 1),
        "reduction_from_previous": round(steps[-1]["weekly_dose_mg"] - target_weekly_dose_mg, 1) if steps else 0
    })
    
    return {
        "current_weekly_dose_mg": current_weekly_dose_mg,
        "target_weekly_dose_mg": target_weekly_dose_mg,
        "reduction_percent_per_step": reduction_percent,
        "interval_days": interval_days,
        "total_steps": len(steps),
        "total_taper_days": day,
        "schedule": steps
    }


# ============================================================================
# Full Assessment
# ============================================================================

def full_warfarin_assessment(
    inr: float,
    current_weekly_dose_mg: float,
    target_inr_low: float = INR_THERAPEUTIC_LOW,
    target_inr_high: float = INR_THERAPEUTIC_HIGH,
    cyp2c9_metabolizer: str = "normal",
    vkorc1_sensitivity: str = "normal",
    recent_inr_values: Optional[List[float]] = None,
    recent_inr_days: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Complete warfarin dosing assessment.
    
    Args:
        inr: Current INR value
        current_weekly_dose_mg: Current total weekly dose in mg
        target_inr_low: Lower bound of target INR range
        target_inr_high: Upper bound of target INR range
        cyp2c9_metabolizer: CYP2C9 metabolizer status
        vkorc1_sensitivity: VKORC1 sensitivity status
        recent_inr_values: Optional list of recent INR values for TTR
        recent_inr_days: Optional list of corresponding days for TTR
        
    Returns:
        Complete assessment dictionary
    """
    # INR interpretation uses the selected target; the genetic sensitivity
    # illustration is intentionally not applied to a titrated maintenance dose.
    inr_interp = interpret_inr(inr, target_inr_low, target_inr_high)
    
    # Dose adjustment
    dose_adj = calculate_new_weekly_dose(current_weekly_dose_mg, inr, target_inr_low, target_inr_high)
    
    # Do not multiply INR-derived maintenance doses by arbitrary genotype scalars.
    pgx = {
        "cyp2c9_status": cyp2c9_metabolizer,
        "vkorc1_status": vkorc1_sensitivity,
        "applied_to_maintenance_dose": False,
        "notes": "Use a validated genotype-guided initiation algorithm where indicated; not applied to titrated maintenance dosing.",
    }

    # TTR calculation if historical data available
    ttr = None
    if recent_inr_values and len(recent_inr_values) >= 2:
        if recent_inr_days:
            ttr = calculate_ttr_rosendaal(recent_inr_values, recent_inr_days, target_inr_low, target_inr_high)
        else:
            ttr = calculate_ttr_simple(recent_inr_values, target_inr_low, target_inr_high)
    
    # Daily schedule
    schedule = (generate_daily_schedule(dose_adj["new_weekly_dose_mg"])
                if dose_adj["new_weekly_dose_mg"] is not None else None)
    
    return {
        "inr_interpretation": inr_interp,
        "dose_adjustment": dose_adj,
        "pharmacogenomic_adjustment": pgx,
        "time_in_therapeutic_range": ttr,
        "daily_schedule": schedule,
        "disclaimer": "FOR EDUCATIONAL/RESEARCH USE ONLY. Illustrative arithmetic is not a prescription; assess bleeding and indication with a qualified clinician."
    }


def main(argv=None):
    """CLI entry point for warfarin dose adjustment."""
    parser = argparse.ArgumentParser(
        prog="warfarin-adjust",
        description="Warfarin INR Dose Adjustment Calculator"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # --- Interpret command ---
    interp_parser = subparsers.add_parser("interpret", help="Interpret INR value")
    interp_parser.add_argument("--inr", type=float, required=True, help="Current INR value")
    
    # --- Adjust command ---
    adjust_parser = subparsers.add_parser("adjust", help="Calculate dose adjustment")
    adjust_parser.add_argument("--inr", type=float, required=True, help="Current INR value")
    adjust_parser.add_argument("--weekly-dose", type=float, required=True, help="Current weekly dose in mg")
    adjust_parser.add_argument("--target-low", type=float, default=INR_THERAPEUTIC_LOW, help="Target INR low (default 2.0)")
    adjust_parser.add_argument("--target-high", type=float, default=INR_THERAPEUTIC_HIGH, help="Target INR high (default 3.0)")
    
    # --- TTR command ---
    ttr_parser = subparsers.add_parser("ttr", help="Calculate time in therapeutic range")
    ttr_parser.add_argument("--inr-values", type=float, nargs="+", required=True, help="List of INR values")
    ttr_parser.add_argument("--days", type=int, nargs="+", help="Corresponding days (for Rosendaal method)")
    ttr_parser.add_argument("--target-low", type=float, default=INR_THERAPEUTIC_LOW, help="Target INR low")
    ttr_parser.add_argument("--target-high", type=float, default=INR_THERAPEUTIC_HIGH, help="Target INR high")
    
    # --- PGx command ---
    pgx_parser = subparsers.add_parser("pgx", help="Pharmacogenomic dose adjustment")
    pgx_parser.add_argument("--dose", type=float, required=True, help="Base weekly dose in mg")
    pgx_parser.add_argument("--cyp2c9", default="normal", 
                           choices=["normal", "intermediate", "poor", "rapid", "ultra_rapid"],
                           help="CYP2C9 metabolizer status")
    pgx_parser.add_argument("--vkorc1", default="normal",
                           choices=["normal", "sensitive", "resistant"],
                           help="VKORC1 sensitivity status")
    
    # --- Taper command ---
    taper_parser = subparsers.add_parser("taper", help="Generate tapering schedule")
    taper_parser.add_argument("--current-dose", type=float, required=True, help="Current weekly dose mg")
    taper_parser.add_argument("--target-dose", type=float, required=True, help="Target weekly dose mg")
    taper_parser.add_argument("--reduction", type=float, default=10.0, help="Reduction %% per step (default 10)")
    taper_parser.add_argument("--interval", type=int, default=7, help="Days between steps (default 7)")
    
    # --- Assess command ---
    assess_parser = subparsers.add_parser("assess", help="Full assessment")
    assess_parser.add_argument("--inr", type=float, required=True, help="Current INR")
    assess_parser.add_argument("--weekly-dose", type=float, required=True, help="Current weekly dose mg")
    assess_parser.add_argument("--cyp2c9", default="normal", help="CYP2C9 status")
    assess_parser.add_argument("--vkorc1", default="normal", help="VKORC1 status")

    # --- Audit command ---
    audit_parser = subparsers.add_parser("audit", help="Run a supervisor audit task")
    audit_parser.add_argument("--task-id", default="CLI-AUDIT-01", help="Task identifier")
    audit_parser.add_argument("--target", default="SPECIMEN-CLI", help="Target identifier")
    audit_parser.add_argument("--primary", type=float, default=12.0, help="Primary metric value")
    audit_parser.add_argument("--secondary", type=float, default=4.0, help="Secondary metric value")
    audit_parser.add_argument("--descriptor", default="NOMINAL", help="Status descriptor")
    audit_parser.add_argument("--critical", action="store_true", help="Flag as critical")

    # --- Chat command ---
    chat_parser = subparsers.add_parser("chat", help="Query the supervisory chat")
    chat_parser.add_argument("query", nargs="+", help="Query text")

    # --- Verify-audit command ---
    subparsers.add_parser("verify-audit", help="Verify HMAC audit trail integrity")

    args = parser.parse_args(argv)
    
    if args.command == "interpret":
        result = interpret_inr(args.inr)
        print(json.dumps(result, indent=2))
    
    elif args.command == "adjust":
        result = calculate_new_weekly_dose(args.weekly_dose, args.inr, args.target_low, args.target_high)
        print(json.dumps(result, indent=2))
    
    elif args.command == "ttr":
        if args.days:
            result = calculate_ttr_rosendaal(args.inr_values, args.days, args.target_low, args.target_high)
        else:
            result = calculate_ttr_simple(args.inr_values, args.target_low, args.target_high)
        print(json.dumps(result, indent=2))
    
    elif args.command == "pgx":
        result = apply_pharmacogenomic_adjustment(args.dose, args.cyp2c9, args.vkorc1)
        print(json.dumps(result, indent=2))
    
    elif args.command == "taper":
        result = generate_taper_schedule(args.current_dose, args.target_dose, args.reduction, args.interval)
        print(json.dumps(result, indent=2))
    
    elif args.command == "assess":
        result = full_warfarin_assessment(args.inr, args.weekly_dose, cyp2c9_metabolizer=args.cyp2c9, vkorc1_sensitivity=args.vkorc1)
        print(json.dumps(result, indent=2))

    elif args.command == "audit":
        from agents.models import SystemTaskPayload
        from agents.supervisor import SystemSupervisor
        supervisor = SystemSupervisor(model_provider="mock")
        payload = SystemTaskPayload(
            task_id=args.task_id,
            target_identifier=args.target,
            primary_metric=args.primary,
            secondary_metric=args.secondary,
            status_descriptor=args.descriptor,
            is_critical_flag=args.critical,
        )
        dossier = supervisor.process_task(payload)
        print(json.dumps(dossier.to_dict(), indent=2, default=str))

    elif args.command == "chat":
        from agents.supervisor import SystemSupervisor
        supervisor = SystemSupervisor(model_provider="mock")
        query = " ".join(args.query)
        response = supervisor.query_supervisory_chat(query)
        print(json.dumps({"response": response}, indent=2))

    elif args.command == "verify-audit":
        from agents.base import AuditLogger
        valid = AuditLogger.verify_integrity()
        print(json.dumps({"audit_integrity_valid": valid, "blocks": len(AuditLogger.get_trail())}, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
