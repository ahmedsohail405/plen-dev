"""Email sending for the audit pipeline.

MAIL_PROVIDER = dryrun (default) | resend | postmark | smtp
  dryrun   : writes the message to outbox/_sent/ and sends nothing
  resend   : RESEND_API_KEY
  postmark : POSTMARK_SERVER_TOKEN
  smtp     : SMTP_HOST, SMTP_PORT (587), SMTP_USER, SMTP_PASS  (Google Workspace, Microsoft 365, Zoho...)
             MS_AUTH=oauth signs in to Microsoft 365 with OAuth (XOAUTH2) instead of SMTP_PASS; see ms_oauth.py
Common: MAIL_FROM ("Ahmed at Plen Dev <audits@plendev.com>"), MAIL_REPLY_TO, MAIL_BCC (copy to yourself)
"""
from __future__ import annotations

import json
import os
import smtplib
import time
from email.message import EmailMessage
from email.utils import make_msgid
from pathlib import Path

import requests

E = os.environ.get
PROVIDER = E("MAIL_PROVIDER", "dryrun").lower()
FROM = E("MAIL_FROM", "Plen Dev <audits@plendev.com>")
REPLY_TO = E("MAIL_REPLY_TO", "info@plendev.com")
BCC = E("MAIL_BCC", "")


def send(to: str, subject: str, html: str, text: str, headers: dict | None = None,
         from_addr: str | None = None, reply_to: str | None = None, bcc: str | None = None,
         smtp: dict | None = None) -> str:
    """headers: extra headers such as List-Unsubscribe (used by Alex). from/reply_to/bcc override env.
    smtp: per-mailbox SMTP settings (Alex's mailbox pool): {"user", "password"} or {"user", "refresh_token"},
          optional "host"/"port". When given, the SMTP provider is used with these instead of SMTP_* env."""
    FROM_, REPLY_TO_, BCC_ = from_addr or FROM, REPLY_TO if reply_to is None else reply_to, BCC if bcc is None else bcc
    headers = headers or {}
    if not to:
        raise ValueError("lead has no email address")
    if PROVIDER == "resend":
        body = {"from": FROM_, "to": [to], "subject": subject, "html": html, "text": text}
        if REPLY_TO_: body["reply_to"] = REPLY_TO_
        if BCC_: body["bcc"] = [BCC_]
        if headers: body["headers"] = headers
        r = requests.post("https://api.resend.com/emails", json=body, timeout=30,
                          headers={"Authorization": f"Bearer {E('RESEND_API_KEY')}"})
        r.raise_for_status()
        return r.json().get("id", "")
    if PROVIDER == "postmark":
        body = {"From": FROM_, "To": to, "Subject": subject, "HtmlBody": html, "TextBody": text,
                "MessageStream": "outbound"}
        if REPLY_TO_: body["ReplyTo"] = REPLY_TO_
        if BCC_: body["Bcc"] = BCC_
        if headers: body["Headers"] = [{"Name": k, "Value": v} for k, v in headers.items()]
        r = requests.post("https://api.postmarkapp.com/email", json=body, timeout=30,
                          headers={"X-Postmark-Server-Token": E("POSTMARK_SERVER_TOKEN", ""), "Accept": "application/json"})
        r.raise_for_status()
        return r.json().get("MessageID", "")
    if PROVIDER == "smtp" or (smtp and PROVIDER != "dryrun"):
        m = EmailMessage()
        m["From"], m["To"], m["Subject"] = FROM_, to, subject
        if REPLY_TO_: m["Reply-To"] = REPLY_TO_
        if BCC_: m["Bcc"] = BCC_
        for k, v in headers.items():
            m[k] = v
        m["Message-ID"] = make_msgid(domain=FROM_.split("@")[-1].strip(">"))
        m.set_content(text)
        m.add_alternative(html, subtype="html")
        sm = smtp or {}
        host, port = sm.get("host") or E("SMTP_HOST"), int(sm.get("port") or E("SMTP_PORT", "587"))
        user = sm.get("user") or E("SMTP_USER")
        with smtplib.SMTP(host, port, timeout=30) as s:
            s.starttls()
            import ms_oauth
            if not sm.get("password") and (sm.get("refresh_token") or sm.get("oauth") or ms_oauth.stored(user)
                                           or E("MS_AUTH", "").lower() == "oauth"):
                ms_oauth.smtp_login(s, user, sm.get("refresh_token"))
            else:
                s.login(user, sm.get("password") or E("SMTP_PASS"))
            s.send_message(m)
        return m["Message-ID"]
    # dryrun
    d = Path(E("OUTBOX_DIR", Path(__file__).resolve().parent / "outbox")) / "_sent"
    d.mkdir(parents=True, exist_ok=True)
    mid = f"dryrun-{int(time.time() * 1000)}"
    (d / f"{mid}.json").write_text(json.dumps({"from": FROM_, "to": to, "reply_to": REPLY_TO_, "subject": subject, "headers": headers, "text": text}, indent=2))
    (d / f"{mid}.html").write_text(html)
    return mid
