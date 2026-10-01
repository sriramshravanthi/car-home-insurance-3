# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Implementation status

The sections below the `---` divider describe the intended product vision and AI-assistant behavior guidelines for a full USA car/home insurance platform. Two things now exist in this repo, served by the same FastAPI app:

1. **`insurance_risk_service.py`** — a FastAPI API (`POST /risk/car`, `POST /risk/home`, `GET /health`) returning a heuristic 0-100 risk score, low/medium/high tier, and premium multiplier. Fully unit-tested (`test_insurance_risk_service.py`).
2. **The "Coverage Check" static site** (`static/`) — a multi-page, fully client-side educational site (home, car, home-insurance, the full price+coverage `tool.html`, `compare.html` company-vs-company comparison, how-it-works, resources/downloads, sources, about, contact, terms, privacy, accessibility, 404) plus this repo's original single-page risk-score UI, now folded in at `static/quick-check/` as a lighter, API-backed companion tool. See `LAUNCH-CHECKLIST.md` and `LAWYER-QUESTIONS.md` at the repo root — **the Coverage Check site is explicitly not launch-ready**: it still contains `[[PLACEHOLDER]]` tokens (company name, contact email, effective dates, governing state) in about/contact/terms/privacy/accessibility, draft (not lawyer-reviewed) legal text, and a working name ("Coverage Check") that hasn't been cleared as a trademark. Do not remove those placeholders or the "DRAFT FOR LEGAL REVIEW" banners without the user explicitly signing off — they're deliberate guardrails, not stray text.

Still missing versus the full vision below: chat/conversational layer, discount finder, claims education module, carrier integrations, and five of the six AI modules under "Planned AI Modules" (Savings Opportunity AI, Coverage Gap AI, Personalized Question Generator, Renewal Analyzer, Policy Document Analyzer) — none of these have any code yet; they're notes for future scoping, not a build queue. `compare.html` (see its own section below) now covers the company-vs-company half of "Quote Comparison AI" and the "Policy Comparison Tool" vision section, using published third-party rate data — not live per-user quotes. The Coverage Check `tool.html` already covers a good chunk of premium estimation, coverage-gap checking, and state-benchmarked pricing that the vision describes — see its own `how-it-works.html` for method/testing/limits before assuming what it can and can't do.

## Commands

Install dependencies:
```
pip install -r requirements-dev.txt   # runtime deps + pytest, httpx, pytest-cov
```

Run the service:
```
python insurance_risk_service.py                  # starts uvicorn on 0.0.0.0:8000
python insurance_risk_service.py --host <h> --port <p>
```

Self-test without starting a server:
```
python insurance_risk_service.py --live-check      # exit 0 = healthy, exit 1 = failed
```

Run tests:
```
python -m pytest test_insurance_risk_service.py -v
python -m pytest test_insurance_risk_service.py -v -k test_car_score_baseline   # single test
```

Run tests with coverage (config in `.coveragerc`, scoped to `insurance_risk_service.py`):
```
python -m pytest --cov=insurance_risk_service --cov-report=term-missing --cov-report=html
```
Open `htmlcov/index.html` for the line-by-line report.

## Architecture (current code)

Single-module service (`insurance_risk_service.py`) — a FastAPI app plus a CLI entrypoint, no separate app/model layers:

- **Pydantic request models** (`CarQuote`, `HomeQuote`) hold all input validation: per-field `ge`/`le` bounds and `@model_validator(mode="after")` cross-field checks (e.g. `years_licensed` can't exceed `driver_age - 16`; `roof_age` can't exceed `property_age`). Add new input constraints here, not in the scoring functions.
- **Scoring functions** (`score_car_risk`, `score_home_risk`) are pure functions: additive point formulas starting from a base score, with `min(x, cap)` used to cap individual factors' contribution before the final `_clamp(score, 0, 100)`. Each factor's weight is a magic number inline in the formula — when changing a weight or cap, update the corresponding hand-computed expected values in the test file (tests assert exact scores, not just direction).
- **`RiskResult`** is the shared output shape for both domains (`risk_score`, `risk_tier` via `_tier_for_score` thresholds at 34/67, `premium_multiplier`); `premium_multiplier` is constrained `ge=0` as a defensive output check.
- **`run_live_check()`** exercises both scoring paths with hardcoded sample data and is what `--live-check` runs; it's meant as a fast smoke test (e.g. for deploy health checks), not a replacement for the pytest suite.
- `main()` is the only argparse/uvicorn wiring; `--live-check` short-circuits before uvicorn is ever imported, so the HTTP server has no runtime dependency for that path.
- **`app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")`** is registered last, after every `@app.get`/`@app.post` route, so it only serves paths the API routes don't claim — this is what makes `/`, `/car.html`, `/tool.html`, etc. resolve to files in `static/` while `/risk/car`, `/risk/home`, `/health` keep hitting the Python handlers. When adding a new API route, add it before this mount call, not after.

