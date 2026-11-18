"""Prospect records (one JSON file each), suppression list and send log."""
from __future__ import annotations

import json
import re
import threading
from datetime import datetime, timezone
from pathlib import Path

from config import DATA

PROSPECTS = DATA / "prospects"
SUPPRESS = DATA / "suppression.txt"
SENDLOG = DATA / "sendlog.jsonl"
STATE = DATA / "worker_state.json"
_lock = threading.Lock()


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def pid_for(domain: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", domain.lower().removeprefix("www.")).strip("-")[:60]


def path(pid: str) -> Path:
    return PROSPECTS / re.sub(r"[^a-z0-9-]", "", pid) / "prospect.json"


def get(pid: str) -> dict | None:
    p = path(pid)
    return json.loads(p.read_text()) if p.exists() else None


def save(p: dict) -> dict:
    f = path(p["id"])
    f.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        p["updated_at"] = now()
        tmp = f.with_suffix(".tmp")
        tmp.write_text(json.dumps(p, indent=2))
        tmp.replace(f)
    return p


def event(p: dict, name: str, **kw) -> None:
    p.setdefault("history", []).append({"at": now(), "event": name, **kw})


def all_prospects(status: str | None = None) -> list[dict]:
    out = []
    for f in sorted(PROSPECTS.glob("*/prospect.json")):
        p = json.loads(f.read_text())
        if status is None or p.get("status") == status:
            out.append(p)
    return out


def by_token(kind: str, token: str) -> dict | None:
    import hmac
    for p in all_prospects():
        if token and hmac.compare_digest(p.get(f"{kind}_token", ""), token):
            return p
    return None


# ---- suppression: emails and whole domains that must never be contacted

def suppressed_set() -> set[str]:
    if not SUPPRESS.exists():
        return set()
    return {l.strip().lower() for l in SUPPRESS.read_text().splitlines() if l.strip() and not l.startswith("#")}


def is_suppressed(email: str = "", domain: str = "") -> bool:
    s = suppressed_set()
    email, domain = email.lower(), domain.lower().removeprefix("www.")
    edom = email.split("@")[-1] if email else ""
    return bool((email and email in s) or (domain and domain in s) or (edom and edom in s and edom == domain))


def suppress(entry: str, reason: str) -> None:
    entry = entry.strip().lower()
    if not entry or entry in suppressed_set():
        return
    SUPPRESS.parent.mkdir(parents=True, exist_ok=True)
    with _lock, SUPPRESS.open("a") as f:
        f.write(f"{entry}\n")
    log({"event": "suppressed", "entry": entry, "reason": reason})


# ---- send log (for daily caps and audit trail)

def log(rec: dict) -> None:
    SENDLOG.parent.mkdir(parents=True, exist_ok=True)
    with _lock, SENDLOG.open("a") as f:
        f.write(json.dumps({"at": now(), **rec}) + "\n")


def sent_on(day_prefix: str, mailbox: str | None = None) -> int:
    if not SENDLOG.exists():
        return 0
    n = 0
    for line in SENDLOG.read_text().splitlines():
        r = json.loads(line)
        if r.get("event") == "sent" and r.get("local_day") == day_prefix and (mailbox is None or r.get("mailbox") == mailbox):
            n += 1
    return n


def import_inbound(lead: dict, report: dict, report_url: str, message_id: str, subject: str) -> dict:
    """Hand-off from the inbound audit server after its audit email is sent.

    lead: the CMS lead (id, name, email, phone, company, website_url, industry)
    report: the audit report dict (report.json); report_url: its public link
    message_id: provider/SMTP Message-ID of the sent audit email; subject: its subject
    Replies to that email are then matched and handled by Alex (sorting, WhatsApp, demos, drafts).
    """
    import secrets
    from urllib.parse import urlparse
    site = lead.get("website_url", "")
    site = site if site.startswith("http") else "https://" + site
    domain = (urlparse(site).hostname or "").removeprefix("www.")
    pid = pid_for(domain) or pid_for(lead["email"])
    p = get(pid) or {"id": pid, "created_at": now(), "history": [], "report_token": secrets.token_urlsafe(18),
                     "unsub_token": secrets.token_urlsafe(18)}
    p.update({
        "domain": domain, "website": site, "status": "inbound_sent", "source": "inbound_audit",
        "business_name": lead.get("company") or domain, "contact_name": lead.get("name", ""),
        "category": lead.get("industry", ""), "area": "", "phone": lead.get("phone", ""),
        "lead_id": lead.get("id"), "report_url": report_url,
        "contact": {"email": lead["email"].lower(), "source_url": "inbound form", "candidates": []},
        "audit": {"score": report["score"]["overall"], "counts": report.get("counts", {}),
                  "pitch": [{"id": f["id"], "severity": f["severity"], "line": f.get("impact") or f["title"]}
                            for f in report.get("top_issues", [])[:3]]},
        "sequence": {"subject": subject, "step": 1, "sent": [{"step": 1, "at": now(), "id": message_id, "subject": subject}],
                     "message_ids": [message_id if message_id.startswith("<") else f"<{message_id}>"], "next_due": None},
    })
    event(p, "inbound_imported", lead_id=lead.get("id"))
    return save(p)


def state(**updates) -> dict:
    """Small persistent worker state (discovery cursor, last inbox check, last report day)."""
    cur = json.loads(STATE.read_text()) if STATE.exists() else {}
    if updates:
        cur.update(updates)
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps(cur, indent=1))
    return cur
