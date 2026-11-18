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
    try:  # WhatsApp to Ahmed through Alex's module (only once Twilio is configured)
        import sys
        alex_dir = ENV("ALEX_DIR", str(Path(__file__).resolve().parent.parent / "alex"))
        if ENV("WHATSAPP_PROVIDER", "print") != "print" and Path(alex_dir, "whatsapp.py").exists():
            if alex_dir not in sys.path:
                sys.path.append(alex_dir)
            import whatsapp
            whatsapp.send(text)
    except Exception as e:  # noqa: BLE001
        print("[notify] whatsapp failed:", e)
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
              speed_measured=r.get("speed_measured", False), industry=(r.get("industry") or {}).get("label", ""),
              email=json.loads((OUTBOX / lid / "email.json").read_text()))
    st["history"].append({"at": now(), "event": "audit_done", "score": r["score"]["overall"]})
    save_state(st)
    cms_patch(lid, {"audit_status": "awaiting_approval", "audit_score": r["score"]["overall"],
                    "audit_report_url": report_url})
    top = "; ".join(f["title"] for f in r["top_issues"][:3])
    notify(f"New audit ready for approval: {r['site_host']} scored {r['score']['overall']}/100 "
           f"for {lead.get('name')} <{lead.get('email')}>. Top issues: {top}. "
           f"Review and approve: {PUBLIC_BASE}/admin?key={ADMIN_TOKEN}#a-{lid}")
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
    # AUDIT_SMTP_USER=info@plendev.com, signed in once via Alex's /admin/ms-login page (Microsoft 365 OAuth).
    smtp = None
    if ENV("AUDIT_SMTP_USER"):
        smtp = {"user": ENV("AUDIT_SMTP_USER"), "host": ENV("AUDIT_SMTP_HOST", "smtp.office365.com"),
                "port": ENV("AUDIT_SMTP_PORT", "587")}
        if ENV("AUDIT_SMTP_PASS"):
            smtp["password"] = ENV("AUDIT_SMTP_PASS")
        else:  # Microsoft OAuth: token saved by Alex's /admin/ms-login page, or AUDIT_MS_REFRESH_TOKEN
            smtp["oauth"] = True
            if ENV("AUDIT_MS_REFRESH_TOKEN"):
                smtp["refresh_token"] = ENV("AUDIT_MS_REFRESH_TOKEN")
    msg_id = mailer.send(to=st["lead"]["email"], subject=subject, html=html, text=text, smtp=smtp)
    dry = mailer.PROVIDER == "dryrun" and not smtp
    st.update(status="sent", sent_at=now(), message_id=msg_id, final_subject=subject, dry_run=dry)
    st["history"].append({"at": now(), "event": "sent", "provider_id": msg_id})
    save_state(st)
    if dry:  # test mode: nothing left the building, so don't start a conversation in Alex
        cms_patch(lid, {"audit_status": "sent", "audit_sent_at": st["sent_at"],
                        "audit_notes": "Test mode (MAIL_PROVIDER=dryrun): email was not really sent."})
        return st
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


# --------------------------------------------------------------------------- approval page

