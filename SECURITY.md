# Security Policy

## Scope

This is a small, mostly solo-maintained educational project — not a production
service handling real user data. In scope for a security report:

- `insurance_risk_service.py` (the FastAPI API: `/risk/car`, `/risk/home`, `/health`,
  and the static-file mount) — e.g. input validation bypasses, injection, path
  traversal through the static file serving, or anything that could affect the host
  it's running on.
- The client-side site in `static/` — e.g. XSS in any page that renders user input.

Out of scope: the accuracy of insurance pricing/coverage content itself (that's a
content issue, not a security one — see `LAUNCH-CHECKLIST.md`), and the known,
intentional `[[PLACEHOLDER]]` tokens and draft legal text.

## Supported versions

There are no released versions — only the latest commit on `master` is maintained.
Please report issues against that.

## Reporting a vulnerability

Please **do not** open a public GitHub issue for a security vulnerability.

Instead, report it privately via
[GitHub Security Advisories](https://github.com/sriramshravanthi/car-home-insurance-3/security/advisories/new)
for this repo, or by contacting the maintainer
([@sriramshravanthi](https://github.com/sriramshravanthi)) directly.

Please include:

- A description of the issue and its potential impact.
- Steps to reproduce (or a proof of concept).
- Which part of the project it affects (API or static site).

This is a side project maintained in spare time, so there's no guaranteed response
time, but reports will be looked at and a fix or mitigation will be prioritized based
on severity.
