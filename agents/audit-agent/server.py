#!/usr/bin/env python3
"""Plen Dev audit pipeline server (stdlib only + audit.py deps).

Flow:
  CMS lead saved -> POST /webhooks/lead (HMAC signed)
    -> queue -> audit.py runs -> email draft in outbox/<lead_id>/
    -> CMS lead PATCHed to audit_status=awaiting_approval
    -> Ahmed reviews (CMS link, GET /admin/audits, or Claude in the project)
    -> POST /admin/audits/<lead_id>/approve -> email sent -> CMS PATCHed to sent
  AUTO_SEND=true skips the approval step (off by default).

Endpoints
  POST /webhooks/lead                      CMS webhook (X-PlenDev-Signature: sha256=<hmac>)
  GET  /r/<token>                          public, unguessable link to the full HTML report
  GET  /admin/audits[?status=...]          list audits                      (Bearer ADMIN_TOKEN)
  GET  /admin/audits/<id>/email            preview the email HTML            (Bearer ADMIN_TOKEN)
  POST /admin/audits/<id>/approve          send it  (optional JSON {"subject": "...", "note": "..."})
  POST /admin/audits/<id>/reject           mark rejected, nothing sent
  POST /admin/audits/<id>/rerun            re-run the audit
  GET  /healthz

Env: see .env.example
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import queue
import re
import secrets
import threading
import traceback
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import requests

import audit
import mailer

ENV = os.environ.get
OUTBOX = Path(ENV("OUTBOX_DIR", Path(__file__).resolve().parent / "outbox"))
PUBLIC_BASE = ENV("PUBLIC_BASE_URL", "http://localhost:8080").rstrip("/")
WEBHOOK_SECRET = ENV("AUDIT_WEBHOOK_SECRET", "")
ADMIN_TOKEN = ENV("ADMIN_TOKEN", "")
CMS_BASE = ENV("CMS_BASE_URL", "").rstrip("/")
CMS_TOKEN = ENV("CMS_API_TOKEN", "")
AUTO_SEND = ENV("AUTO_SEND", "false").lower() == "true"
NOTIFY_WEBHOOK = ENV("NOTIFY_WEBHOOK_URL", "")  # optional: Slack/Discord/etc incoming webhook
MAX_PAGES = int(ENV("AUDIT_MAX_PAGES", "15"))

jobs: queue.Queue = queue.Queue()
lock = threading.Lock()


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def public_target(url: str) -> bool:
    """Reject malformed URLs and anything resolving to a private/internal address (SSRF guard)."""
    import ipaddress
    import socket
    host = urlparse(url if "://" in url else "https://" + url).hostname or ""
    if ENV("ALLOW_PRIVATE_TARGETS", "false").lower() == "true":
        return bool(host)
    if not re.match(r"^[\w.-]+\.[a-z]{2,}$", host, re.I):
        return False
    try:
        addrs = {ai[4][0] for ai in socket.getaddrinfo(host, None)}
    except socket.gaierror:
        return False
    return all(ipaddress.ip_address(a).is_global for a in addrs)


def safe_id(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "", str(s))[:64]


def state_path(lead_id: str) -> Path:
    return OUTBOX / safe_id(lead_id) / "state.json"


def load_state(lead_id: str) -> dict | None:
    p = state_path(lead_id)
    return json.loads(p.read_text()) if p.exists() else None


def save_state(st: dict) -> None:
    p = state_path(st["lead"]["id"])
    p.parent.mkdir(parents=True, exist_ok=True)
    with lock:
        st["updated_at"] = now()
        p.write_text(json.dumps(st, indent=2))


def cms_patch(lead_id: str, fields: dict) -> None:
    if not (CMS_BASE and CMS_TOKEN):
        return
    try:
        requests.patch(f"{CMS_BASE}/api/leads/{lead_id}", json=fields, timeout=15,
                       headers={"Authorization": f"Bearer {CMS_TOKEN}"})
    except requests.RequestException as e:
        print("CMS patch failed:", e)


def notify(text: str) -> None:
    print("[notify]", text)
    if NOTIFY_WEBHOOK:
        try:
            requests.post(NOTIFY_WEBHOOK, json={"text": text, "content": text}, timeout=10)
        except requests.RequestException:
            pass


# --------------------------------------------------------------------------- worker

def process(lead: dict) -> None:
    lid = safe_id(lead["id"])
    st = load_state(lid) or {"lead": lead, "token": secrets.token_urlsafe(18), "created_at": now(), "history": []}
    st.update(status="auditing")
    st["history"].append({"at": now(), "event": "audit_started"})
    save_state(st)
    cms_patch(lid, {"audit_status": "auditing"})
    report_url = f"{PUBLIC_BASE}/r/{st['token']}"
    try:
        r = audit.run_audit(lead["website_url"], lead, OUTBOX / lid, MAX_PAGES,
                            ENV("PAGESPEED_API_KEY"), report_url=report_url)
    except Exception as e:  # noqa: BLE001
        st.update(status="failed", error=str(e))
        st["history"].append({"at": now(), "event": "audit_failed", "error": traceback.format_exc()[-800:]})
        save_state(st)
        cms_patch(lid, {"audit_status": "failed", "audit_notes": str(e)[:500]})
        notify(f"Audit FAILED for {lead.get('website_url')} ({lead.get('email')}): {e}")
        return
    st.update(status="awaiting_approval", score=r["score"]["overall"], report_url=report_url,
              email=json.loads((OUTBOX / lid / "email.json").read_text()))
    st["history"].append({"at": now(), "event": "audit_done", "score": r["score"]["overall"]})
    save_state(st)
    cms_patch(lid, {"audit_status": "awaiting_approval", "audit_score": r["score"]["overall"],
                    "audit_report_url": report_url})
    top = "; ".join(f["title"] for f in r["top_issues"][:3])
    notify(f"New audit ready for approval: {r['site_host']} scored {r['score']['overall']}/100 "
           f"for {lead.get('name')} <{lead.get('email')}>. Top issues: {top}. "
           f"Preview: {PUBLIC_BASE}/admin/audits/{lid}/email  Report: {report_url}")
    if AUTO_SEND:
        send(lid, {})


def send(lid: str, overrides: dict) -> dict:
    st = load_state(lid)
    if not st:
        raise KeyError(lid)
    if st["status"] == "sent":
        return st
    folder = OUTBOX / lid
    subject = overrides.get("subject") or st["email"]["subject"]
    html = (folder / "email.html").read_text()
    text = (folder / "email.txt").read_text()
    if overrides.get("note"):  # optional personal line from Ahmed, added after the greeting
        note = overrides["note"].strip()
        import html as _h
        para = f'\n  <p style="margin:0 0 16px;font-size:16px;line-height:1.55;">{_h.escape(note)}</p>'
        html = re.sub(r"(Hi [^<]*,</p>)", lambda m: m.group(1) + para, html, count=1)
        text = re.sub(r"^(Hi [^\n]*,\n)", lambda m: m.group(1) + "\n" + note + "\n", text, count=1)
    # The audit sender (audit@plendev.com, an alias of info@) can sign in separately from Alex's mailboxes:
    # AUDIT_SMTP_USER=info@plendev.com + AUDIT_MS_REFRESH_TOKEN (Microsoft 365 OAuth) or AUDIT_SMTP_PASS.
    smtp = None
    if ENV("AUDIT_SMTP_USER"):
        smtp = {"user": ENV("AUDIT_SMTP_USER"), "host": ENV("AUDIT_SMTP_HOST", "smtp.office365.com"),
                "port": ENV("AUDIT_SMTP_PORT", "587")}
        if ENV("AUDIT_MS_REFRESH_TOKEN"):
            smtp["refresh_token"] = ENV("AUDIT_MS_REFRESH_TOKEN")
        else:
            smtp["password"] = ENV("AUDIT_SMTP_PASS", "")
    msg_id = mailer.send(to=st["lead"]["email"], subject=subject, html=html, text=text, smtp=smtp)
    st.update(status="sent", sent_at=now(), message_id=msg_id, final_subject=subject)
    st["history"].append({"at": now(), "event": "sent", "provider_id": msg_id})
    save_state(st)
    cms_patch(lid, {"audit_status": "sent", "audit_sent_at": st["sent_at"]})
    handoff_to_alex(st, subject, msg_id)
    return st


def handoff_to_alex(st: dict, subject: str, msg_id: str) -> None:
    """After the audit email goes out, Alex owns the conversation: reply handling, 2-3 demo designs
    (each approved by Ahmed first) and WhatsApp forwarding. Set ALEX_DIR to the alex/ folder."""
    alex_dir = ENV("ALEX_DIR", str(Path(__file__).resolve().parent.parent / "alex"))
    if not Path(alex_dir, "store.py").exists():
        return
    import sys
    if alex_dir not in sys.path:
        sys.path.insert(0, alex_dir)
    try:
        import config  # noqa: F401  (alex config sets paths)
        import store
        report = json.loads((OUTBOX / safe_id(st["lead"]["id"]) / "report.json").read_text())
        store.import_inbound(st["lead"], report, st.get("report_url", ""), msg_id, subject)
        st["history"].append({"at": now(), "event": "handed_to_alex"})
        save_state(st)
    except Exception as e:  # noqa: BLE001
        notify(f"Audit sent but hand-off to Alex failed for {st['lead'].get('email')}: {e}")


def worker() -> None:
    while True:
        lead = jobs.get()
        try:
            process(lead)
        finally:
            jobs.task_done()


# --------------------------------------------------------------------------- http

class H(BaseHTTPRequestHandler):
    server_version = "PlenDevAudit/1.0"

    def _send(self, code: int, body, ctype="application/json"):
        data = body if isinstance(body, (bytes, str)) else json.dumps(body, indent=2)
        data = data.encode() if isinstance(data, str) else data
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _admin(self) -> bool:
        ok = ADMIN_TOKEN and hmac.compare_digest(self.headers.get("Authorization", ""), f"Bearer {ADMIN_TOKEN}")
        if not ok:
            self._send(401, {"error": "unauthorized"})
        return bool(ok)

    def _body(self) -> bytes:
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(min(n, 1_000_000))

    def do_GET(self):
        u = urlparse(self.path)
        parts = [p for p in u.path.split("/") if p]
        if u.path == "/healthz":
            return self._send(200, {"ok": True, "queue": jobs.qsize(), "auto_send": AUTO_SEND})
        if len(parts) == 2 and parts[0] == "r":
            for d in OUTBOX.glob("*/state.json"):
                st = json.loads(d.read_text())
                if hmac.compare_digest(st.get("token", ""), parts[1]):
                    return self._send(200, (d.parent / "report.html").read_bytes(), "text/html; charset=utf-8")
            return self._send(404, {"error": "not found"})
        if parts[:2] == ["admin", "audits"]:
            if not self._admin():
                return
            if len(parts) == 2:
                want = parse_qs(u.query).get("status", [None])[0]
                items = []
                for d in sorted(OUTBOX.glob("*/state.json"), key=lambda p: p.stat().st_mtime, reverse=True):
                    st = json.loads(d.read_text())
                    if want and st.get("status") != want:
                        continue
                    items.append({k: st.get(k) for k in ("status", "score", "report_url", "updated_at")} |
                                 {"lead": st["lead"], "subject": (st.get("email") or {}).get("subject")})
                return self._send(200, {"audits": items})
            lid = safe_id(parts[2])
            if len(parts) == 4 and parts[3] == "email":
                f = OUTBOX / lid / "email.html"
                return self._send(200, f.read_bytes(), "text/html; charset=utf-8") if f.exists() else self._send(404, {})
            if len(parts) == 3:
                st = load_state(lid)
                return self._send(200, st) if st else self._send(404, {})
        self._send(404, {"error": "not found"})

    def do_POST(self):
        parts = [p for p in urlparse(self.path).path.split("/") if p]
        raw = self._body()
        if parts == ["webhooks", "lead"]:
            sig = self.headers.get("X-PlenDev-Signature", "")
            want = "sha256=" + hmac.new(WEBHOOK_SECRET.encode(), raw, hashlib.sha256).hexdigest()
            if not WEBHOOK_SECRET or not hmac.compare_digest(sig, want):
                return self._send(401, {"error": "bad signature"})
            try:
                lead = json.loads(raw)["lead"]
            except (ValueError, KeyError):
                return self._send(400, {"error": "bad payload"})
            if lead.get("type") != "website_audit" or not lead.get("website_url") or not lead.get("email"):
                return self._send(200, {"ignored": True})
            if not public_target(lead["website_url"]):
                return self._send(422, {"error": "invalid or non-public website_url"})
            if (st := load_state(safe_id(lead["id"]))) and st["status"] not in ("failed",):
                return self._send(200, {"duplicate": True, "status": st["status"]})
            jobs.put(lead)
            cms_patch(safe_id(lead["id"]), {"audit_status": "queued"})
            return self._send(202, {"queued": True})
        if parts[:2] == ["admin", "audits"] and len(parts) == 4:
            if not self._admin():
                return
            lid, action = safe_id(parts[2]), parts[3]
            st = load_state(lid)
            if not st:
                return self._send(404, {"error": "unknown audit"})
            opts = json.loads(raw or b"{}")
            if action == "approve":
                if st["status"] not in ("awaiting_approval", "approved"):
                    return self._send(409, {"error": f"status is {st['status']}"})
                try:
                    return self._send(200, send(lid, opts))
                except Exception as e:  # noqa: BLE001
                    st.update(status="failed", error=f"send failed: {e}")
                    save_state(st)
                    return self._send(502, {"error": str(e)})
            if action == "reject":
                st.update(status="rejected", reject_reason=opts.get("reason", ""))
                st["history"].append({"at": now(), "event": "rejected"})
                save_state(st)
                cms_patch(lid, {"audit_status": "failed", "audit_notes": "Rejected by Ahmed: " + opts.get("reason", "")})
                return self._send(200, st)
            if action == "rerun":
                jobs.put(st["lead"])
                return self._send(202, {"queued": True})
        self._send(404, {"error": "not found"})

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} {fmt % args}")


def main():
    OUTBOX.mkdir(parents=True, exist_ok=True)
    for _ in range(int(ENV("AUDIT_WORKERS", "2"))):
        threading.Thread(target=worker, daemon=True).start()
    port = int(ENV("PORT", "8080"))
    print(f"Plen Dev audit server on :{port} (auto_send={AUTO_SEND}, mail={mailer.PROVIDER})")
    ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()


if __name__ == "__main__":
    main()
