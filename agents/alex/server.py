#!/usr/bin/env python3
"""Alex's small public web service.

  GET  /r/<token>              the prospect's audit report (linked from the email)
  GET  /u/<token>              unsubscribe page;  POST /u/<token>  one-click unsubscribe (RFC 8058)
  GET  /admin/queue            drafts awaiting approval            (Bearer ALEX_ADMIN_TOKEN)
  GET  /admin/p/<id>           one prospect with drafts
  POST /admin/p/<id>/approve   {"subject": "...", "note": "...", "text": "..."}
  POST /admin/p/<id>/reject    {"reason": "..."}
  GET  /d/<token>/<n>[.png]    demo homepage concepts for an interested lead (and their screenshots)
  POST /wa                     Twilio WhatsApp webhook: Ahmed's commands (approve/reject/edit/show/queue)
  GET  /healthz
"""
from __future__ import annotations

import hmac
import html
import json
import os
import re
from argparse import Namespace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import config as C
import store

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>body{{font:16px/1.5 -apple-system,Segoe UI,Roboto,Arial,sans-serif;max-width:520px;margin:60px auto;padding:0 16px;color:#222}}
button{{font:inherit;padding:10px 18px;border:0;border-radius:6px;background:#222;color:#fff;cursor:pointer}}</style></head><body>{body}</body></html>"""


class H(BaseHTTPRequestHandler):
    server_version = "PlenDevAlex/1.0"

    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, (bytes, str)) else json.dumps(body, indent=2)
        data = data.encode() if isinstance(data, str) else data
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Robots-Tag", "noindex")
        self.end_headers()
        self.wfile.write(data)

    def _page(self, title, body, code=200):
        self._send(code, PAGE.format(title=html.escape(title), body=body), "text/html; charset=utf-8")

    def _admin(self):
        ok = C.ADMIN_TOKEN and hmac.compare_digest(self.headers.get("Authorization", ""), f"Bearer {C.ADMIN_TOKEN}")
        if not ok:
            self._send(401, {"error": "unauthorized"})
        return bool(ok)

    def _whatsapp(self, raw: bytes):
        from urllib.parse import parse_qsl
        params = dict(parse_qsl(raw.decode()))
        url = C.PUBLIC_BASE + "/wa"
        if not twilio_valid(url, params, self.headers.get("X-Twilio-Signature", "")):
            return self._send(403, {"error": "bad signature"})
        owner = os.environ.get("WHATSAPP_TO", "").lower()
        if params.get("From", "").lower() != owner:
            return self._send(200, "<Response/>", "text/xml")
        try:
            answer = wa_command(params.get("Body", ""))
        except SystemExit as e:  # e.g. send refused by preflight
            answer = f"Not sent: {e}"
        except Exception as e:  # noqa: BLE001
            answer = f"Error: {e}"
        return self._send(200, f"<Response><Message>{html.escape(answer[:1500])}</Message></Response>", "text/xml")

    def _unsubscribe(self, p):
        store.suppress(p["contact"]["email"], "unsubscribe link")
        if p["status"] not in ("opted_out",):
            p["status"] = "opted_out"
            store.event(p, "opted_out", via="link")
            store.save(p)
            store.log({"event": "reply", "id": p["id"], "kind": "unsubscribe"})

    def do_GET(self):
        parts = [x for x in urlparse(self.path).path.split("/") if x]
        if parts == ["healthz"]:
            return self._send(200, {"ok": True})
        if len(parts) == 2 and parts[0] == "r":
            p = store.by_token("report", parts[1])
            f = p and store.path(p["id"]).parent / "audit" / "report.html"
            return self._send(200, f.read_bytes(), "text/html; charset=utf-8") if f and f.exists() else self._send(404, {})
        if len(parts) == 3 and parts[0] == "d":
            p = store.by_token("demo", parts[1])
            m = re.fullmatch(r"([1-9])(-mobile)?(\.png)?", parts[2])
            if not p or not m:
                return self._send(404, {})
            f = store.path(p["id"]).parent / "demos" / (parts[2] if m.group(3) else f"{m.group(1)}.html")
            if not f.exists():
                return self._send(404, {})
            return self._send(200, f.read_bytes(), "image/png" if m.group(3) else "text/html; charset=utf-8")
        if len(parts) == 2 and parts[0] == "u":
            p = store.by_token("unsub", parts[1])
            if not p:
                return self._page("Not found", "<p>This link is not valid.</p>", 404)
            if p["status"] == "opted_out":
                return self._page("Unsubscribed", f"<h1>You're unsubscribed</h1><p>{C.COMPANY} won't email {html.escape(p['contact']['email'])} again.</p>")
            return self._page("Unsubscribe", f"<h1>Unsubscribe</h1><p>Stop all emails from {C.COMPANY} to "
                              f"<b>{html.escape(p['contact']['email'])}</b>?</p><form method=post><button>Unsubscribe</button></form>")
        if parts == ["admin", "queue"] and self._admin():
            items = store.all_prospects("awaiting_approval") + store.all_prospects("reply_awaiting_approval")
            return self._send(200, [{"id": p["id"], "business": p["business_name"], "site": p["website"],
                                     "score": p["audit"]["score"], "to": p["contact"]["email"], "status": p["status"],
                                     "subject": (p.get("reply_draft") or p["drafts"]["1"])["subject"]} for p in items])
        if len(parts) == 3 and parts[:2] == ["admin", "p"] and self._admin():
            p = store.get(parts[2])
            return self._send(200, p) if p else self._send(404, {})
        if parts[:1] != ["admin"]:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        parts = [x for x in urlparse(self.path).path.split("/") if x]
        raw = self.rfile.read(min(int(self.headers.get("Content-Length") or 0), 100_000))
        if len(parts) == 2 and parts[0] == "u":
            p = store.by_token("unsub", parts[1])
            if not p:
                return self._page("Not found", "<p>This link is not valid.</p>", 404)
            self._unsubscribe(p)
            return self._page("Unsubscribed", f"<h1>You're unsubscribed</h1><p>{C.COMPANY} won't email you again.</p>")
        if parts == ["wa"]:
            return self._whatsapp(raw)
        if len(parts) == 4 and parts[:2] == ["admin", "p"] and self._admin():
            import alex
            body = json.loads(raw or b"{}")
            if parts[3] == "approve":
                alex.cmd_approve(Namespace(id=parts[2], subject=body.get("subject"), note=body.get("note"), text=body.get("text")))
            elif parts[3] == "reject":
                alex.cmd_reject(Namespace(id=parts[2], reason=body.get("reason")))
            return self._send(200, {"status": store.get(parts[2])["status"]})
        if parts[:1] != ["admin"]:
            self._send(404, {"error": "not found"})


def twilio_valid(url: str, params: dict, sig: str) -> bool:
    import base64
    import hashlib
    tok = os.environ.get("TWILIO_AUTH_TOKEN", "")
    if not tok:
        return False
    data = url + "".join(k + params[k] for k in sorted(params))
    want = base64.b64encode(hmac.new(tok.encode(), data.encode(), hashlib.sha1).digest()).decode()
    return hmac.compare_digest(want, sig)


def wa_command(text: str) -> str:
    """Ahmed's WhatsApp commands. Returns the answer text."""
    import alex
    t = text.strip()
    m = re.match(r"(?is)^(approve|reject|show|edit)\s+([a-z0-9-]+|all)\s*:?\s*(.*)$", t)
    if t.lower() in ("queue", "list", "pending"):
        items = store.all_prospects("reply_awaiting_approval") + store.all_prospects("awaiting_approval")
        if not items:
            return "Nothing waiting for approval."
        return "\n".join(f"{p['id']} | {p['business_name']} | {p['audit']['score']}/100 | "
                         f"{'REPLY' if p['status'] == 'reply_awaiting_approval' else 'first email'}" for p in items[:20])
    if not m:
        return 'Commands: "queue", "show <id>", "approve <id>", "approve all" (first emails only), "reject <id>", "edit <id>: <new reply text>"'
    cmd, pid, rest = m.group(1).lower(), m.group(2).lower(), m.group(3).strip()
    if cmd == "approve" and pid == "all":
        items = store.all_prospects("awaiting_approval")
        for p in items:
            alex.cmd_approve(Namespace(id=p["id"], subject=None, note=None, text=None))
        return f"Approved {len(items)} first emails. They go out in the next send window. Replies still need one-by-one approval."
    p = store.get(pid)
    if not p:
        return f"No lead called {pid}."
    if cmd == "show":
        d = p.get("reply_draft") or (p.get("drafts") or {}).get("1")
        return f"{p['business_name']} ({p['website']}) {p['status']}\nTo: {p.get('contact', {}).get('email')}\n\n" + (
            f"Subject: {d['subject']}\n{d['text'][:1200]}" if d else "No draft.")
    if cmd == "reject":
        alex.cmd_reject(Namespace(id=pid, reason="rejected on WhatsApp"))
        return f"Rejected {pid}. Nothing sent."
    if cmd == "edit":
        if p["status"] != "reply_awaiting_approval" or not rest:
            return "Edit works on reply drafts: edit <id>: <full new text>"
        alex.cmd_approve(Namespace(id=pid, subject=None, note=None, text=rest + "\n\n" + alex.compose.env.get_template("_sig.txt.j2").render(**alex.compose.ctx(p))))
        return f"Sent your edited reply to {p['business_name']}."
    alex.cmd_approve(Namespace(id=pid, subject=None, note=None, text=None))
    st = store.get(pid)["status"]
    return f"Done: {pid} is now {st}."


def main():
    import os
    port = int(os.environ.get("ALEX_PORT") or os.environ.get("PORT", "8090"))
    print(f"Alex web service on :{port}")
    ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()


if __name__ == "__main__":
    main()
