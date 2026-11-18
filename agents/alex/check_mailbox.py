#!/usr/bin/env python3
"""Check Alex's mailbox without sending anything.

  python3 check_mailbox.py

Tests: SMTP login (password or MS_AUTH=oauth), IMAP login + inbox count, and the sending domain's
DNS (MX, SPF, DKIM for Microsoft 365, DMARC). Reads secrets from the environment only.
"""
from __future__ import annotations

import imaplib
import smtplib
import sys

import requests

import config as C  # noqa: F401  (puts audit-agent on the path)
import replies

E = C.E
ok = True


def line(good: bool, what: str, detail: str = "") -> None:
    global ok
    ok &= good
    print(f"[{'OK' if good else '!!'}] {what}" + (f": {detail}" if detail else ""))


def dns(name: str, rtype: str) -> list[str]:
    try:
        import dns.resolver  # dnspython, if installed
        return [r.to_text().strip('"') for r in dns.resolver.resolve(name, rtype)]
    except ImportError:
        r = requests.get("https://dns.google/resolve", params={"name": name, "type": rtype}, timeout=15).json()
        return [a["data"].strip('"') for a in r.get("Answer", [])]
    except Exception:  # noqa: BLE001
        return []


user = E("SMTP_USER", "")
domain = user.split("@")[-1].lower()
print(f"Mailbox {user}\n")

try:
    with smtplib.SMTP(E("SMTP_HOST", "smtp.office365.com"), int(E("SMTP_PORT", "587")), timeout=30) as s:
        s.starttls()
        if E("MS_AUTH", "").lower() == "oauth":
            import ms_oauth
            ms_oauth.smtp_login(s, user)
        else:
            s.login(user, E("SMTP_PASS", ""))
    line(True, "SMTP login")
except smtplib.SMTPAuthenticationError as e:
    msg = e.smtp_error.decode(errors="replace")
    hint = ("SMTP AUTH is disabled for this mailbox/tenant, or Microsoft no longer accepts passwords: "
            "turn on Authenticated SMTP for the mailbox and use MS_AUTH=oauth (see audit-agent/ms_oauth.py)")
    line(False, "SMTP login", f"{e.smtp_code} {msg[:160]}" + (f"\n     -> {hint}" if "5.7.139" in msg or "basic" in msg.lower() or "disabled" in msg.lower() else ""))
except Exception as e:  # noqa: BLE001
    line(False, "SMTP login", str(e)[:200])

try:
    with imaplib.IMAP4_SSL(C.IMAP_HOST or "outlook.office365.com") as m:
        replies.imap_login(m)
        typ, data = m.select("INBOX", readonly=True)
        line(True, "IMAP login", f"{data[0].decode()} messages in inbox")
except Exception as e:  # noqa: BLE001
    line(False, "IMAP login", f"{str(e)[:160]}\n     -> Microsoft 365 needs OAuth for IMAP (MS_AUTH=oauth) and IMAP enabled on the mailbox")

mx = dns(domain, "MX")
line(any("outlook.com" in r for r in mx), "MX points to Microsoft 365", ", ".join(mx) or "none")
spf = [r for r in dns(domain, "TXT") if r.lower().startswith("v=spf1")]
line(bool(spf) and "spf.protection.outlook.com" in spf[0], "SPF includes Microsoft 365",
     spf[0] if spf else "missing: add TXT  v=spf1 include:spf.protection.outlook.com -all")
dk = dns(f"selector1._domainkey.{domain}", "CNAME") + dns(f"selector2._domainkey.{domain}", "CNAME")
line(len(dk) >= 2, "DKIM (selector1/selector2)", ", ".join(dk) or "missing: enable DKIM for the domain in Microsoft Defender and add both CNAMEs")
dm = [r for r in dns(f"_dmarc.{domain}", "TXT") if r.lower().startswith("v=dmarc1")]
line(bool(dm), "DMARC", dm[0] if dm else "missing: add TXT _dmarc  v=DMARC1; p=none; rua=mailto:info@plendev.com")

print("\nAll good." if ok else "\nFix the items marked !! before sending.")
sys.exit(0 if ok else 1)
