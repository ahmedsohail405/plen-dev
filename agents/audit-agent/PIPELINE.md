# Plen Dev: automated website audit + SEO agent

> **Update 2026-11-17 (Ahmed):** Plen Dev only sells new websites, never fixes. The audit is now a deep audit
> (9 areas, 68 checks incl. security, conversion & trust, design/technology age, accessibility/ADA) in
> `audit.py` + `deep_checks.py`. Client copy shows "what we found" + "what it costs you" (the `impact` field),
> never how to fix; the report adds a "why rebuild instead of patching" section (`rebuild_case`). Emails are
> signed "Alex H, Sales, Plen Dev" and offer 2-3 free homepage concepts on reply. After Ahmed approves and the
> email sends, `server.handoff_to_alex()` passes the lead to Alex (`alex/store.import_inbound`), which handles
> replies, demo designs (Ahmed approves each) and WhatsApp forwarding. SEO agent (section 8) is on hold.

Status: audit engine, webhook server, approval queue and email sender are built and tested end to end locally (dry-run sending). Nothing is deployed, no API keys are used, and no real email has been sent.

## 1. Flow

```
Plen Dev site "Free website audit" form
   -> Payload CMS saves lead (type=website_audit)
   -> CMS afterChange hook POSTs signed webhook  ->  audit server /webhooks/lead
   -> audit runs (crawl up to 15 pages + Google PageSpeed + 35 checks)   ~30-90 s
   -> report.html + email draft saved, CMS lead -> audit_status=awaiting_approval
   -> Ahmed is notified (Slack/Discord ping and/or this Claude project)
   -> Ahmed approves (optionally adds a personal line / edits subject)
   -> email sent from Ahmed's domain, CMS lead -> audit_status=sent
   -> if client books a call / signs: SEO agent starts on their site
```

`AUTO_SEND=true` skips approval. Recommended: keep approval on for the first ~20 audits, then switch.

## 2. What the audit checks (audit.py)

| Category (weight) | Checks |
|---|---|
| Technical SEO (25) | site reachable, HTTPS + http->https redirect, robots.txt (and not blocking all), XML sitemap, soft 404s, broken internal links, noindex pages, canonical tags, mixed content, mobile viewport, analytics installed |
| On-page SEO (20) | missing/long/short/duplicate titles, meta descriptions, H1 missing/multiple, thin content (<300 words), image alt text, Open Graph tags |
| Speed & Core Web Vitals (20) | Google PageSpeed mobile + desktop: performance score, LCP, CLS, TBT, top opportunities (falls back to response time/page weight when PageSpeed is unavailable; the category is left out of the score rather than faked) |
| Local SEO (15) | LocalBusiness/Organization schema, phone shown + click-to-call, street address, Google Map embed, html lang |
| AI search readiness (10) | /llms.txt, AI crawlers (GPTBot, ClaudeBot, PerplexityBot, Google-Extended) blocked in robots.txt, structured data present, FAQ schema, content visible without JavaScript |
| Lead conversion (10) | call to action above the fold, contact/quote form, favicon |

Each finding has severity (critical/high/medium/low), plain-English "why it matters" and "how to fix", and affected pages. Score = 100 minus severity points per category, weighted into an overall 0-100 and a letter grade.

## 3. Files

| File | Purpose |
|---|---|
| `audit.py` | crawler + checks + scoring + rendering; also a CLI: `python3 audit.py https://site.com --name Dana --email d@x.com --out ./outbox/test` |
| `server.py` | webhook receiver, job queue, approval API, public report links, CMS write-back, notifications |
| `mailer.py` | sending via `dryrun` (default), Resend, Postmark or SMTP (Google Workspace / M365) |
| `templates/email.html.j2`, `email.txt.j2` | the client email (HTML + plain text) |
| `templates/report.html.j2` | full report, hosted at an unguessable `/r/<token>` link, printable to PDF |
| `.env.example` | every setting |
| `samples/` | sample email + report for a fictional Brooklyn dentist |

Security: webhook is HMAC-SHA256 signed, admin endpoints need a bearer token, report links are random 24-char tokens, and submitted URLs that resolve to private/internal IPs are refused (SSRF guard). Duplicate webhooks for the same lead are ignored.

## 4. Lead contract with the CMS (agreed with the site thread)