### Sitewide design layer: navy/professional (current, as of this session)

The site went through **two** visual directions this session. First a colourful "jewel-tone aurora" redesign (gradient text, animated aurora background, bobbing hero cards). The user then explicitly said they didn't like it, asked for `compare.html` to be built in a serious, professional "insurance comparison tool" tone instead (navy chrome, solid colors, no gradients/decorative animation), liked that direction, and asked for the rest of the site to be redone to match it. **The navy/professional system is current; nothing in the codebase should still look jewel-tone.** If you find gradient text (`background-clip:text`) or an aurora/grain background anywhere, that's a regression, not an intentional design choice.

Every top-level page except `quick-check/` (see below) loads `assets/home.css` and `assets/home.js` on top of the base `assets/site.css`:

- **`assets/site.css`** owns the fixed navy header/footer (`.sx-header`/`.sx-footer` are always dark navy — `var(--navy)` — regardless of the user's light/dark theme preference, like a masthead color; only the page *content* between them follows the theme) and all the plain `sx-` component classes (buttons, notes, cards, tables).
- **`assets/home.css`** is the marketing/section layer on top: the `cx-` prefixed hero/section classes (navy hero band restyled to match the header, stat counters, reveal-on-scroll cards, timeline, FAQ accordion, source ticker, persona quick-links, mobile sticky CTA). No markup changes were needed to re-skin the plain informational pages (`about.html`, `contact.html`, `terms.html`, `privacy.html`, `accessibility.html`, `how-it-works.html`, `resources.html`, `sources.html`, `404.html`) — linking the two files is enough, since `home.css` restyles the `sx-` classes directly.
- **Color system split, both files**: `--brand`/`--accent` is for TEXT (links, borders) against the page surface; `--brand-btn`/`--accent-btn` is for BUTTON BACKGROUNDS that carry white text on top. They're the same value in light mode (both are "vs white" checks) but diverge in dark mode — text wants a *brighter* blue against the dark surface, a button-with-white-text needs a *darker* one. **If you add a new button or dark-mode color anywhere in this system (including `tool.html` and `compare.html`, which each define their own copy of this split), pick the right one of the pair and verify contrast — don't assume one variable works for both.**
- **`tool.html`** and **`compare.html`** do *not* link `assets/home.css`/`site.css` — each is fully self-contained with its own embedded `<style>`, because their CSS variable names don't match the shared files' (cross-file `var()` references would silently resolve to nothing and drop rules). Each re-implements the same navy header/footer, the same brand/brand-btn split, and the same mobile-nav-toggle fix independently — keep the three copies in sync by eye if you change the shared look. Keep `tool.html`'s own font stack (`Atkinson Hyperlegible`, no Google Fonts) — it's a dense data-entry/results UI, not a marketing page, and loading fonts there would contradict the "runs in your browser, loads nothing else" claims specific to the tool (see `privacy.html`).
- **`quick-check/`** keeps its own distinct, already-animated "ledger/dossier" aesthetic (`quick-check/styles.css`, earth-tone rust/forest/ochre palette, stamp-drop and paper-grain effects) and was deliberately left alone through both redesigns — a different, self-contained bespoke design, not an oversight. It was *not* asked to be brought into the navy system; confirm with the user before doing so if that ever seems like the obvious next step.

Key constraint: **every `.reveal` element must be visible with `home.js` absent.** `home.js`'s first line adds a `.js` class to `<html>`; only `.js .reveal` gets `opacity:0` in CSS, so without JS nothing is hidden. Preserve this pattern for any new animated element — never make content's default (no-JS) state hidden. `.sx-nav-toggle` is `display:none` until `.js` is present, so without JS the full nav link list stays visible at every width — never a dead button.

All pages load Google Fonts (Fraunces, IBM Plex Mono) except `tool.html`, `compare.html`, and `quick-check/`; `privacy.html`'s third-party-loads disclosure reflects that split — update it if it changes.

**No more gradient text, anywhere.** The jewel-tone version used `background-clip:text` + `color:transparent` for the nav logo, `h1`s, and stat numbers. It's gone now (solid colors instead) for two reasons, not just taste: (1) it's incompatible with the navy/professional tone the user asked for, and (2) it was a real print bug — most browsers default the print dialog's "background graphics" setting to **off**, and `color:transparent` with no fallback prints as literally nothing. If you're tempted to add gradient text back, don't, and if you do anyway, you must also add a `@media print` override forcing a solid fallback color (every `@media print` block in this codebase already does this for the few places it's still structurally possible, like the navy hero backgrounds — see `assets/home.css`, `tool.html`, `compare.html`). Verify with computed styles, not just "a print rule exists": confirm via `getComputedStyle(el).color` under `Emulation.setEmulatedMedia({media:"print"})` that text actually resolves to a solid color — a rule can exist and still lose the cascade.

