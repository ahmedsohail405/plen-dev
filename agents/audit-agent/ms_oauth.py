"""Microsoft 365 OAuth2 for SMTP and IMAP (XOAUTH2), used when MS_AUTH=oauth.

Microsoft has retired password ("basic") logins for IMAP and is retiring them for SMTP AUTH in
Exchange Online, so a 365 mailbox normally needs OAuth. One-time setup:
  1. Entra admin center > App registrations > New (single tenant). Note the client ID and tenant ID.
     Authentication > "Allow public client flows" = Yes.
     API permissions > Office 365 Exchange Online (delegated): SMTP.Send, IMAP.AccessAsUser.All; plus offline_access.
  2. Exchange admin > the mailbox > Mail apps: "Authenticated SMTP" and "IMAP" enabled.
  3. Run `python3 ms_oauth.py login` and sign in as the mailbox once (device code). It prints MS_REFRESH_TOKEN
     to store as a secret on the server (never in code). Tokens refresh themselves after that.
Env: MS_TENANT_ID, MS_CLIENT_ID, MS_REFRESH_TOKEN
"""
from __future__ import annotations

import base64
import os
import sys
import time

import requests

E = os.environ.get
SCOPE = "https://outlook.office.com/SMTP.Send https://outlook.office.com/IMAP.AccessAsUser.All offline_access"
_cache: dict = {}  # refresh token -> {"tok", "exp", "refresh"}


def _url(path: str) -> str:
    return f"https://login.microsoftonline.com/{E('MS_TENANT_ID', 'organizations')}/oauth2/v2.0/{path}"


def access_token(refresh_token: str | None = None) -> str:
    """refresh_token: per-mailbox token (several Alex mailboxes); default MS_REFRESH_TOKEN."""
    key = refresh_token or E("MS_REFRESH_TOKEN", "")
    c = _cache.setdefault(key, {})
    if c.get("exp", 0) > time.time() + 60:
        return c["tok"]
    r = requests.post(_url("token"), timeout=30, data={
        "client_id": E("MS_CLIENT_ID", ""), "grant_type": "refresh_token",
        "refresh_token": c.get("refresh") or key, "scope": SCOPE})
    r.raise_for_status()
    d = r.json()
    c.update(tok=d["access_token"], exp=time.time() + int(d.get("expires_in", 3600)),
             refresh=d.get("refresh_token") or c.get("refresh"))
    return d["access_token"]


def xoauth2(user: str, refresh_token: str | None = None) -> str:
    """Raw SASL XOAUTH2 string (not base64): for imaplib.authenticate and smtplib auth."""
    return f"user={user}\x01auth=Bearer {access_token(refresh_token)}\x01\x01"


def smtp_login(s, user: str, refresh_token: str | None = None) -> None:
    s.ehlo()
    code, resp = s.docmd("AUTH", "XOAUTH2 " + base64.b64encode(xoauth2(user, refresh_token).encode()).decode())
    if code != 235:
        raise RuntimeError(f"SMTP XOAUTH2 failed: {code} {resp!r}")


def login() -> None:
    r = requests.post(_url("devicecode"), data={"client_id": E("MS_CLIENT_ID", ""), "scope": SCOPE}, timeout=30)
    r.raise_for_status()
    d = r.json()
    print(d["message"])
    while True:
        time.sleep(d.get("interval", 5))
        t = requests.post(_url("token"), timeout=30, data={
            "client_id": E("MS_CLIENT_ID", ""), "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": d["device_code"]}).json()
        if "refresh_token" in t:
            print("\nStore this as the MS_REFRESH_TOKEN secret on the server:\n" + t["refresh_token"])
            return
        if t.get("error") not in ("authorization_pending", "slow_down"):
            sys.exit(f"login failed: {t.get('error_description', t)}")


if __name__ == "__main__" and sys.argv[1:] == ["login"]:
    login()
