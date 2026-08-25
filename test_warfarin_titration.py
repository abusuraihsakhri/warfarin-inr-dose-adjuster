"""
Tests for Warfarin INR Dose Adjustment Calculator.
"""
import pytest
from warfarin_titration import (
    interpret_inr,
    calculate_new_weekly_dose,
    generate_daily_schedule,
    calculate_ttr_rosendaal,
    calculate_ttr_simple,
    apply_pharmacogenomic_adjustment,
    generate_taper_schedule,
    full_warfarin_assessment,
    main,
    INR_THERAPEUTIC_LOW,
    INR_THERAPEUTIC_HIGH,
)


# ============================================================================
# INR Interpretation Tests
# ============================================================================

class TestINRInterpretation:
    def test_therapeutic_inr(self):
        result = interpret_inr(2.5)
        assert result["status"] == "THERAPEUTIC"
        assert result["risk_level"] == "LOW"
        assert result["dose_change_percent"] == 0.0
        assert result["hold_doses"] == 0

    def test_subtherapeutic_low(self):
        result = interpret_inr(1.5)
        assert result["status"] == "SUBTHERAPEUTIC"
        assert result["dose_change_percent"] > 0

    def test_subtherapeutic_very_low(self):
        result = interpret_inr(1.2)
        assert result["status"] == "HIGHLY_SUBTHERAPEUTIC"
        assert result["risk_level"] == "HIGH"

    def test_mildly_supratherapeutic(self):
        result = interpret_inr(3.3)
        assert result["status"] == "MILDLY_SUPRATHERAPEUTIC"
        assert result["dose_change_percent"] < 0
        assert result["hold_doses"] == 0

    def test_supratherapeutic(self):
        result = interpret_inr(4.0)
        assert result["status"] == "SUPRATHERAPEUTIC"
        assert result["hold_doses"] == 1

    def test_dangerous(self):
        result = interpret_inr(6.0)
        assert result["status"] == "DANGEROUS"
        assert result["vitamin_k"] is not None
        assert result["hold_doses"] == 2

    def test_critical(self):
        result = interpret_inr(12.0)
        assert result["status"] == "CRITICAL"
        assert result["risk_level"] == "CRITICAL"
        assert result["vitamin_k"]["dose_mg"] == 5.0

    def test_boundary_therapeutic_low(self):
        result = interpret_inr(2.0)
        assert result["status"] == "THERAPEUTIC"

    def test_boundary_therapeutic_high(self):
        result = interpret_inr(3.0)
        assert result["status"] == "THERAPEUTIC"

    def test_invalid_inr(self):
        with pytest.raises(ValueError):
            interpret_inr(0)
        with pytest.raises(ValueError):
            interpret_inr(-1)


# ============================================================================
# Dose Adjustment Tests
# ============================================================================

class TestDoseAdjustment:
    def test_therapeutic_no_change(self):
        result = calculate_new_weekly_dose(35.0, 2.5)
        assert result["new_weekly_dose_mg"] == 35.0
        assert result["dose_change_percent"] == 0.0

    def test_subtherapeutic_increase(self):
        result = calculate_new_weekly_dose(35.0, 1.8)
        assert result["new_weekly_dose_mg"] > 35.0
        assert result["dose_change_percent"] > 0

    def test_supratherapeutic_decrease(self):
        result = calculate_new_weekly_dose(35.0, 3.3)
        assert result["new_weekly_dose_mg"] < 35.0
        assert result["dose_change_percent"] < 0

    def test_dangerous_hold(self):
        result = calculate_new_weekly_dose(35.0, 5.0)
        assert result["hold_doses"] == 2
        assert result["vitamin_k"] is not None

    def test_critical_hold(self):
        result = calculate_new_weekly_dose(35.0, 12.0)
        assert result["hold_doses"] == 3
        assert result["vitamin_k"]["dose_mg"] == 5.0

    def test_custom_target_range(self):
        result = calculate_new_weekly_dose(35.0, 2.8, 2.5, 3.5)
        # INR 2.8 is therapeutic for 2.5-3.5 range
        assert result["status"] == "THERAPEUTIC"

    def test_invalid_dose(self):
        with pytest.raises(ValueError):
            calculate_new_weekly_dose(0, 2.5)

    def test_invalid_inr(self):
        with pytest.raises(ValueError):
            calculate_new_weekly_dose(35.0, 0)


# ============================================================================
# Daily Schedule Tests
# ============================================================================

class TestDailySchedule:
    def test_basic_schedule(self):
        result = generate_daily_schedule(35.0)
        assert "schedule" in result
        assert len(result["schedule"]) == 7
        total = sum(day["dose_mg"] for day in result["schedule"].values())
        assert abs(total - 35.0) < 1.0

    def test_schedule_has_tablets(self):
        result = generate_daily_schedule(35.0)
        for day, info in result["schedule"].items():
            assert "dose_mg" in info
            assert "tablets" in info

    def test_invalid_dose(self):
        with pytest.raises(ValueError):
            generate_daily_schedule(0)


# ============================================================================
# TTR Tests
# ============================================================================

