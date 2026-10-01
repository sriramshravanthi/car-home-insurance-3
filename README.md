# Coverage Check — Car & Home Insurance

An educational USA car/home insurance platform: a static, client-side "Coverage Check"
website plus a small FastAPI risk-scoring API, served together from one app.

**Status: not launch-ready.** The site still contains `[[PLACEHOLDER]]` tokens (company
name, contact email, effective dates, governing state) and draft, not-lawyer-reviewed
legal text in `about.html`, `contact.html`, `terms.html`, `privacy.html`, and
`accessibility.html`. See `LAUNCH-CHECKLIST.md` and `LAWYER-QUESTIONS.md` before
deploying this anywhere real.

## What's here

- **`insurance_risk_service.py`** — a FastAPI API (`POST /risk/car`, `POST /risk/home`,
  `GET /health`) that returns a heuristic 0–100 risk score, a low/medium/high tier, and
  a premium multiplier. Fully unit-tested in `test_insurance_risk_service.py`.
- **`static/`** — the "Coverage Check" site: a multi-page, fully client-side educational
  site (home, car, home insurance, the full price + coverage `tool.html`, the
  company-vs-company `compare.html`, how-it-works, downloads, sources, about, contact,
  terms, privacy, accessibility, 404), plus a lighter API-backed companion tool at
  `static/quick-check/`.

Every dollar figure in `compare.html` is a published third-party average (NerdWallet,
Insurance.com, the Oklahoma Insurance Department's official filings), each traced to a
source URL, publish date, and sample profile — not a live per-user quote. See
`compare.html`'s own "About these numbers" section and `how-it-works.html` for method,
testing, and limits.

## Quick start

Install dependencies:

```
pip install -r requirements-dev.txt
```

Run the service (serves the API and the static site together):

```
python insurance_risk_service.py
python insurance_risk_service.py --host <h> --port <p>
```

Then open `http://localhost:8000/` in a browser.

Self-test without starting a server:

```
python insurance_risk_service.py --live-check
```

## Tests

```
python -m pytest test_insurance_risk_service.py -v
python -m pytest --cov=insurance_risk_service --cov-report=term-missing --cov-report=html
```

Open `htmlcov/index.html` for the line-by-line coverage report.

## Project docs

- **`CLAUDE.md`** — architecture notes, design-system details, and known browser
  quirks/fixes for anyone (human or AI) working on this codebase.
- **`PRD.md`** / **`TASKS.md`** — product scope and task tracking.
- **`LAUNCH-CHECKLIST.md`** / **`LAWYER-QUESTIONS.md`** — what's left before this could
  go live.

## License

MIT — see [`LICENSE`](LICENSE). Code only: this covers the FastAPI service and the
site's HTML/CSS/JS, not an endorsement of the insurance content itself, which is
educational and still has draft/placeholder sections (see "Status" above).
