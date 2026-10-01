"""Car & home insurance risk scoring service.

Run as an HTTP API:      python insurance_risk_service.py
Run a self-test and exit: python insurance_risk_service.py --live-check
"""
from __future__ import annotations

import argparse
import sys
from enum import Enum
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator

STATIC_DIR = Path(__file__).parent / "static"


class RiskTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RiskResult(BaseModel):
    risk_score: float = Field(..., ge=0, le=100)
    risk_tier: RiskTier
    premium_multiplier: float = Field(..., ge=0)


def _tier_for_score(score: float) -> RiskTier:
    if score < 34:
        return RiskTier.LOW
    if score < 67:
        return RiskTier.MEDIUM
    return RiskTier.HIGH


def _clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, value))


class CarQuote(BaseModel):
    driver_age: int = Field(..., ge=16, le=100)
    years_licensed: int = Field(..., ge=0, le=84)
    vehicle_age: int = Field(..., ge=0, le=60)
    annual_mileage: int = Field(..., ge=0, le=150_000)
    accidents_last_5yrs: int = Field(0, ge=0, le=20)
    claims_last_5yrs: int = Field(0, ge=0, le=20)
    vehicle_value: float = Field(..., gt=0, le=2_000_000)
    urban_area: bool = False

    @model_validator(mode="after")
    def _check_years_licensed(self) -> "CarQuote":
        max_possible = self.driver_age - 16
        if self.years_licensed > max_possible:
            raise ValueError(
                f"years_licensed ({self.years_licensed}) cannot exceed "
                f"driver_age - 16 ({max_possible})"
            )
        return self


def score_car_risk(q: CarQuote) -> RiskResult:
    score = 30.0

    if q.driver_age < 25:
        score += 20
    elif q.driver_age < 30:
        score += 8
    elif q.driver_age > 70:
        score += 6

    score -= min(q.years_licensed, 20) * 0.5
    score += min(q.vehicle_age, 15) * 0.6
    score += (q.annual_mileage / 15000) * 8
    score += q.accidents_last_5yrs * 12
    score += q.claims_last_5yrs * 10
    score += 5 if q.urban_area else 0

    score = _clamp(score)
    return RiskResult(
        risk_score=round(score, 1),
        risk_tier=_tier_for_score(score),
        premium_multiplier=round(0.6 + (score / 100) * 1.8, 2),
    )


class HomeQuote(BaseModel):
    property_age: int = Field(..., ge=0, le=300)
    square_footage: int = Field(..., gt=0, le=50_000)
    roof_age: int = Field(..., ge=0, le=300)
    claims_last_5yrs: int = Field(0, ge=0, le=20)
    security_system: bool = False
    flood_zone: bool = False
    fire_station_distance_km: float = Field(..., ge=0, le=100)
    property_value: float = Field(..., gt=0, le=50_000_000)

    @model_validator(mode="after")
    def _check_roof_age(self) -> "HomeQuote":
        if self.roof_age > self.property_age:
            raise ValueError(
                f"roof_age ({self.roof_age}) cannot exceed property_age ({self.property_age})"
            )
        return self


def score_home_risk(q: HomeQuote) -> RiskResult:
    score = 25.0

    score += min(q.property_age, 50) * 0.3
    score += min(q.roof_age, 30) * 0.5
    score += q.claims_last_5yrs * 12
    score += 18 if q.flood_zone else 0
    score += min(q.fire_station_distance_km, 20) * 0.8
    score -= 8 if q.security_system else 0
    score += (q.square_footage / 2000) * 3

    score = _clamp(score)
    return RiskResult(
        risk_score=round(score, 1),
        risk_tier=_tier_for_score(score),
        premium_multiplier=round(0.5 + (score / 100) * 2.0, 2),
    )


app = FastAPI(title="Insurance Risk Service")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/risk/car", response_model=RiskResult)
def risk_car(quote: CarQuote) -> RiskResult:
    return score_car_risk(quote)


@app.post("/risk/home", response_model=RiskResult)
def risk_home(quote: HomeQuote) -> RiskResult:
    return score_home_risk(quote)


# Registered last so it never shadows the API routes above: Starlette matches
# routes in registration order, and this Mount only catches what nothing else did.
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


def run_live_check() -> bool:
    """Exercise both scoring paths with sample data and sanity-check the output."""
    checks: list[tuple[str, bool]] = []

    try:
        car_result = score_car_risk(
            CarQuote(
                driver_age=19,
                years_licensed=1,
                vehicle_age=8,
                annual_mileage=18000,
                accidents_last_5yrs=1,
                claims_last_5yrs=0,
                vehicle_value=12000,
                urban_area=True,
            )
        )
        checks.append(("car risk scoring", car_result.risk_tier in (RiskTier.MEDIUM, RiskTier.HIGH)))
    except Exception as exc:  # noqa: BLE001
        print(f"[live-check] car scoring raised: {exc}")
        checks.append(("car risk scoring", False))

    try:
        home_result = score_home_risk(
            HomeQuote(
                property_age=5,
                square_footage=1800,
                roof_age=2,
                claims_last_5yrs=0,
                security_system=True,
                flood_zone=False,
                fire_station_distance_km=2.0,
                property_value=350000,
            )
        )
        checks.append(("home risk scoring", home_result.risk_tier == RiskTier.LOW))
    except Exception as exc:  # noqa: BLE001
        print(f"[live-check] home scoring raised: {exc}")
        checks.append(("home risk scoring", False))

    checks.append(("app routes registered", len(app.routes) >= 4))

    all_ok = all(ok for _, ok in checks)
    for name, ok in checks:
        print(f"[live-check] {name}: {'PASS' if ok else 'FAIL'}")

    return all_ok


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live-check",
        action="store_true",
        help="Run an in-process self-test of the risk models and exit (no server started).",
    )
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.live_check:
        healthy = run_live_check()
        sys.exit(0 if healthy else 1)

    import uvicorn  # pragma: no cover

    uvicorn.run(app, host=args.host, port=args.port)  # pragma: no cover


if __name__ == "__main__":  # pragma: no cover
    main()
