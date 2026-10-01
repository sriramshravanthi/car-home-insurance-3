"""Unit tests for insurance_risk_service.py: input validation and scoring formulas."""
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from insurance_risk_service import (
    CarQuote,
    HomeQuote,
    RiskResult,
    RiskTier,
    _tier_for_score,
    app,
    main,
    run_live_check,
    score_car_risk,
    score_home_risk,
)

client = TestClient(app)

VALID_CAR = dict(
    driver_age=40,
    years_licensed=20,
    vehicle_age=5,
    annual_mileage=12000,
    accidents_last_5yrs=0,
    claims_last_5yrs=0,
    vehicle_value=15000,
    urban_area=False,
)

VALID_HOME = dict(
    property_age=10,
    square_footage=1800,
    roof_age=5,
    claims_last_5yrs=0,
    security_system=True,
    flood_zone=False,
    fire_station_distance_km=3.0,
    property_value=350000,
)


# ---------------------------------------------------------------------------
# CarQuote field-level validation
# ---------------------------------------------------------------------------

def test_car_quote_accepts_valid_input():
    quote = CarQuote(**VALID_CAR)
    assert quote.driver_age == 40


@pytest.mark.parametrize(
    "field,value",
    [
        ("driver_age", 15),          # below minimum driving age
        ("driver_age", 101),         # above sanity cap
        ("years_licensed", -1),
        ("years_licensed", 85),      # above cap
        ("vehicle_age", -1),
        ("vehicle_age", 61),         # above cap
        ("annual_mileage", -1),
        ("annual_mileage", 150_001), # above cap
        ("accidents_last_5yrs", -1),
        ("accidents_last_5yrs", 21), # above cap
        ("claims_last_5yrs", -1),
        ("claims_last_5yrs", 21),    # above cap
        ("vehicle_value", 0),
        ("vehicle_value", -100),
        ("vehicle_value", 2_000_001),# above cap
    ],
)
def test_car_quote_rejects_out_of_range_fields(field, value):
    payload = {**VALID_CAR, field: value}
    with pytest.raises(ValidationError):
        CarQuote(**payload)


@pytest.mark.parametrize("value", [16, 100])
def test_car_quote_driver_age_boundaries_are_accepted(value):
    payload = {**VALID_CAR, "driver_age": value, "years_licensed": 0}
    CarQuote(**payload)  # should not raise


def test_car_quote_rejects_years_licensed_exceeding_driver_age():
    payload = {**VALID_CAR, "driver_age": 18, "years_licensed": 10}
    with pytest.raises(ValidationError, match="years_licensed"):
        CarQuote(**payload)


def test_car_quote_allows_years_licensed_at_exact_boundary():
    payload = {**VALID_CAR, "driver_age": 25, "years_licensed": 9}
    CarQuote(**payload)  # 25 - 16 == 9, should be allowed


# ---------------------------------------------------------------------------
# HomeQuote field-level validation
# ---------------------------------------------------------------------------

def test_home_quote_accepts_valid_input():
    quote = HomeQuote(**VALID_HOME)
    assert quote.property_value == 350000


@pytest.mark.parametrize(
    "field,value",
    [
        ("property_age", -1),
        ("property_age", 301),
        ("square_footage", 0),
        ("square_footage", -1),
        ("square_footage", 50_001),
        ("roof_age", -1),
        ("roof_age", 301),
        ("claims_last_5yrs", -1),
        ("claims_last_5yrs", 21),
        ("fire_station_distance_km", -1),
        ("fire_station_distance_km", 101),
        ("property_value", 0),
        ("property_value", -100),
        ("property_value", 50_000_001),
    ],
)
def test_home_quote_rejects_out_of_range_fields(field, value):
    payload = {**VALID_HOME, field: value}
    with pytest.raises(ValidationError):
        HomeQuote(**payload)


def test_home_quote_rejects_roof_older_than_property():
    payload = {**VALID_HOME, "property_age": 5, "roof_age": 50}
    with pytest.raises(ValidationError, match="roof_age"):
        HomeQuote(**payload)


def test_home_quote_allows_roof_age_equal_to_property_age():
    payload = {**VALID_HOME, "property_age": 10, "roof_age": 10}
    HomeQuote(**payload)  # should not raise


# ---------------------------------------------------------------------------
# RiskResult output validation
# ---------------------------------------------------------------------------

def test_risk_result_rejects_negative_premium_multiplier():
    with pytest.raises(ValidationError):
        RiskResult(risk_score=50, risk_tier=RiskTier.MEDIUM, premium_multiplier=-0.1)


def test_risk_result_rejects_score_out_of_bounds():
    with pytest.raises(ValidationError):
        RiskResult(risk_score=101, risk_tier=RiskTier.HIGH, premium_multiplier=1.0)
    with pytest.raises(ValidationError):
        RiskResult(risk_score=-1, risk_tier=RiskTier.LOW, premium_multiplier=1.0)