**Accessibility re-testing (2026-10-01, run after both redesigns and again after the navy rewrite):** axe-core 4.10.2 via CDP (not the DevTools panel) across every top-level page in both light and dark theme, plus 320/390/768/834/1280px reflow and simulated real-Tab-key keyboard-focus checks. Consistently zero violations after each pass. Issues found and fixed along the way: `.sx-note a` links outside `.sx-main` falling back to unreadable default blue in dark mode; two hero `<section>`s not contained by any landmark (fixed with `aria-label`); `quick-check/`'s header nav overflowing at 320px (no mobile collapse — added one); `quick-check/` missing a skip link entirely (added, matching its own palette); the gradient-text print bug above; and, when introducing the navy/professional system, two new button-background colors (`compare.html`'s `--accent-btn`, `tool.html`'s `.go`/`.tabs button`) that needed contrast fixes for dark mode. **Gotcha for next time:** if re-running this kind of scan, disable the Chrome HTTP cache per-tab (`Network.setCacheDisabled`) *before* navigating — the obvious approach (create tab via `/json/new?<url>`, which navigates immediately) serves a stale cached response on a second run against the same URL and silently hides fixes.

### Mobile nav toggle: plain `<button>`, not `<details>` — and a `justify-content` landmine

The header's mobile hamburger menu used to be a `<details class="sx-nav-details"><summary class="sx-nav-toggle">…</summary><ul>…</ul></details>`. It is now a plain `<button class="sx-nav-toggle" aria-expanded="…" aria-controls="sx-nav-menu">` immediately followed by `<ul id="sx-nav-menu">`, both direct children of `<nav class="sx-nav">`, with open/close state as a `.is-open` class on `.sx-nav` toggled by `assets/home.js` (click, outside-click, and Escape all close it). Do not revert this to `<details>`/`<summary>` — it was a deliberate fix, not a style preference:

- **Root cause, confirmed via 30+ isolated repros in Chrome 154**: `.sx-bar`'s `justify-content:space-between` (needed to push the nav to the right of the brand) silently drops a nested flex/grid/positioned descendant from painting *entirely* once the container is narrow enough that real free-space distribution has to happen — confirmed for `justify-content:space-between`, `margin:auto` on any sibling, `flex-grow` on any sibling, and CSS Grid's `fr` unit / `justify-self`. This is **not specific to `<details>`** (a plain `<button>` reproduces it identically) — the switch away from `<details>` fixes a *different*, separate bug (Chrome's newer `::details-content` mechanism additionally hides a closed `<details>`'s content even under the old `display:contents` escape hatch, which is what broke the *desktop* nav during this session before the mobile bug was even found). Two independent bugs, two independent fixes.
- **The actual fix**: `@media (max-width:860px){ .sx-bar{justify-content:flex-start} ... }` in `assets/site.css` — confirmed working via tablet-width testing (768/834/900px) on 2026-10-01: hamburger correctly shows below 860px, full horizontal nav correctly shows at/above it, no hidden links either way. Desktop keeps `space-between` — it was never actually broken there, since with enough available width the browser's incorrect internal sizing never becomes visually apparent. Only override it where the bug is visible.
  The three self-contained copies of this fix are kept in sync on this value by hand (no shared source — editing one does not update the others): `assets/site.css` (shared by every `sx-`-based page), `tool.html`'s embedded stylesheet (was `780px` until unified on 2026-10-01), and `compare.html`'s own `nav.main` collapse (was `900px` until unified on 2026-10-01) all now switch at `860px`. If you change the breakpoint in one, change it in all three or you'll reintroduce the mismatch.
