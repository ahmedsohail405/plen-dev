# Plen Dev agents

Two Python agents that run together in one Railway service:

| Process | Code | What it does |
|---|---|---|
| `audit` | `audit-agent/server.py` | Receives "website audit" leads from the CMS, runs the deep audit, drafts the email, waits for Ahmed's approval, sends it, then hands the lead to Alex |
| `alex-web` | `alex/server.py` | Report, unsubscribe and demo-design links, Twilio WhatsApp webhook (`/wa`) |
| `alex-worker` | `alex/alex.py work` | Outbound sales agent. Schedules itself on ET weekdays: inbox checks, approved sends, prospecting, daily WhatsApp report |

`run.py` starts all three and restarts any that crash. Data lives on a Railway volume at `/data`.
Nothing here contains secrets; everything is set as Railway variables.

## Deploy on Railway (one time, ~10 minutes)

1. **New service.** In Railway: New Project → Deploy from GitHub repo → `ahmedsohail405/plen-dev`.
2. **Root directory.** Service → Settings → Source → Root Directory: `/agents`. (Railway then uses `agents/Dockerfile` and `agents/railway.json`.)
3. **Volume.** Service → right-click / Command palette → Add Volume → mount path `/data`.
4. **Variables.** Service → Variables → Raw editor → paste the block below and fill in the values.
5. **Domains.** Service → Settings → Networking → Generate Domain **twice**:
   - one with target port `8080` (audit server) → put it in `PUBLIC_BASE_URL`
   - one with target port `8081` (Alex) → put it in `ALEX_PUBLIC_BASE_URL`
   You can later use custom domains such as `audit.plendev.com` and `go.plendev.com`.
6. **Check.** Open `https://<audit-domain>/healthz`. It should show `{"ok": true, ...}`.
7. **Connect the CMS.** In the Plen Dev CMS → Site Settings → Integrations, set the audit webhook URL to
   `https://<audit-domain>/webhooks/lead` and the webhook secret to the same `AUDIT_WEBHOOK_SECRET`.

### Variables (paste into the Raw editor)

```
# ---- shared
PORT=8080
ALEX_PORT=8081
MAIL_PROVIDER=dryrun            # keep dryrun until the business address is set; then smtp
PLENDEV_ADDRESS=                # required before real sending (CAN-SPAM)
PLENDEV_SITE=https://plendev.com
PLENDEV_EMAIL=info@plendev.com
PLENDEV_PHONE=
PLENDEV_BOOKING_URL=
PAGESPEED_API_KEY=              # free, Google Cloud console > PageSpeed Insights API
# Optional. The visual audit (phone + desktop screenshots in headless Chromium) is on by default.
# Set VISUAL_AUDIT=0 to turn it off; VISUAL_TIMEOUT_MS is how long to wait for a slow page (default 45000).

# ---- inbound audit server
PUBLIC_BASE_URL=https://<audit-domain>
ADMIN_TOKEN=<long random string>
AUDIT_WEBHOOK_SECRET=<long random string, same value in the CMS>
AUTO_SEND=false                 # Ahmed approves every audit email
CMS_BASE_URL=https://<plen-dev site domain>
CMS_API_TOKEN=<from the CMS>
MAIL_FROM=Alex H <audit@plendev.com>
MAIL_REPLY_TO=audit@plendev.com
AUDIT_SMTP_USER=info@plendev.com     # audit@ is an alias of info@; we sign in as info@

# ---- Alex
ALEX_PUBLIC_BASE_URL=https://<alex-domain>
ALEX_ADMIN_TOKEN=<long random string>
ALEX_SEND_ENABLED=false
ALEX_MAIL_FROM=Alex H <alex@...>
ALEX_REPLY_TO=
ALEX_WARMUP_START=
# mailbox (Microsoft 365 OAuth)
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=
MS_AUTH=oauth
MS_TENANT_ID=6209b41b-f4cb-4e81-ae2f-26a6e6c93eba
MS_CLIENT_ID=9215b5a4-063b-4759-ae51-8760248d11d7
ALEX_IMAP_HOST=outlook.office365.com
ALEX_IMAP_USER=
ALEX_READ_INBOXES=[{"user":"info@plendev.com"}]   # Alex reads audit replies in info@ (read-only)
# WhatsApp (Twilio)
WHATSAPP_PROVIDER=twilio
WHATSAPP_TO=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_FROM=
TWILIO_CONTENT_SID=
# writer
ALEX_LLM=off                    # on = Claude writes each email (needs ANTHROPIC_API_KEY)
ANTHROPIC_API_KEY=
# optional
GOOGLE_PLACES_API_KEY=
ALEX_BCC=
```

`OUTBOX_DIR=/data/audit-outbox`, `ALEX_DATA_DIR=/data/alex` and the code paths are already set in the Dockerfile.
Never set `ALLOW_PRIVATE_TARGETS` in production. Set `DISABLE_ALEX=true` to run only the audit server.

See `audit-agent/PIPELINE.md` and `alex/README.md` and each folder's `.env.example` for details on every setting.

## Approving audits

Open `https://<audit-domain>/admin?key=<ADMIN_TOKEN>` (bookmark it on your phone). Each new audit shows the
score, a preview of the email and the full report, with **Approve & send** (optional subject change and personal
line) and **Reject**. A WhatsApp alert with this link goes out for every new audit once Twilio is configured.
While `MAIL_PROVIDER=dryrun`, approving only marks the audit "sent (test mode)": no email leaves and Alex is not started.

## Audit mailbox: sending as audit@plendev.com (Microsoft 365 via GoDaddy)

`audit@plendev.com` is an alias of `info@plendev.com`. The audit server signs in as info@ with Microsoft OAuth
(no password stored) and sends with From: audit@. One-time setup:

1. **Allow sending from aliases.** Exchange admin center (admin.exchange.microsoft.com, sign in with the GoDaddy
   Microsoft 365 admin account) → Settings → Mail flow → tick "Turn on sending from aliases" → Save.
   Can take up to an hour to apply.
2. **Turn on SMTP and IMAP for info@.** Microsoft 365 admin center → Users → Active users → info@plendev.com → Mail →
   Manage email apps → tick **Authenticated SMTP** and **IMAP** → Save.
3. **App registration** (reuse the one Alex uses if it exists, same `MS_TENANT_ID` / `MS_CLIENT_ID`):
   Microsoft Entra admin center → App registrations → New → name "Plen Dev agents", single tenant →
   Authentication → "Allow public client flows" = Yes → API permissions → add delegated
   `SMTP.Send`, `IMAP.AccessAsUser.All`, `offline_access` → Grant admin consent.
4. **Sign in each mailbox once.** After deploying, open
   `https://<alex-domain>/admin/ms-login?key=<ALEX_ADMIN_TOKEN>` and sign in info@plendev.com (and Alex's
   mailbox). Tokens are saved on the volume (`/data/ms-tokens`) and refreshed automatically; nothing to paste,
   and no client secret is needed.
5. Send yourself a test before switching `MAIL_PROVIDER=smtp`.

If GoDaddy's account doesn't expose the Exchange admin center or app registrations, the fallback is to send
as info@ with Reply-To audit@ (set `MAIL_FROM=Alex H <info@plendev.com>`), which needs only step 2 + a password
or the same OAuth.

## Run locally

```
pip install -r audit-agent/requirements.txt -r alex/requirements.txt
OUTBOX_DIR=./data/audit-outbox ALEX_DATA_DIR=./data/alex ADMIN_TOKEN=dev AUDIT_WEBHOOK_SECRET=dev python run.py
```
