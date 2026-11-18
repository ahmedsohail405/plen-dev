"""Alex's sending mailboxes.

One warmed mailbox can safely send roughly 30-40 cold emails a day. To do more, add mailboxes on
separate look-alike domains (getplendev.com, tryplendev.com, ...), each warmed up for 2-3 weeks,
and Alex rotates between them. A conversation always stays on the mailbox that started it.

ALEX_MAILBOXES (JSON list), secrets referenced by env-var NAME, never inline:
  [{"from": "Alex H at Plen Dev <alex@getplendev.com>", "user": "alex@getplendev.com",
    "refresh_env": "MB1_REFRESH_TOKEN", "warmup_start": "2026-12-08", "daily_cap": 30}]
  "password_env" instead of "refresh_env" for password SMTP/IMAP. Without ALEX_MAILBOXES, the single
  mailbox from SMTP_USER / ALEX_MAIL_FROM / ALEX_WARMUP_START / ALEX_DAILY_CAP is used.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta

import config as C
import store


def pool() -> list[dict]:
    raw = C.E("ALEX_MAILBOXES", "")
    if raw:
        boxes = [b for b in json.loads(raw) if b.get("send", True)]  # "send": false = read-only inbox
    else:
        boxes = [{"from": C.MAIL_FROM, "user": C.E("SMTP_USER", "") or C.MAIL_FROM.split("<")[-1].strip(">"),
                  "warmup_start": C.WARMUP_START, "daily_cap": C.DAILY_CAP,
                  "refresh_env": "MS_REFRESH_TOKEN" if C.E("MS_AUTH", "").lower() == "oauth" else "",
                  "password_env": "SMTP_PASS"}]
    for b in boxes:
        b.setdefault("daily_cap", C.DAILY_CAP)
        b["id"] = b["user"].lower()
    return boxes


def smtp_settings(box: dict) -> dict | None:
    if not C.E("ALEX_MAILBOXES"):
        return None  # single-mailbox mode: mailer reads SMTP_* env itself
    s = {"user": box["user"], "host": box.get("host"), "port": box.get("port")}
    if box.get("refresh_env") or not box.get("password_env"):  # OAuth (token from env or the saved sign-in)
        s["oauth"] = True
        s["refresh_token"] = C.E(box.get("refresh_env") or "", "")
    else:
        s["password"] = C.E(box.get("password_env", ""), "")
    return s


def cap_today(box: dict, t: datetime) -> int:
    """Warm-up ramp: nothing before warmup_start, then 5/day + 2 per sending day, up to daily_cap."""
    ws = box.get("warmup_start")
    if not ws:
        return 0 if C.SEND_ENABLED else box["daily_cap"]
    start = datetime.fromisoformat(ws).date()
    if t.date() < start:
        return 0
    days = sum(1 for i in range((t.date() - start).days) if (start + timedelta(days=i)).weekday() in C.SEND_DAYS)
    return min(box["daily_cap"], 5 + 2 * days)


def remaining(box: dict, t: datetime) -> int:
    return cap_today(box, t) - store.sent_on(t.strftime("%Y-%m-%d"), box["id"])


def for_prospect(p: dict, t: datetime) -> dict | None:
    """The mailbox a prospect's emails go out from: the one already used, else the one with most room today."""
    boxes = pool()
    if p.get("mailbox"):
        return next((b for b in boxes if b["id"] == p["mailbox"]), None)
    best = max(boxes, key=lambda b: remaining(b, t), default=None)
    return best if best and remaining(best, t) > 0 else None


def total_remaining(t: datetime) -> int:
    return sum(max(0, remaining(b, t)) for b in pool())
