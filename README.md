# Plen Dev: agency site + CMS

Next.js 16 (App Router) + Payload CMS 3. SQLite locally, Postgres on Vercel.

## Run locally
```bash
pnpm install
cp .env.example .env        # fill in secrets
SEED_ADMIN_EMAIL=you@x.com SEED_ADMIN_PASSWORD=... pnpm seed
pnpm dev                    # http://localhost:3000, CMS at /admin
```

## What the CMS does
- **Pages, Portfolio, Packages, Blog**: drafts, autosave and live preview.
- **Leads**: every form submission (contact, quote, website audit) is stored. Audit leads start as `audit_status: queued`.
- **Site Settings**: business info, SEO defaults (GA4, GTM, Meta Pixel, verification), header/body code snippets site-wide or scoped to pages or path globs, AI crawler settings and llms.txt facts, lead webhook URL.
- **Per page/post**: SEO title/description/image, canonical, noindex, keywords, schema type, custom JSON-LD, custom code snippets.
- AI-friendly: `/llms.txt`, `/llms-full.txt`, `robots.txt` that allows AI bots, `sitemap.xml`, JSON-LD on every page.

## Audit agent integration
1. A new lead triggers `POST` to the webhook URL with `{event:"lead.created", lead:{...}}`.
   Header `X-PlenDev-Signature: sha256=<hex HMAC of raw body with AUDIT_WEBHOOK_SECRET>`.
2. The agent updates the lead: `PATCH /api/leads/:id` with `Authorization: Bearer <CMS_API_TOKEN>`.
   Writable fields: `audit_status` (queued|auditing|awaiting_approval|approved|sent|failed), `audit_score`, `audit_report_url`, `audit_sent_at`, `audit_notes`.
   The token cannot edit lead details, pages or users.
3. The admin dashboard shows counts of new leads and audits awaiting approval.

## Demo sites and videos
- Source: `showcase-src/*.html` → `node scripts/build-showcase.mjs` → `public/showcase/<slug>/`.
- Videos: `node scripts/record-showcase.cjs` (Playwright + ffmpeg) → `public/showcase-media/`.

## Deploying (Vercel)
Set env vars above with a Postgres `DATABASE_URL`, generate migrations with `pnpm payload migrate:create`, run `pnpm payload migrate`, then `pnpm seed` once (`ALLOW_SEED=true` if using the seed route in production).

### Creating migrations
Run `pnpm payload migrate:create <name>` with a Postgres `DATABASE_URL` **and** a `BLOB_READ_WRITE_TOKEN` set
(any `vercel_blob_rw_<id>_<x>` value works). The Blob plugin adds a `_objectKey` column to media only when a token
is present, so a migration generated without one would drop that column in production.
