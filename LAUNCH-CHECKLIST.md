# Launch checklist

Do not launch until every "Must" item is done. Tick each box.

## Must (blocks launch)
- [ ] A lawyer has reviewed and approved terms, privacy, about, contact and accessibility text, and confirmed whether any insurance license is needed for what the site does (see LAWYER-QUESTIONS.md).
- [ ] Every `[[ ]]` placeholder is replaced (search all files for `[[`). Every statement on the About page is true for your organization.
- [ ] Data-reuse check: someone has read the terms of each source used (NerdWallet, Insurance.com, InsuranceQuotes, Bankrate, MoneyGeek, Insure.com, J.D. Power, LexisNexis, Insurify, etc.) and the site's use of their figures and downloads is allowed, or the figures are removed or replaced.
- [ ] A named person owns the site, monitors the contact email, and knows how to fix an error and how to take a page down quickly.
- [ ] The working name is cleared and replaced everywhere; a real domain is set; HTTPS is on.
- [ ] `robots.txt` and `sitemap.xml` use the real domain.
- [ ] The tool has been opened and used end to end in Safari and Firefox on a computer and on at least one iPhone and one Android phone: car flow, home flow, results, print, copy summary, Test tab, Trust and fairness tab. (Chromium at desktop and phone sizes was already tested; see README.)

## Should (do soon after, or before if you can)
- [ ] Screen reader test (VoiceOver on Mac/iPhone; NVDA on Windows) of the home page, one tool flow and the results. Update the accessibility statement with what you found.
- [ ] Keyboard-only walk-through of every tool screen; zoom to 200% and 400%.
- [ ] Deploy with the security headers in `_headers` (Netlify or Cloudflare Pages) or set the same headers at your host, then confirm the tool still works.
- [ ] Check the site with a free tool such as WebPageTest or Lighthouse and fix anything serious.
- [ ] Ask a licensed independent agent to read the tool's outputs for three or four realistic households and tell you what looks wrong.
- [ ] Collect real quotes in one pilot state (see the quote collection kit) and run the Test tab.
- [ ] Set up an error-report inbox and write down who replies within how many days (put that in the contact page).
- [ ] Decide whether you want analytics. If yes, choose a privacy-respecting tool, add it deliberately, and update the privacy policy BEFORE it goes live.

## Ongoing
- [ ] Quarterly: refresh prices and the "last updated" date; re-run the tool's tests and the link check.
- [ ] Yearly: refresh Oklahoma's official samples, minimum liability limits, claim sizes; review the legal pages.
- [ ] After any change to money or rules (ads, referrals, forms, accounts): legal review first.
- [ ] Keep a copy of every published version (a git repository is simplest).

## Things that would change the risk a lot
Adding ads, lead forms, "get a quote" buttons, referral or commission links, email capture, accounts, a chat assistant, or comparing named insurers' live prices. Each can trigger licensing, advertising, privacy or consumer-protection rules. Get advice before building any of them.
