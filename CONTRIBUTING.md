# Contributing

Thanks for taking a look at this project. It's a small, mostly solo-maintained
educational site + API, so the process here is intentionally lightweight.

## Before you start

- Read `CLAUDE.md` first — it has the architecture notes, the current design system,
  and a few real browser bugs (with their fixes) that are easy to accidentally
  reintroduce if you're not aware of them.
- Check `LAUNCH-CHECKLIST.md` and `LAWYER-QUESTIONS.md` for context on what's still
  unfinished. The `[[PLACEHOLDER]]` tokens and "DRAFT FOR LEGAL REVIEW" banners in
  `about.html`, `contact.html`, `terms.html`, `privacy.html`, and `accessibility.html`
  are deliberate guardrails, not stray text — please don't remove them in a PR.
- For anything beyond a small fix, open an issue first to discuss the approach before
  writing code.

## Making a change

1. Fork the repo and create a branch off `master`.
2. Make your change. A few conventions worth knowing:
   - **`insurance_risk_service.py`**: input validation belongs in the Pydantic models
     (`CarQuote`/`HomeQuote`), not the scoring functions. Scoring functions are pure,
     additive-formula functions — if you change a weight or cap, update the
     corresponding hand-computed expected values in
     `test_insurance_risk_service.py` (tests assert exact scores, not just direction).
   - **`static/`**: every page repeats its own nav/footer markup inline (no
     templating), so a sitewide nav change has to be applied to each page
     individually. `assets/site.css`/`assets/home.css` are shared by most pages;
     `tool.html` and `compare.html` are self-contained with their own embedded
     styles for the reasons explained in `CLAUDE.md` — keep the three copies of the
     mobile-nav-toggle fix in sync if you touch it.
   - **`compare.html`**: any dollar figure must trace to a real, verified source
     (fetch the primary page yourself, don't propagate a secondhand summary) with a
     URL, publish date, and sample profile. No fabricated or estimated per-user
     quotes — see `CLAUDE.md` for why.
3. Run the tests before opening a PR:
   ```
   python -m pytest test_insurance_risk_service.py -v
   ```
4. For any UI change, check it in an actual browser at mobile (~375px), tablet
   (~768–860px), and desktop widths — not just DevTools' responsive-mode emulation,
   which has been unreliable for at least one real bug in this codebase (see
   `CLAUDE.md`'s `justify-content` write-up).
5. Open a PR describing what changed and why. Keep the "educational only, not an
   insurance quote" framing intact in anything user-facing — see the Core Principles
   in `CLAUDE.md`.

## Reporting a bug

Open an issue with: what you expected, what happened instead, your browser/OS if it's
a rendering issue, and steps to reproduce. For a visual bug, a screenshot helps a lot.
