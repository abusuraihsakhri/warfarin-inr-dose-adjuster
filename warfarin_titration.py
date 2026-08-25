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

def interpret_inr(inr: float) -> Dict[str, Any]:
    """
    Interpret INR value and provide clinical guidance.
    
    Args:
        inr: International Normalized Ratio
        
    Returns:
        Dictionary with interpretation, risk level, and action
    """
    if inr <= 0:
        raise ValueError("INR must be positive")
    
    if inr < 1.5:
        return {
            "inr": inr,
            "status": "HIGHLY_SUBTHERAPEUTIC",
            "risk_level": "HIGH",
            "action": "Increase dose significantly. Consider bridging with LMWH if high thrombotic risk.",
            "dose_change_percent": 15.0,
            "hold_doses": 0,
            "recheck_days": 7,
            "vitamin_k": None,
            "notes": "Significantly below therapeutic range. Assess compliance and drug interactions."
        }
    elif inr < 2.0:
        return {
            "inr": inr,
            "status": "SUBTHERAPEUTIC",
            "risk_level": "MODERATE",
            "action": "Increase weekly dose by 5-15%. Recheck INR in 1-2 weeks.",
            "dose_change_percent": DOSE_INCREASE_MILD * 100,
            "hold_doses": 0,
            "recheck_days": 10,
            "vitamin_k": None,
            "notes": "Below therapeutic range. Consider dietary vitamin K changes or medication interactions."
        }
    elif inr <= 3.0:
        return {
            "inr": inr,
            "status": "THERAPEUTIC",
            "risk_level": "LOW",
            "action": "No dose change. Continue current regimen.",
            "dose_change_percent": 0.0,
            "hold_doses": 0,
            "recheck_days": 28,
            "vitamin_k": None,
            "notes": "Within therapeutic range (2.0-3.0). Maintain current dosing."
        }
    elif inr <= 3.5:
        return {
            "inr": inr,
            "status": "MILDLY_SUPRATHERAPEUTIC",
            "risk_level": "MODERATE",
            "action": "Decrease weekly dose by 5-15%. Recheck INR in 1-2 weeks.",
            "dose_change_percent": -DOSE_DECREASE_MILD * 100,
            "hold_doses": 0,
            "recheck_days": 10,
            "vitamin_k": None,
            "notes": "Slightly above therapeutic range. Assess for dietary changes or drug interactions."
        }
    elif inr <= 4.5:
        return {
            "inr": inr,
            "status": "SUPRATHERAPEUTIC",
            "risk_level": "HIGH",
            "action": "Hold 1 dose. Decrease weekly dose by 10-20%. Recheck INR in 1 week.",
            "dose_change_percent": -DOSE_DECREASE_MODERATE * 100,
            "hold_doses": 1,
            "recheck_days": 7,
            "vitamin_k": None,
            "notes": "Above therapeutic range. Hold one dose and reduce maintenance. Check for interactions."
        }
    elif inr <= 10.0:
        return {
            "inr": inr,
            "status": "DANGEROUS",
            "risk_level": "VERY_HIGH",
            "action": "Hold 1-2 doses. Give vitamin K 1-2.5 mg PO. Recheck INR in 24 hours.",
            "dose_change_percent": -20.0,
            "hold_doses": 2,
            "recheck_days": 1,
            "vitamin_k": {"dose_mg": 2.5, "route": "PO", "note": "1-2.5 mg oral vitamin K"},
            "notes": "Dangerously elevated. Administer vitamin K and monitor closely for bleeding."
        }
    else:  # INR > 10
        return {
            "inr": inr,
            "status": "CRITICAL",
            "risk_level": "CRITICAL",
            "action": "Hold warfarin. Give vitamin K 2.5-5 mg PO. Recheck INR in 24 hours. Consider hospitalization.",
            "dose_change_percent": -25.0,
            "hold_doses": 3,
            "recheck_days": 1,
            "vitamin_k": {"dose_mg": 5.0, "route": "PO", "note": "2.5-5 mg oral vitamin K"},
            "notes": "Critical INR. High bleeding risk. Administer vitamin K urgently. Evaluate for active bleeding."
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
    """
    Calculate new weekly warfarin dose based on current INR.
    
    Args:
        current_weekly_dose_mg: Current total weekly dose in mg
        inr: Current INR value
        target_inr_low: Lower bound of target INR range
        target_inr_high: Upper bound of target INR range
        
    Returns:
        Dictionary with dose adjustment details
    """
    if current_weekly_dose_mg <= 0:
        raise ValueError("Current weekly dose must be positive")
    if inr <= 0:
        raise ValueError("INR must be positive")
    
    interp = interpret_inr(inr)
    
    # Calculate adjustment
    change_pct = interp["dose_change_percent"]
    dose_change_mg = current_weekly_dose_mg * (change_pct / 100)
    new_weekly_dose = current_weekly_dose_mg + dose_change_mg
    
    # Ensure dose doesn't go negative
    new_weekly_dose = max(0, new_weekly_dose)
    
    # Calculate daily dose equivalent
    new_daily_dose = new_weekly_dose / 7
    
    return {
        "current_weekly_dose_mg": current_weekly_dose_mg,
        "inr": inr,
        "target_range": f"{target_inr_low}-{target_inr_high}",
        "status": interp["status"],
        "dose_change_percent": change_pct,
        "dose_change_mg": round(dose_change_mg, 1),
        "new_weekly_dose_mg": round(new_weekly_dose, 1),
        "new_daily_dose_mg": round(new_daily_dose, 1),
        "hold_doses": interp["hold_doses"],
        "recheck_days": interp["recheck_days"],
        "vitamin_k": interp["vitamin_k"],
        "action": interp["action"],
        "notes": interp["notes"]
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
    """
    Calculate Time in Therapeutic Range using Rosendaal's linear interpolation method.
    
    The Rosendaal method interpolates linearly between consecutive INR measurements
    and calculates the percentage of time the interpolated INR falls within range.
    
    Args:
        inr_values: List of INR measurements
        dates_days: List of corresponding days (integers, e.g., days from start)
        target_low: Lower bound of target INR range
        target_high: Upper bound of target INR range
        
    Returns:
        Dictionary with TTR calculation results
    """
    if len(inr_values) < 2:
        raise ValueError("Need at least 2 INR values for TTR calculation")
    if len(inr_values) != len(dates_days):
        raise ValueError("INR values and dates must have same length")
    
    # Sort by date
    paired = sorted(zip(dates_days, inr_values))
    dates_sorted = [p[0] for p in paired]
    inr_sorted = [p[1] for p in paired]
    
    total_days = 0
    days_in_range = 0
    
    for i in range(len(dates_sorted) - 1):
        t_start = dates_sorted[i]
        t_end = dates_sorted[i + 1]
        inr_start = inr_sorted[i]
        inr_end = inr_sorted[i + 1]
        
        interval_days = t_end - t_start
        if interval_days <= 0:
            continue
        
        total_days += interval_days
        
        # Linear interpolation
        # Check if entire interval is in range
        if target_low <= inr_start <= target_high and target_low <= inr_end <= target_high:
            days_in_range += interval_days
        # Check if entire interval is out of range
        elif (inr_start < target_low and inr_end < target_low) or \
             (inr_start > target_high and inr_end > target_high):
            pass  # 0 days in range
        else:
            # Find crossover points
            # INR(t) = inr_start + (inr_end - inr_start) * (t - t_start) / (t_end - t_start)
            slope = (inr_end - inr_start) / interval_days
            
            # Find time when INR crosses target_low
            t_low = None
            if slope != 0:
                t_low_candidate = t_start + (target_low - inr_start) / slope
                if t_start <= t_low_candidate <= t_end:
                    t_low = t_low_candidate
            
            # Find time when INR crosses target_high
            t_high = None
            if slope != 0:
                t_high_candidate = t_start + (target_high - inr_start) / slope
                if t_start <= t_high_candidate <= t_end:
                    t_high = t_high_candidate
            
            # Calculate time in range within this interval
            crossover_times = sorted(filter(None, [t_low, t_high]))
            
            if len(crossover_times) == 2:
                # Two crossovers - time in range is between them or outside
                if inr_start < target_low:
                    # Below -> in range -> above (or below -> above -> below)
                    days_in_range += crossover_times[1] - crossover_times[0]
                elif inr_start > target_high:
                    # Above -> in range -> below
                    days_in_range += crossover_times[1] - crossover_times[0]
                else:
                    # In range -> out -> in range
                    days_in_range += (crossover_times[0] - t_start) + (t_end - crossover_times[1])
            elif len(crossover_times) == 1:
                # One crossover
                if target_low <= inr_start <= target_high:
                    days_in_range += crossover_times[0] - t_start
                elif target_low <= inr_end <= target_high:
                    days_in_range += t_end - crossover_times[0]
    
    ttr = (days_in_range / total_days * 100) if total_days > 0 else 0
    
    return {
        "ttr_percent": round(ttr, 1),
        "days_in_range": round(days_in_range, 1),
        "total_days": total_days,
        "target_range": f"{target_low}-{target_high}",
        "num_inr_values": len(inr_values),
        "inr_values": inr_values,
        "quality": "GOOD" if ttr >= 65 else ("MODERATE" if ttr >= 50 else "POOR")
    }


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
        "notes": "Pharmacogenomic adjustments are estimates. Clinical response and INR monitoring remain essential."
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
    if current_weekly_dose_mg <= 0:
        raise ValueError("Current dose must be positive")
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
    # INR interpretation
    inr_interp = interpret_inr(inr)
    
    # Dose adjustment
    dose_adj = calculate_new_weekly_dose(current_weekly_dose_mg, inr, target_inr_low, target_inr_high)
    
    # Pharmacogenomic adjustment
    pgx = apply_pharmacogenomic_adjustment(
        dose_adj["new_weekly_dose_mg"],
        cyp2c9_metabolizer,
        vkorc1_sensitivity
    )
    
    # TTR calculation if historical data available
    ttr = None
    if recent_inr_values and len(recent_inr_values) >= 2:
        if recent_inr_days:
            ttr = calculate_ttr_rosendaal(recent_inr_values, recent_inr_days, target_inr_low, target_inr_high)
        else:
            ttr = calculate_ttr_simple(recent_inr_values, target_inr_low, target_inr_high)
    
    # Daily schedule
    schedule = generate_daily_schedule(pgx["adjusted_weekly_dose_mg"])
    
    return {
        "inr_interpretation": inr_interp,
        "dose_adjustment": dose_adj,
        "pharmacogenomic_adjustment": pgx,
        "time_in_therapeutic_range": ttr,
        "daily_schedule": schedule,
        "disclaimer": "FOR EDUCATIONAL/RESEARCH USE ONLY. Not a substitute for clinical pharmacist review."
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
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