- **If you touch `.sx-bar`, `.sx-nav`, or add anything else that needs to be pushed to the far edge of a flex row**: do not reach for `justify-content:space-between`/`margin:auto`/`flex:1` spacers at narrow viewports without re-testing at ~375–420px width in an actual current Chrome build (a headless screenshot is enough — DevTools' responsive-mode emulation did *not* reliably reproduce this in ad hoc testing, only a real viewport resize did). `flex-start` plus a fixed `gap` is safe; distribution is the trigger, not flexbox itself.
- No-JS fallback is unchanged in spirit: `.sx-nav-toggle` is `display:none` until `.js` is present (see `home.js`), so without JS the full link list stays visible at every width — never a dead button.

### `compare.html` — company-vs-company comparison, and its data-sourcing rule

Built after the user explicitly rejected fabricating per-user "GEICO quotes you $X" style numbers (no API/data-partner access exists for that, and doing it with invented numbers would be deceptive and contrary to the Core Principles above). Instead it ranks **named real companies by published third-party average rates** — every dollar figure traces to a specific source URL, publish date, and sample profile, stated both inline (`sourceBox()` in its script) and in its own "About these numbers" section. Data is hardcoded in `<script>` as `CAR_FULL`/`CAR_MIN`/`HOME`/`CAR_CATEGORIES`/`HOME_BUNDLE` objects — verified by fetching each source page directly (not trusting a search engine's AI summary of it) before writing the number in. **If you add or refresh a figure here, fetch the primary source page yourself and re-verify the exact number, sample profile and date** — don't propagate a secondhand summary.

This page is also where the navy/professional visual direction (see the design-layer section above) started, before the user asked for it site-wide — it's self-contained (own `<style>`, doesn't link `assets/*.css`) for the cross-file-`var()` reason noted above. Its header flex row uses `margin-left:auto` on the CTA, which is a trigger for the `justify-content` Chromium bug described below — neutralized the same way, `.bar .cta{margin-left:0}` inside its own `@media(max-width:900px)` block. Don't remove that override.

### Static site (`static/`)

- Top-level HTML/CSS/JS (`index.html`, `car.html`, `home.html`, `tool.html`, `compare.html`, `how-it-works.html`, `resources.html`, `sources.html`, `about.html`, `contact.html`, `terms.html`, `privacy.html`, `accessibility.html`, `404.html`, `assets/`, `downloads/`) is the "Coverage Check" educational site — fully static, no network calls, no cookies, no server-side dependency on `insurance_risk_service.py`'s Python logic. `tool.html` (~2000 lines) is a self-contained client-side car/home price + coverage estimator with its own pricing model (state medians/curves, described in `how-it-works.html`) — distinct from and more detailed than the API's heuristic risk score.
- `static/quick-check/` is this repo's original single-page tool: a lighter, API-backed risk-tier check that calls `POST /risk/car` / `POST /risk/home` directly. Keep it in sync with the Pydantic model constraints in `insurance_risk_service.py` if those change (min/max attributes are duplicated in `quick-check/index.html`'s `<input>` tags for UX, but the API is the source of truth for validation).
- Every Coverage Check page repeats the same nav/footer markup inline (no templating) — when adding a nav item, it needs to be added to each page's `<nav>` block individually (see how the "Quick check" link was added via a sed pass over the `Downloads</a></li>` string common to all of them).

### Testing conventions