Webhook `POST {AUDIT_WEBHOOK_URL}` header `X-PlenDev-Signature: sha256=<HMAC of raw body>`:

```json
{"event":"lead.created","lead":{"id":"...","type":"website_audit","created_at":"ISO8601",
 "name":"","email":"","phone":"","company":"","website_url":"","industry":"","message":"",
 "source_page":"/free-website-audit","utm":{"source":"","medium":"","campaign":""},"consent_marketing":true}}
```

Lead fields the audit server writes back via `PATCH /api/leads/:id` (Bearer CMS_API_TOKEN): `audit_status` (queued|auditing|awaiting_approval|approved|sent|failed), `audit_score`, `audit_report_url`, `audit_sent_at`, `audit_notes`.

## 5. Approval API

```
GET  /admin/audits?status=awaiting_approval
GET  /admin/audits/<lead_id>/email                 (preview)
POST /admin/audits/<lead_id>/approve   {"subject":"optional","note":"optional personal line"}
POST /admin/audits/<lead_id>/reject    {"reason":"spam"}
POST /admin/audits/<lead_id>/rerun
```

The CMS lead screen can show "Preview / Approve & send / Reject" buttons that call these (site thread), so Ahmed can approve from his phone.

## 6. Getting audits "into this chat"

Options (needs Ahmed's OK, since each creates a scheduled job or uses an account):
- **A. Claude routine (recommended):** a scheduled task in this project runs every 15-30 min, calls `GET /admin/audits?status=awaiting_approval`, posts each new audit here with score, top issues and preview link, and sends it when Ahmed replies "approve".
- **B. Slack/Discord ping** via `NOTIFY_WEBHOOK_URL`, approve in the CMS.
- **C. Both.**

## 7. Hosting

Any small always-on host works: Railway/Render/Fly.io (~$5/mo), or a $6 DigitalOcean droplet. It can also run as a Next.js API route + background job next to the Payload site, but crawling 15 pages + PageSpeed takes up to 90 s, which is too long for Vercel's default function limits, so a separate small service is simpler.

`pip install -r requirements.txt && python3 server.py`

## 8. SEO agent (phase 2, after a client signs)

Goal: rank the client's site for "<service> in <neighborhood/borough>" terms as fast as possible. Runs as a Claude agent per client with these jobs:

1. **Onboard (day 1):** read the audit, connect Google Search Console + GA4 + Google Business Profile (client grants access), pull current rankings/impressions, pick 10-30 target keywords (service x location: Brooklyn, Queens, Manhattan, Long Island neighborhoods).
2. **Fix technical issues (week 1):** turn every critical/high audit finding into a task; if the site is on Plen Dev's CMS it edits directly, otherwise opens a PR (GitHub) or produces a fix list for WordPress/Shopify/Wix.
3. **On-page (weeks 1-2):** rewrite titles/meta/H1s per target keyword, add LocalBusiness + Service + FAQPage schema, internal links, llms.txt.
4. **Content (weekly):** one location or service page / blog post per week targeting a keyword gap, with FAQ blocks AI tools can quote. Drafts go to Ahmed (or client) for approval before publishing.
5. **Local (ongoing):** Google Business Profile posts weekly, review-request email template, NAP consistency checks across directories (Yelp, BBB, Apple Maps, Bing Places).
6. **Report (monthly):** re-run the audit, compare scores, rankings and leads, email the client a progress report (same approval flow).

Tooling it needs: Search Console API, GA4 Data API, Google Business Profile API, PageSpeed API, optionally a rank-tracking API (DataForSEO ~$0.0006/keyword check or SerpApi), and CMS/GitHub write access per client. Each is an account Ahmed has to create or the client has to grant, so this phase starts once the first client signs.

## 9. Decisions (Ahmed, 2026-11-17)

- Ahmed approves every audit email before it sends (AUTO_SEND=false).
- Sender: an agent mailbox Ahmed is creating on the Plen Dev domain. Replies and contact go to info@plendev.com. Phone gets added later (phone lines hide while it's empty).
- New audits come to Ahmed in this Claude project for approval (option A in section 6).
- Email pitch is web development (fix or rebuild), not ongoing SEO. The SEO agent in section 8 is on hold until Ahmed confirms he wants it.

Still open: hosting for the audit server, business address for the footer (required before going live), PageSpeed API key, and the agent mailbox's sending setup (SMTP or Resend).