# ---------------------------------------------------------------------------
# Scoring logic sanity checks
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "score,expected",
    [(0, RiskTier.LOW), (33.9, RiskTier.LOW), (34, RiskTier.MEDIUM), (66.9, RiskTier.MEDIUM), (67, RiskTier.HIGH), (100, RiskTier.HIGH)],
)
def test_tier_for_score_boundaries(score, expected):
    assert _tier_for_score(score) == expected


def test_score_car_risk_premium_multiplier_never_negative():
    result = score_car_risk(CarQuote(**VALID_CAR))
    assert result.premium_multiplier >= 0


def test_score_home_risk_premium_multiplier_never_negative():
    result = score_home_risk(HomeQuote(**VALID_HOME))
    assert result.premium_multiplier >= 0


# ---------------------------------------------------------------------------
# score_car_risk formula
# ---------------------------------------------------------------------------
# Baseline: score=30, driver_age=40 (no age bracket bonus), years_licensed=20
# (-10), vehicle_age=5 (+3), annual_mileage=12000 (+6.4) => 29.4

def test_car_score_baseline():
    result = score_car_risk(CarQuote(**VALID_CAR))
    assert result.risk_score == pytest.approx(29.4)
    assert result.risk_tier == RiskTier.LOW
    assert result.premium_multiplier == pytest.approx(1.13)


def test_car_score_young_driver_bracket_under_25():
    quote = CarQuote(**{**VALID_CAR, "driver_age": 20, "years_licensed": 0})
    result = score_car_risk(quote)
    # 30 + 20 (young) - 0 + 3 + 6.4 = 59.4
    assert result.risk_score == pytest.approx(59.4)
    assert result.risk_tier == RiskTier.MEDIUM


def test_car_score_mid_bracket_25_to_29():
    quote = CarQuote(**{**VALID_CAR, "driver_age": 27, "years_licensed": 9})
    result = score_car_risk(quote)
    # 30 + 8 - 4.5 + 3 + 6.4 = 42.9
    assert result.risk_score == pytest.approx(42.9)


def test_car_score_senior_driver_bracket_over_70():
    quote = CarQuote(**{**VALID_CAR, "driver_age": 75, "years_licensed": 20})
    result = score_car_risk(quote)
    # 30 + 6 - 10 + 3 + 6.4 = 35.4
    assert result.risk_score == pytest.approx(35.4)


def test_car_score_middle_age_gets_no_bracket_bonus():
    # ages 30-70 fall into the implicit "else" branch (+0)
    quote = CarQuote(**{**VALID_CAR, "driver_age": 50, "years_licensed": 20})
    result = score_car_risk(quote)
    assert result.risk_score == pytest.approx(29.4)


def test_car_score_years_licensed_is_capped_at_20():
    # driver_age=40 allows years_licensed up to 24; both 20 and 24 should
    # clamp to the same -10 penalty (min(years_licensed, 20) * 0.5).
    capped = score_car_risk(CarQuote(**{**VALID_CAR, "years_licensed": 24}))
    uncapped = score_car_risk(CarQuote(**{**VALID_CAR, "years_licensed": 20}))
    assert capped.risk_score == pytest.approx(uncapped.risk_score)
    assert capped.risk_score == pytest.approx(29.4)


def test_car_score_vehicle_age_is_capped_at_15():
    quote = CarQuote(**{**VALID_CAR, "vehicle_age": 40})
    result = score_car_risk(quote)
    # 30 - 10 + min(40,15)*0.6=9 + 6.4 = 35.4
    assert result.risk_score == pytest.approx(35.4)


def test_car_score_annual_mileage_scales_linearly():
    quote = CarQuote(**{**VALID_CAR, "annual_mileage": 30000})
    result = score_car_risk(quote)
    # 30 - 10 + 3 + (30000/15000)*8=16 = 39
    assert result.risk_score == pytest.approx(39.0)


def test_car_score_accidents_add_12_points_each():
    quote = CarQuote(**{**VALID_CAR, "accidents_last_5yrs": 2})
    result = score_car_risk(quote)
    assert result.risk_score == pytest.approx(29.4 + 24)


def test_car_score_claims_add_10_points_each():
    quote = CarQuote(**{**VALID_CAR, "claims_last_5yrs": 1})
    result = score_car_risk(quote)
    assert result.risk_score == pytest.approx(29.4 + 10)


def test_car_score_urban_area_adds_5_points():
    quote = CarQuote(**{**VALID_CAR, "urban_area": True})
    result = score_car_risk(quote)
    assert result.risk_score == pytest.approx(29.4 + 5)


def test_car_score_clamps_at_100_when_all_factors_maxed():
    quote = CarQuote(
        driver_age=20,
        years_licensed=0,
        vehicle_age=60,
        annual_mileage=150_000,
        accidents_last_5yrs=20,
        claims_last_5yrs=20,
        vehicle_value=15000,
        urban_area=True,
    )
    result = score_car_risk(quote)
    assert result.risk_score == 100
    assert result.risk_tier == RiskTier.HIGH
    assert result.premium_multiplier == pytest.approx(2.4)