`test_insurance_risk_service.py` uses FastAPI's `TestClient` for endpoint-level (HTTP status code) tests, and calls `score_car_risk`/`score_home_risk` directly for formula-level tests. Formula tests hand-compute the expected score from the source formula for a given input rather than re-deriving it programmatically — when adding a scoring factor, add both a hand-computed test case and a "capped" test case if the factor has a `min(x, cap)`.

---
 
## Project Overview
 
This project is a USA Car and Home Insurance Platform that helps individuals compare insurance options, estimate premiums, understand coverage, identify discounts, and make informed insurance decisions.
 
The platform is designed for:
 
- Homeowners
- Renters
- Vehicle Owners
- Families
- First-time Insurance Buyers
- Insurance Advisors
- Financial Planners
 
Primary goals:
 
1. Explain insurance concepts in simple language.
2. Compare insurance carriers and coverage options.
3. Provide educational guidance.
4. Estimate premiums using user inputs.
5. Identify available discounts.
6. Recommend suitable coverage levels.
7. Improve insurance literacy.
8. Support policy review and renewal decisions.
 
---
 
# Core Principles
 
1. Always provide educational guidance only.
2. Never claim to be a licensed insurance agent.
3. Do not sell insurance policies.
4. Do not guarantee premium pricing.
5. Clearly state estimates may vary by insurer.
6. Explain assumptions used in calculations.
7. Use plain English whenever possible.
8. Ensure information is relevant to U.S. insurance practices.
9. Encourage users to verify details with licensed professionals.
10. Maintain data privacy and security.
 
---
 
# User Personas
 
## Car Insurance Customers
 
- First-time drivers
- Teen drivers
- Families
- Senior drivers
- High-risk drivers
- Rideshare drivers
 
## Home Insurance Customers
 
- Homeowners
- Condo Owners
- Renters
- Landlords
- Vacation Property Owners
 
---
 
# Car Insurance Module
 
## Collect User Information
 
- State
- ZIP Code
- Age
- Marital Status
- Vehicle Make
- Vehicle Model
- Vehicle Year
- Annual Mileage
- Driving History
- Current Insurance Status
 
## Coverage Types
 
### Liability Coverage
 
Explain:
 
- Bodily Injury Liability
- Property Damage Liability
 
### Collision Coverage
 
Explain:
 
- Covered situations
- Deductibles
- Claim examples
 
### Comprehensive Coverage
 
Explain:
 
- Theft
- Fire
- Vandalism
- Natural disasters
- Animal collisions
 
### Personal Injury Protection
 
Explain:
 
- Medical expenses
- Lost wages
- State eligibility
 
### Uninsured Motorist Coverage
 
Explain:
 
- Benefits
- Coverage situations
 
---
 
# Home Insurance Module
 
## Property Information
 
Gather:
 
- Property Type
- Home Value
- Year Built
- Square Footage
- State
- ZIP Code
- Security Features
 
## Coverage Categories
 
### Dwelling Coverage
 
Protects:
 
- Structure
- Attached garages
- Built-in systems
 
### Other Structures
 
Examples:
 
- Detached garages
- Sheds
- Fences
 
### Personal Property
 
Examples:
 
- Electronics
- Furniture
- Clothing
 
### Loss of Use
 
Explain:
 
- Temporary housing expenses
- Food expenses
 
### Personal Liability
 
Explain:
 
- Lawsuits
- Injuries occurring on property
 
---
 
# Premium Estimation Engine
 
Estimate premiums based on:
 
## Car Insurance Factors
 
- Driver Age
- Location
- Vehicle Type
- Credit Factors (where applicable)
- Driving Record
- Coverage Limits
- Deductibles
 
## Home Insurance Factors
 
- Property Value
- Construction Type
- Home Age
- ZIP Code
- Claims History
- Security Systems
- Coverage Selection
 
Display:
 
- Low estimate
- Average estimate
- High estimate
 
Include disclaimer:
 
"Premium estimates are educational only and are not official insurance quotes."
 
---
 
# Discount Finder
 
## Auto Insurance Discounts
 
Check eligibility for:
 
- Safe Driver
- Multi-Car
- Bundling
- Good Student
- Defensive Driving Course
- Low Mileage
- Military
- Senior Driver
 
## Home Insurance Discounts
 
Check eligibility for:
 
- Bundling
- Security Alarms
- Smart Home Devices
- New Home
- Claims-Free History
- Fire Protection Systems
 
