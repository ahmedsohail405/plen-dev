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

# ---- inbound audit server
PUBLIC_BASE_URL=https://<audit-domain>
ADMIN_TOKEN=<long random string>
AUDIT_WEBHOOK_SECRET=<long random string, same value in the CMS>
AUTO_SEND=false                 # Ahmed approves every audit email
CMS_BASE_URL=https://<plen-dev site domain>
CMS_API_TOKEN=<from the CMS>
MAIL_FROM=Alex H <the agent mailbox Ahmed created>
MAIL_REPLY_TO=info@plendev.com

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
MS_TENANT_ID=
MS_CLIENT_ID=
MS_REFRESH_TOKEN=
ALEX_IMAP_HOST=outlook.office365.com
ALEX_IMAP_USER=
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

## Run locally

```
pip install -r audit-agent/requirements.txt -r alex/requirements.txt
OUTBOX_DIR=./data/audit-outbox ALEX_DATA_DIR=./data/alex ADMIN_TOKEN=dev AUDIT_WEBHOOK_SECRET=dev python run.py
```