# ---------------------------------------------------------------------------
# score_home_risk formula
# ---------------------------------------------------------------------------
# Baseline: score=25, property_age=10 (+3), roof_age=5 (+2.5), fire_dist=3.0
# (+2.4), security_system=True (-8), square_footage=1800 (+2.7) => 27.6

def test_home_score_baseline():
    result = score_home_risk(HomeQuote(**VALID_HOME))
    assert result.risk_score == pytest.approx(27.6)
    assert result.risk_tier == RiskTier.LOW
    assert result.premium_multiplier == pytest.approx(1.05)


def test_home_score_property_age_is_capped_at_50():
    quote = HomeQuote(**{**VALID_HOME, "property_age": 100, "roof_age": 5})
    result = score_home_risk(quote)
    # 27.6 + (min(100,50)*0.3 - min(10,50)*0.3) = 27.6 + (15 - 3) = 39.6
    assert result.risk_score == pytest.approx(39.6)


def test_home_score_roof_age_is_capped_at_30():
    quote = HomeQuote(**{**VALID_HOME, "property_age": 40, "roof_age": 40})
    result = score_home_risk(quote)
    # 25 + min(40,50)*0.3=12 + min(40,30)*0.5=15 + 0 + 0 + 2.4 - 8 + 2.7 = 49.1
    assert result.risk_score == pytest.approx(49.1)


def test_home_score_claims_add_12_points_each():
    quote = HomeQuote(**{**VALID_HOME, "claims_last_5yrs": 1})
    result = score_home_risk(quote)
    assert result.risk_score == pytest.approx(27.6 + 12)


def test_home_score_flood_zone_adds_18_points():
    quote = HomeQuote(**{**VALID_HOME, "flood_zone": True})
    result = score_home_risk(quote)
    assert result.risk_score == pytest.approx(27.6 + 18)


def test_home_score_fire_station_distance_is_capped_at_20km():
    quote = HomeQuote(**{**VALID_HOME, "fire_station_distance_km": 50})
    result = score_home_risk(quote)
    # 27.6 + (min(50,20)*0.8 - min(3,20)*0.8) = 27.6 + (16 - 2.4) = 41.2
    assert result.risk_score == pytest.approx(41.2)


def test_home_score_no_security_system_removes_discount():
    quote = HomeQuote(**{**VALID_HOME, "security_system": False})
    result = score_home_risk(quote)
    assert result.risk_score == pytest.approx(27.6 + 8)


def test_home_score_square_footage_scales_linearly():
    quote = HomeQuote(**{**VALID_HOME, "square_footage": 4000})
    result = score_home_risk(quote)
    # 27.6 + ((4000/2000)*3 - (1800/2000)*3) = 27.6 + (6 - 2.7) = 30.9
    assert result.risk_score == pytest.approx(30.9)


def test_home_score_clamps_at_100_when_all_factors_maxed():
    quote = HomeQuote(
        property_age=300,
        square_footage=50_000,
        roof_age=300,
        claims_last_5yrs=20,
        security_system=False,
        flood_zone=True,
        fire_station_distance_km=100,
        property_value=350000,
    )
    result = score_home_risk(quote)
    assert result.risk_score == 100
    assert result.risk_tier == RiskTier.HIGH
    assert result.premium_multiplier == pytest.approx(2.5)


# ---------------------------------------------------------------------------
# API-level validation (end-to-end through FastAPI)
# ---------------------------------------------------------------------------

def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_risk_car_endpoint_accepts_valid_payload():
    resp = client.post("/risk/car", json=VALID_CAR)
    assert resp.status_code == 200
    body = resp.json()
    assert body["premium_multiplier"] >= 0


def test_risk_car_endpoint_rejects_negative_vehicle_value():
    payload = {**VALID_CAR, "vehicle_value": -1}
    resp = client.post("/risk/car", json=payload)
    assert resp.status_code == 422


def test_risk_car_endpoint_rejects_inconsistent_license_years():
    payload = {**VALID_CAR, "driver_age": 18, "years_licensed": 10}
    resp = client.post("/risk/car", json=payload)
    assert resp.status_code == 422


def test_risk_home_endpoint_accepts_valid_payload():
    resp = client.post("/risk/home", json=VALID_HOME)
    assert resp.status_code == 200
    body = resp.json()
    assert body["premium_multiplier"] >= 0


def test_risk_home_endpoint_rejects_negative_property_value():
    payload = {**VALID_HOME, "property_value": -1}
    resp = client.post("/risk/home", json=payload)
    assert resp.status_code == 422


def test_risk_home_endpoint_rejects_roof_older_than_property():
    payload = {**VALID_HOME, "property_age": 5, "roof_age": 50}
    resp = client.post("/risk/home", json=payload)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# CLI self-test (--live-check)
# ---------------------------------------------------------------------------

def test_run_live_check_passes_with_sample_data():
    assert run_live_check() is True


def test_main_live_check_flag_exits_zero(monkeypatch):
    monkeypatch.setattr("sys.argv", ["insurance_risk_service.py", "--live-check"])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0
