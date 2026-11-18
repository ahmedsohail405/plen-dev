"""Alex settings, all from environment variables (see .env.example)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

E = os.environ.get
HERE = Path(__file__).resolve().parent
AUDIT_DIR = Path(E("AUDIT_ENGINE_DIR", HERE.parent / "audit-agent"))
sys.path.insert(0, str(AUDIT_DIR))  # reuse the audit engine + mailer

DATA = Path(E("ALEX_DATA_DIR", HERE / "data"))
os.environ.setdefault("OUTBOX_DIR", str(DATA / "outbox"))  # mailer dry-run writes here

PUBLIC_BASE = E("ALEX_PUBLIC_BASE_URL", "http://localhost:8090").rstrip("/")
ADMIN_TOKEN = E("ALEX_ADMIN_TOKEN", "")

# Identity (Ahmed 2026-11-17: sign as "Alex H, Sales, Plen Dev"). Alex never claims to be human:
# if a prospect asks, the reply_identity template answers honestly.
AGENT_NAME = E("ALEX_NAME", "Alex H")
AGENT_TITLE = E("ALEX_TITLE", "Sales, Plen Dev")
MAIL_FROM = E("ALEX_MAIL_FROM", "Alex H at Plen Dev <alex@plendev.com>")
REPLY_TO = E("ALEX_REPLY_TO", "")          # empty = replies go to the From mailbox, which Alex reads
BCC = E("ALEX_BCC", "")
COMPANY = E("PLENDEV_NAME", "Plen Dev")
SITE = E("PLENDEV_SITE", "https://plendev.com")
CONTACT_EMAIL = E("PLENDEV_EMAIL", "info@plendev.com")
PHONE = E("PLENDEV_PHONE", "")
ADDRESS = E("PLENDEV_ADDRESS", "")          # REQUIRED before any real send (CAN-SPAM)
BOOKING_URL = E("PLENDEV_BOOKING_URL", "")  # Cal.com / Calendly link; empty = "reply with a time"
PRICE_FROM = E("PLENDEV_PRICE_FROM", "$1,499")  # Launch package; matches /packages
HOME_AREA = E("PLENDEV_HOME_AREA", "Brooklyn")

# Targeting and qualification
MAX_SCORE = int(E("ALEX_MAX_SCORE", "62"))        # pitch sites at or below this score (deep audit scoring, Nov 18)...
VISUAL = E("ALEX_VISUAL_AUDIT", "false").lower() == "true"  # headless-browser checks: +15-25s per site
MIN_SERIOUS = int(E("ALEX_MIN_SERIOUS", "5"))      # ...or with at least this many critical/high pitchable issues
MIN_ISSUES = int(E("ALEX_MIN_PITCH_ISSUES", "2"))  # need this many sales-relevant medium+ issues
AUDIT_PAGES = int(E("ALEX_AUDIT_PAGES", "8"))
CRAWL_DELAY = float(E("ALEX_CRAWL_DELAY", "1.5"))  # seconds between requests to a prospect site
PSI_KEY = E("PAGESPEED_API_KEY") or None
GOOGLE_PLACES_KEY = E("GOOGLE_PLACES_API_KEY", "")

# Sending
SEND_ENABLED = E("ALEX_SEND_ENABLED", "false").lower() == "true"  # false = dry run only
DAILY_CAP = int(E("ALEX_DAILY_CAP", "30"))         # all emails (first + follow-ups) per day, after warm-up
# Warm-up: no cold email before ALEX_WARMUP_START; then the cap starts at 5/day and grows by 2 each sending day.
WARMUP_START = E("ALEX_WARMUP_START", "")          # YYYY-MM-DD, first day Alex may send cold email
MIN_GAP = int(E("ALEX_MIN_GAP_SECONDS", "90"))      # spacing between sends
INBOX_EVERY = int(E("ALEX_INBOX_EVERY_SECONDS", "600"))  # how often the worker checks for replies
TICK = int(E("ALEX_TICK_SECONDS", "60"))                 # worker loop interval
TZ = E("ALEX_TZ", "America/New_York")
SEND_DAYS = [int(d) for d in E("ALEX_SEND_DAYS", "0,1,2,3,4").split(",")]  # Mon-Fri
SEND_HOURS = tuple(int(h) for h in E("ALEX_SEND_HOURS", "9,17").split(","))  # 9:00 to 4:59 PM local (Ahmed: 9 to 5 Eastern)
FOLLOWUP_DAYS = [int(d) for d in E("ALEX_FOLLOWUP_DAYS", "3,7").split(",")]  # after previous email

# Reply inbox (IMAP), optional
IMAP_HOST, IMAP_USER, IMAP_PASS = E("ALEX_IMAP_HOST", ""), E("ALEX_IMAP_USER", ""), E("ALEX_IMAP_PASS", "")

NOTIFY_WEBHOOK = E("ALEX_NOTIFY_WEBHOOK_URL", "")
WHATSAPP_FORWARD = E("ALEX_WHATSAPP_FORWARD", "true").lower() == "true"  # every reply + draft to Ahmed
DEMO_COUNT = int(E("ALEX_DEMO_COUNT", "3"))


def preflight_errors(box: dict | None = None) -> list[str]:
    """Things that must be set before Alex may send a real email."""
    errs = []
    if box is not None and not box.get("warmup_start"):
        errs.append(f"warmup_start for mailbox {box.get('user')}")
    if not ADDRESS:
        errs.append("PLENDEV_ADDRESS (postal address in every email, required by CAN-SPAM)")
    if PUBLIC_BASE.startswith("http://localhost"):
        errs.append("ALEX_PUBLIC_BASE_URL (public host for report and unsubscribe links)")
    if "@" not in MAIL_FROM:
        errs.append("ALEX_MAIL_FROM")
    if box is None and not WARMUP_START:
        errs.append("ALEX_WARMUP_START (first cold-email day, after the 2-3 week warm-up)")
    if E("MAIL_PROVIDER", "dryrun") == "dryrun":
        errs.append("MAIL_PROVIDER (resend | postmark | smtp)")
    return errs