class TestTTR:
    def test_all_in_range(self):
        inr_values = [2.1, 2.5, 2.8, 2.3, 2.7]
        result = calculate_ttr_simple(inr_values)
        assert result["ttr_percent"] == 100.0

    def test_none_in_range(self):
        inr_values = [1.0, 1.5, 1.8, 3.5, 4.0]
        result = calculate_ttr_simple(inr_values)
        assert result["ttr_percent"] == 0.0

    def test_mixed(self):
        inr_values = [2.1, 1.5, 2.8, 3.5, 2.3]
        result = calculate_ttr_simple(inr_values)
        assert result["ttr_percent"] == 60.0  # 3/5

    def test_rosendaal_method(self):
        inr_values = [2.0, 3.0]
        days = [0, 14]
        result = calculate_ttr_rosendaal(inr_values, days)
        assert result["ttr_percent"] == 100.0

    def test_rosendaal_with_crossover(self):
        inr_values = [1.5, 3.5]
        days = [0, 14]
        result = calculate_ttr_rosendaal(inr_values, days)
        # Linear interpolation crosses 2.0 and 3.0
        assert 0 < result["ttr_percent"] < 100

    def test_rosendaal_insufficient_data(self):
        with pytest.raises(ValueError):
            calculate_ttr_rosendaal([2.5], [0])

    def test_quality_assessment(self):
        result = calculate_ttr_simple([2.1, 2.5, 2.8, 2.3, 2.7, 2.9, 3.0])
        assert result["quality"] == "GOOD"


# ============================================================================
# Pharmacogenomics Tests
# ============================================================================

class TestPharmacogenomics:
    def test_normal_metabolizer(self):
        result = apply_pharmacogenomic_adjustment(35.0, "normal", "normal")
        assert result["adjusted_weekly_dose_mg"] == 35.0
        assert result["combined_multiplier"] == 1.0

    def test_poor_metabolizer(self):
        result = apply_pharmacogenomic_adjustment(35.0, "poor", "normal")
        assert result["adjusted_weekly_dose_mg"] < 35.0
        assert result["cyp2c9_multiplier"] == 0.60

    def test_sensitive_vkorc1(self):
        result = apply_pharmacogenomic_adjustment(35.0, "normal", "sensitive")
        assert result["adjusted_weekly_dose_mg"] < 35.0
        assert result["vkorc1_multiplier"] == 0.65

    def test_combined_poor_sensitive(self):
        result = apply_pharmacogenomic_adjustment(35.0, "poor", "sensitive")
        assert result["combined_multiplier"] == 0.60 * 0.65

    def test_rapid_metabolizer(self):
        result = apply_pharmacogenomic_adjustment(35.0, "rapid", "normal")
        assert result["adjusted_weekly_dose_mg"] > 35.0

    def test_invalid_cyp2c9(self):
        with pytest.raises(ValueError):
            apply_pharmacogenomic_adjustment(35.0, "invalid", "normal")

    def test_invalid_vkorc1(self):
        with pytest.raises(ValueError):
            apply_pharmacogenomic_adjustment(35.0, "normal", "invalid")


# ============================================================================
# Tapering Tests
# ============================================================================

class TestTapering:
    def test_basic_taper(self):
        result = generate_taper_schedule(50.0, 30.0, 10.0, 7)
        assert result["total_steps"] > 1
        assert result["schedule"][0]["weekly_dose_mg"] == 50.0
        assert result["schedule"][-1]["weekly_dose_mg"] == 30.0

    def test_taper_to_zero(self):
        result = generate_taper_schedule(50.0, 0.0, 10.0, 7)
        assert result["schedule"][-1]["weekly_dose_mg"] == 0.0 or result["schedule"][-1]["mme"] == 0.0

    def test_invalid_target_higher(self):
        with pytest.raises(ValueError):
            generate_taper_schedule(30.0, 50.0)

    def test_invalid_reduction(self):
        with pytest.raises(ValueError):
            generate_taper_schedule(50.0, 30.0, 100.0)


# ============================================================================
# Full Assessment Tests
# ============================================================================

class TestFullAssessment:
    def test_basic_assessment(self):
        result = full_warfarin_assessment(2.5, 35.0)
        assert "inr_interpretation" in result
        assert "dose_adjustment" in result
        assert "pharmacogenomic_adjustment" in result
        assert "daily_schedule" in result

    def test_assessment_with_pgx(self):
        result = full_warfarin_assessment(2.5, 35.0, cyp2c9_metabolizer="poor")
        assert result["pharmacogenomic_adjustment"]["cyp2c9_status"] == "poor"

    def test_assessment_with_ttr(self):
        inr_values = [2.1, 2.5, 2.8, 2.3, 2.7]
        days = [0, 7, 14, 21, 28]
        result = full_warfarin_assessment(2.5, 35.0, recent_inr_values=inr_values, recent_inr_days=days)
        assert result["time_in_therapeutic_range"] is not None


# ============================================================================
# CLI Tests
# ============================================================================

class TestCLI:
    def test_interpret_command(self):
        ret = main(["interpret", "--inr", "2.5"])
        assert ret == 0

    def test_adjust_command(self):
        ret = main(["adjust", "--inr", "2.5", "--weekly-dose", "35"])
        assert ret == 0

    def test_ttr_command(self):
        ret = main(["ttr", "--inr-values", "2.1", "2.5", "2.8", "2.3"])
        assert ret == 0

    def test_pgx_command(self):
        ret = main(["pgx", "--dose", "35", "--cyp2c9", "normal", "--vkorc1", "normal"])
        assert ret == 0

    def test_taper_command(self):
        ret = main(["taper", "--current-dose", "50", "--target-dose", "30"])
        assert ret == 0

    def test_assess_command(self):
        ret = main(["assess", "--inr", "2.5", "--weekly-dose", "35"])
        assert ret == 0
