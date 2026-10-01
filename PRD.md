# Product Requirements Document — USA Car & Home Insurance Platform

**Status:** Draft
**Owner:** _TBD_
**Last updated:** 2026-09-29

## 1. Summary

A platform that helps individuals compare insurance options, estimate premiums, understand coverage, identify discounts, and make informed car/home insurance decisions. The platform provides educational guidance only — it does not sell policies, bind coverage, or act as a licensed insurance agent (see [Section 9](#9-compliance--legal-guardrails)).

## 2. Problem Statement

_TBD — describe the gap this fills (e.g. "Consumers shopping for car/home insurance struggle to compare coverage types and estimate realistic premiums without a licensed agent")._

## 3. Goals & Success Metrics

| Goal | Metric | Target |
|---|---|---|
| Explain insurance concepts in plain language | _TBD_ | _TBD_ |
| Estimate premiums from user inputs | _TBD_ | _TBD_ |
| Identify available discounts | _TBD_ | _TBD_ |
| Improve insurance literacy | _TBD_ | _TBD_ |

## 4. Target Users

**Car insurance:** first-time drivers, teen drivers, families, senior drivers, high-risk drivers, rideshare drivers.
**Home insurance:** homeowners, condo owners, renters, landlords, vacation property owners.
**Other personas:** insurance advisors, financial planners.

## 5. Scope

### 5.1 In scope for MVP (currently implemented)

**API (`insurance_risk_service.py`):**
- `POST /risk/car` — car risk scoring from driver age, license years, vehicle age, mileage, accident/claims history, urban/rural. Returns a 0-100 risk score, low/medium/high tier, and a premium multiplier.
- `POST /risk/home` — home risk scoring from property age, square footage, roof age, claims history, security system, flood zone, fire station distance. Returns the same result shape.
- Input validation: field-level range checks plus cross-field consistency checks (e.g. years licensed vs. driver age, roof age vs. property age).
- `/health` endpoint and a `--live-check` CLI self-test for deploy verification.

**Website ("Coverage Check", `static/`)** — a multi-page educational site, fully client-side, no ads/forms/accounts/tracking:
- Home, car, and home-insurance landing pages with sourced statistics (state price ranges, underinsurance rates, claim sizes) and links to sources.
- `tool.html` — the main interactive tool: state-benchmarked car and home price estimates (with a typical range and percentile), a coverage-gap stress test (fire, wind/hail, hurricane, burst pipe, theft, liability, flood, earthquake), a "test with real quotes" tab, and a "trust and fairness" tab (model card, controls register). Its own pricing model and validation-against-real-insurer-prices are documented in `how-it-works.html`.
- `resources.html` — downloadable Excel workbook, reports, quote-collection kits, and the raw Oklahoma Insurance Department benchmark data used to validate the model.
- `sources.html` — every data source cited, with links.
- `about.html`, `contact.html` — **placeholders**, not complete (see 9.1 below).
- `terms.html`, `privacy.html`, `accessibility.html` — **drafts for lawyer review**, not final.
- `static/quick-check/` — this project's original lighter tool: calls the `/risk/car` / `/risk/home` API directly for an instant risk-tier check, linked from the main site's nav as "Quick check".

See `CLAUDE.md` for exact commands and architecture, and `LAUNCH-CHECKLIST.md` / `LAWYER-QUESTIONS.md` (repo root) for what's still required before this can go live publicly.

### 5.2 Planned / out of scope for MVP

These are described conceptually in `CLAUDE.md`'s product-vision section but **not yet built**:

- Conversational/chat interface
- Discount Finder (auto: safe driver, multi-car, bundling, good student, defensive driving, low mileage, military, senior; home: bundling, security alarms, smart home devices, new home, claims-free, fire protection)
- Policy Comparison Tool as a distinct feature (coverage limits, deductibles, premiums, benefits, exclusions → similarities/differences/best-value analysis) — `tool.html`'s stress test covers a related but narrower need (what one policy pays across scenarios)
- Claims Education Module beyond the general education already on `car.html`/`home.html`
- Carrier comparison / real quote integration (explicitly excluded by the Coverage Check site's own launch checklist as a licensing/advertising risk without legal review first)

## 6. Functional Requirements

### 6.1 Risk assessment (implemented)

- Collect car inputs: driver age, years licensed, vehicle age, annual mileage, accident/claim history, urban/rural, vehicle value.
- Collect home inputs: property age, square footage, roof age, claims history, security system, flood zone, distance to fire station, property value.
- Reject invalid/inconsistent inputs with a clear error rather than silently producing a nonsensical score.
- Return an estimated risk tier and premium multiplier, not a bound/official quote.

### 6.2 Premium estimation (planned)

- Display low / average / high estimate ranges, not a single number.
- Always show the disclaimer: _"Premium estimates are educational only and are not official insurance quotes."_
- Explain which inputs drove the estimate.

### 6.3 Discount finder (planned)

- Check eligibility against the discount list in [5.2](#52-planned--out-of-scope-for-mvp) given the same inputs already collected for risk/premium.

### 6.4 Policy comparison (planned)

- Accept 2+ policies/quotes as input and output a structured similarities/differences/best-value comparison.

### 6.5 Education & guidance (planned)

- Plain-language explanations of coverage types, keyed to the user's stated insurance type (car/home) and, where available, state.

## 7. Non-Functional Requirements

- **Explainability:** every estimate/recommendation states its assumptions and that results may vary by insurer.
- **Validation:** reject out-of-range or logically inconsistent inputs at the API boundary (see `insurance_risk_service.py` Pydantic models).
- **Testability:** scoring formulas and validation rules covered by unit tests with hand-computed expected values (see `test_insurance_risk_service.py`); target ≥90% coverage on the scoring module.
- **Deployability:** `--live-check` must pass before a deploy is considered healthy.

## 8. User Flows (high level)

_TBD — sequence diagrams or step lists for: (1) get a car risk estimate, (2) get a home risk estimate, (3) compare two policies, (4) find applicable discounts._

## 9. Compliance & Legal Guardrails

The platform must never:

- Claim to be a licensed insurance agent, or act as an insurance carrier.
- Sell policies or bind coverage.
- Guarantee premium pricing, savings, or claim approval.
- Provide legal or financial advice, or misrepresent state regulations.

The platform must always:

- Present estimates as educational, with assumptions stated and a disclaimer shown.
- Encourage users to verify details with a licensed professional.
- Maintain data privacy and security for any inputs collected.

### 9.1 Launch blockers (Coverage Check site specifically)

The site as implemented is a first version, not launch-ready. Tracked in full in `LAUNCH-CHECKLIST.md` and `LAWYER-QUESTIONS.md` at the repo root; the highlights:

- **Legal review not done.** Terms, privacy, and accessibility pages are explicitly marked "DRAFT FOR LEGAL REVIEW — DO NOT PUBLISH AS WRITTEN." A lawyer must also confirm whether any insurance producer/consultant license is required for what the tool does.
- **`[[PLACEHOLDER]]` tokens remain** in about.html, contact.html, terms.html, privacy.html, and accessibility.html (company name, address, contact email, effective date, governing state, minimum ages). Search for `[[` before publishing — no page is ready while any remain.
- **"Coverage Check" is a working name**, not cleared as a trademark.
- **Data-reuse terms not checked** for third-party sources (NerdWallet, Insurance.com, Bankrate, MoneyGeek, etc.) whose figures are reproduced in the site and downloads.
- **Cross-browser/device/screen-reader testing not done** — only Chromium desktop/tablet/phone sizes were tested; Safari, Firefox, real phones, and screen readers were not.
- Do not add ads, lead-capture forms, "get a quote" buttons, referral/commission links, or accounts without a legal review first — each changes the licensing/advertising exposure per `LAUNCH-CHECKLIST.md`.

## 10. Open Questions

- Who are the initial target states/markets for the state-specific guidance module?
- Should the API's simple 0-100 heuristic risk score (`quick-check`) and `tool.html`'s state-benchmarked dollar pricing model be reconciled into one model, or deliberately kept as two different-depth tools (quick check vs. full check)?
- Is a conversational (chat) interface required for MVP+1, or does the existing form-based UI (both the quick check and `tool.html`) suffice?
- Success metrics and target numbers in [Section 3](#3-goals--success-metrics) need input from the product owner.
- Who is the named owner for the live site, and what's the incident/correction process? (`tool.html`'s own model card flags this as missing.)

## 11. References

- `CLAUDE.md` — technical architecture, commands, and the full AI-assistant behavior/response-structure spec this product is meant to follow.
- `LAUNCH-CHECKLIST.md`, `LAWYER-QUESTIONS.md` — pre-launch requirements and the question list to bring to counsel.