def admin_page() -> bytes:
    import html as h
    rows = []
    for d in sorted(OUTBOX.glob("*/state.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:60]:
        st = json.loads(d.read_text())
        lead, lid = st["lead"], safe_id(st["lead"]["id"])
        status = st.get("status", "")
        if status == "sent" and st.get("dry_run"):
            status = "sent (test mode)"
        email_link = f"/admin/audits/{lid}/email?key={ADMIN_TOKEN}"
        actions = ""
        if st.get("status") == "awaiting_approval":
            actions = f"""
<form method=post action="/admin/audits/{lid}/approve"><input type=hidden name=key value="{ADMIN_TOKEN}">
<label>Subject <input name=subject value="{h.escape((st.get('email') or {}).get('subject', ''))}"></label>
<label>Personal line (optional) <textarea name=note rows=2></textarea></label>
<button class=ok>Approve &amp; send</button></form>
<form method=post action="/admin/audits/{lid}/reject"><input type=hidden name=key value="{ADMIN_TOKEN}">
<input name=reason placeholder="Reason (optional)"><button class=no>Reject</button></form>"""
        elif st.get("status") == "failed":
            actions = f"""<form method=post action="/admin/audits/{lid}/rerun"><input type=hidden name=key value="{ADMIN_TOKEN}">
<button>Run audit again</button></form><p class=err>{h.escape(st.get('error', ''))}</p>"""
        rows.append(f"""<section id="a-{lid}" class="card {h.escape(st.get('status', ''))}">
<div class=top><b>{h.escape(lead.get('company') or lead.get('website_url', ''))}</b><span class=pill>{h.escape(status)}</span></div>
<div class=meta>{h.escape(lead.get('name', ''))} &lt;{h.escape(lead.get('email', ''))}&gt; · {h.escape(lead.get('website_url', ''))}
{f" · score <b>{st['score']}/100</b>" if st.get('score') is not None else ''}{(' · ' + h.escape(st['industry'])) if st.get('industry') else ''}{' · <span class=err>speed not measured (add PAGESPEED_API_KEY)</span>' if st.get('score') is not None and st.get('speed_measured') is False else ''} · {h.escape(st.get('updated_at', '')[:16].replace('T', ' '))} UTC</div>
<div class=links>{f'<a href="{email_link}" target=_blank>Preview email</a>' if st.get('email') else ''}
{f'<a href="{st["report_url"]}" target=_blank>Full report</a>' if st.get('report_url') else ''}</div>{actions}</section>""")
    test = '<p class=banner>Test mode: approving will NOT send real email (MAIL_PROVIDER=dryrun).</p>' if mailer.PROVIDER == "dryrun" else ''
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<meta name=robots content=noindex><title>Audit approvals</title><style>
:root{{--bg:#f6f7f9;--card:#fff;--ink:#1f2330;--mute:#6b7280;--line:#e5e7eb}}
@media(prefers-color-scheme:dark){{:root{{--bg:#111318;--card:#1b1e25;--ink:#e8eaf0;--mute:#9aa1ad;--line:#2b2f38}}}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,Segoe UI,Roboto,sans-serif}}
main{{max-width:760px;margin:0 auto;padding:20px 16px}}h1{{font-size:22px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin:12px 0}}
.awaiting_approval{{border-left:4px solid #4f46e5}}.top{{display:flex;justify-content:space-between;gap:8px}}
.pill{{font-size:12px;padding:2px 8px;border-radius:99px;background:var(--line)}}.meta{{color:var(--mute);font-size:13px;margin:4px 0}}
.links a{{margin-right:14px;color:#6366f1}}form{{margin-top:10px;display:grid;gap:6px}}
input,textarea{{width:100%;box-sizing:border-box;padding:8px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink)}}
label{{font-size:13px;color:var(--mute)}}button{{padding:10px;border:0;border-radius:8px;font-weight:600;cursor:pointer}}
.ok{{background:#4f46e5;color:#fff}}.no{{background:var(--line);color:var(--ink)}}.err{{color:#d93025;font-size:13px}}
.banner{{background:#fff4d6;color:#7a5600;padding:10px 12px;border-radius:8px}}</style></head>
<body><main><h1>Website audit approvals</h1>{test}{''.join(rows) or '<p>No audits yet.</p>'}</main></body></html>""".encode()


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

    def _admin(self, key: str = "") -> bool:
        key = key or parse_qs(urlparse(self.path).query).get("key", [""])[0]
        ok = ADMIN_TOKEN and (hmac.compare_digest(self.headers.get("Authorization", ""), f"Bearer {ADMIN_TOKEN}")
                              or hmac.compare_digest(key, ADMIN_TOKEN))
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
            import importlib.util
            return self._send(200, {"ok": True, "queue": jobs.qsize(), "auto_send": AUTO_SEND,
                                    "engine": audit.ENGINE_VERSION,
                                    "visual_ready": importlib.util.find_spec("playwright") is not None,
                                    # true only when a Railway volume is mounted at /data (otherwise every deploy wipes it)
                                    "storage_persistent": os.path.ismount("/data")})
        if len(parts) in (2, 3) and parts[0] == "r":
            if len(parts) == 3 and not re.fullmatch(r"[a-z0-9-]+\.jpg", parts[2]):  # only screenshots, never state/json
                return self._send(404, {"error": "not found"})
            for d in OUTBOX.glob("*/state.json"):
                st = json.loads(d.read_text())
                if hmac.compare_digest(st.get("token", ""), parts[1]):
                    if len(parts) == 3:
                        f = d.parent / parts[2]
                        return self._send(200, f.read_bytes(), "image/jpeg") if f.exists() else self._send(404, {})
                    return self._send(200, (d.parent / "report.html").read_bytes(), "text/html; charset=utf-8")
            return self._send(404, {"error": "not found"})
        if parts == ["admin"]:
            if not self._admin():
                return
            return self._send(200, admin_page(), "text/html; charset=utf-8")
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
            form = "application/x-www-form-urlencoded" in self.headers.get("Content-Type", "")
            opts = {k: v[0] for k, v in parse_qs(raw.decode(errors="replace")).items()} if form else None
            if not self._admin((opts or {}).get("key", "")):
                return
            lid, action = safe_id(parts[2]), parts[3]
            st = load_state(lid)
            if not st:
                return self._send(404, {"error": "unknown audit"})
            if form:  # approval page: do the action, then go back to the page
                res = self._act(lid, action, st, {k: v for k, v in opts.items() if k != "key" and v.strip()})
                self.send_response(303)
                self.send_header("Location", f"/admin?key={ADMIN_TOKEN}&msg={res}#a-{lid}")
                self.end_headers()
                return
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

    def _act(self, lid: str, action: str, st: dict, opts: dict) -> str:
        if action == "approve" and st["status"] in ("awaiting_approval", "approved"):
            try:
                st2 = send(lid, opts)
                return "test-sent" if st2.get("dry_run") else "sent"
            except Exception as e:  # noqa: BLE001
                st.update(status="failed", error=f"send failed: {e}")
                save_state(st)
                return "send-failed"
        if action == "reject" and st["status"] == "awaiting_approval":
            st.update(status="rejected", reject_reason=opts.get("reason", ""))
            st["history"].append({"at": now(), "event": "rejected"})
            save_state(st)
            cms_patch(lid, {"audit_status": "failed", "audit_notes": "Rejected by Ahmed: " + opts.get("reason", "")})
            return "rejected"
        if action == "rerun":
            jobs.put(st["lead"])
            return "rerunning"
        return "no-change"

    def log_message(self, fmt, *args):  # never log query strings (they carry the admin key)
        print(f"{self.address_string()} {(fmt % args).split('?')[0]}")


def main():
    OUTBOX.mkdir(parents=True, exist_ok=True)
    for _ in range(int(ENV("AUDIT_WORKERS", "2"))):
        threading.Thread(target=worker, daemon=True).start()
    port = int(ENV("PORT", "8080"))
    print(f"Plen Dev audit server on :{port} (auto_send={AUTO_SEND}, mail={mailer.PROVIDER})")
    ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()


if __name__ == "__main__":
    main()