---
 
# Policy Comparison Tool
 
Compare:
 
- Coverage Limits
- Deductibles
- Estimated Premiums
- Key Benefits
- Potential Exclusions
 
Output should include:
 
- Similarities
- Differences
- Best Value Analysis
 
---
 
# Risk Assessment Module
 
Assess:
 
## Auto Risks
 
- Vehicle Theft Exposure
- Accident Risk
- Weather Exposure
 
## Home Risks
 
- Flood Risk
- Fire Risk
- Storm Risk
- Theft Risk
 
Provide educational recommendations only.
 
---
 
# Coverage Recommendation Engine
 
Provide:
 
### Budget Option
 
Lower premium focus.
 
### Balanced Option
 
Coverage and affordability.
 
### Premium Protection Option
 
Maximum protection focus.
 
Explain reasoning clearly.
 
---
 
# Insurance Education Center
 
Explain:
 
## Car Insurance
 
- Liability
- Collision
- Comprehensive
- Deductibles
- Claims Process
 
## Home Insurance
 
- Dwelling
- Liability
- Replacement Cost
- Actual Cash Value
- Claims Process
 
Keep explanations beginner-friendly.
 
---
 
# State-Specific Guidance
 
When state information is available:
 
- Explain required minimum coverages.
- Explain relevant insurance rules.
- Highlight important state considerations.
 
Never provide legal advice.
 
---
 
# Claims Education Module
 
Provide education on:
 
- Filing a claim
- Required documentation
- Common claim mistakes
- Typical claim workflow
 
Do not guarantee claim approval.
 
---

# Planned AI Modules (Not Yet Implemented)

Not yet implemented -- notes captured for future scoping/planning, not a build queue. All would still need to comply with the Core Principles, Compliance Notes, and AI Response Guidelines below (educational only, no guarantees, no premium promises, encourage professional verification).

## Quote Comparison AI

Compare policy information across quotes: coverage limits, deductibles, estimated premiums, key benefits, potential exclusions. Overlaps with the existing "Policy Comparison Tool" section above -- scope these together rather than as separate features.

## Savings Opportunity AI

Identify possible savings opportunities for the consumer (e.g. underused discounts, coverage mismatches driving cost). Overlaps with the existing "Discount Finder" section above.

## Coverage Gap AI

Identify potential areas the consumer should discuss with a licensed professional -- gaps between current coverage and typical/recommended coverage. Educational flag only, never a substitute for professional review.

## Personalized Question Generator

Generate a tailored list of questions the consumer should ask their insurer or agent, based on their collected inputs (state, property/vehicle details, coverage selections, etc.).

## Renewal Analyzer

Analyze a renewal notice against the consumer's previous policy: what changed (premium, deductible, limits, endorsements) and flag changes worth understanding before renewing.

## Policy Document Analyzer

Allow users to upload a policy document and extract/identify:

- Premium
- Deductible
- Coverage limits
- Major exclusions
- Endorsements
- Changes from the previous policy (if a prior version is also provided)

Would require document upload/parsing -- currently out of scope for the fully static, no-server-side-processing Coverage Check site; any implementation needs a decision on where parsing happens (client-side only vs. a new backend endpoint) before scoping further.

---
 
# AI Response Guidelines
 
Always:
 
1. Be fact-based.
2. Explain assumptions.
3. Use simple terms.
4. Mention limitations.
5. Show calculations when applicable.
6. Highlight uncertainties.
7. Encourage professional verification.
 
Never:
 
- Guarantee savings.
- Guarantee approvals.
- Promise premium amounts.
- Misrepresent regulations.
- Act as an insurance carrier.
 
---
 
# Compliance Notes
 
The platform:
 
- Does not issue policies.
- Does not bind coverage.
- Does not provide legal advice.
- Does not provide financial advice.
- Does not replace licensed insurance professionals.
 
All outputs are educational and informational only.
 
---
 
# Preferred Response Structure
 
1. User Objective
2. Collected Inputs
3. Coverage Analysis
4. Risk Assessment
5. Premium Estimate
6. Discount Opportunities
7. Coverage Recommendations
8. Key Considerations
9. Disclaimer
 
Keep responses professional, concise, accurate, and easy for U.S. consumers to understand.