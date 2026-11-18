"""Microsoft 365 OAuth2 for SMTP and IMAP (XOAUTH2), used when MS_AUTH=oauth.

Microsoft has retired password ("basic") logins for IMAP and is retiring them for SMTP AUTH in
Exchange Online, so a 365 mailbox normally needs OAuth. One-time setup:
  1. Entra admin center > App registrations > New (single tenant). Note the client ID and tenant ID.
     Authentication > "Allow public client flows" = Yes.
     API permissions > Office 365 Exchange Online (delegated): SMTP.Send, IMAP.AccessAsUser.All; plus offline_access.
  2. Exchange admin > the mailbox > Mail apps: "Authenticated SMTP" and "IMAP" enabled.
  3. Sign in as the mailbox once (device code). Easiest on the server: open Alex's
     /admin/ms-login?user=<mailbox>&key=<ALEX_ADMIN_TOKEN> page. The refresh token is saved on the data
     volume (MS_TOKEN_DIR, default <ALEX_DATA_DIR>/../ms-tokens), never shown, and kept current as
     Microsoft rotates it. Or run `python3 ms_oauth.py login [mailbox]` locally and store the printed
     token as MS_REFRESH_TOKEN (or a per-mailbox env var).
Env: MS_TENANT_ID, MS_CLIENT_ID, optional MS_REFRESH_TOKEN / MS_TOKEN_DIR.
Token order for a mailbox: saved token file (newest) > the token passed in (env) > MS_REFRESH_TOKEN.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import threading
import time
from pathlib import Path

import requests

E = os.environ.get
SCOPE = "https://outlook.office.com/SMTP.Send https://outlook.office.com/IMAP.AccessAsUser.All offline_access"
_lock = threading.Lock()


def token_dir() -> Path:
    if E("MS_TOKEN_DIR"):
        return Path(E("MS_TOKEN_DIR"))
    if E("ALEX_DATA_DIR"):
        return Path(E("ALEX_DATA_DIR")).resolve().parent / "ms-tokens"
    return Path(__file__).resolve().parent / "data" / "ms-tokens"


def _file(user: str) -> Path:
    safe = "".join(ch for ch in user.lower() if ch.isalnum() or ch in "@._-")
    return token_dir() / f"{safe}.json"


def stored(user: str | None) -> str:
    """The saved refresh token for a mailbox, or ''."""
    if not user:
        return ""
    try:
        return json.loads(_file(user).read_text()).get("refresh_token", "")
    except (OSError, ValueError):
        return ""


def save(user: str, refresh_token: str) -> None:
    f = _file(user)
    with _lock:
        f.parent.mkdir(parents=True, exist_ok=True)
        tmp = f.with_suffix(".tmp")
        tmp.write_text(json.dumps({"user": user.lower(), "refresh_token": refresh_token, "saved_at": int(time.time())}))
        os.chmod(tmp, 0o600)
        tmp.replace(f)
_cache: dict = {}  # refresh token -> {"tok", "exp", "refresh"}


def _url(path: str) -> str:
    return f"https://login.microsoftonline.com/{E('MS_TENANT_ID', 'organizations')}/oauth2/v2.0/{path}"


def access_token(refresh_token: str | None = None, user: str | None = None) -> str:
    """Access token for a mailbox. Saved token file first, then the token passed in, then MS_REFRESH_TOKEN.
    New refresh tokens Microsoft hands back are saved for that mailbox."""
    key = stored(user) or refresh_token or E("MS_REFRESH_TOKEN", "")
    if not key:
        raise RuntimeError(f"no Microsoft sign-in for {user or 'this mailbox'}: open /admin/ms-login on Alex's server")
    c = _cache.setdefault(user.lower() if user else key, {})
    if c.get("exp", 0) > time.time() + 60 and c.get("src") == key:
        return c["tok"]
    r = requests.post(_url("token"), timeout=30, data={
        "client_id": E("MS_CLIENT_ID", ""), "grant_type": "refresh_token",
        "refresh_token": key, "scope": SCOPE})
    if r.status_code >= 400:
        d = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        raise RuntimeError(f"Microsoft token refresh failed for {user}: {d.get('error_description', r.text)[:200]}")
    d = r.json()
    new = d.get("refresh_token") or key
    if user and new != key:
        save(user, new)
    c.update(tok=d["access_token"], exp=time.time() + int(d.get("expires_in", 3600)), src=new)
    return d["access_token"]


def xoauth2(user: str, refresh_token: str | None = None) -> str:
    """Raw SASL XOAUTH2 string (not base64): for imaplib.authenticate and smtplib auth."""
    return f"user={user}\x01auth=Bearer {access_token(refresh_token, user)}\x01\x01"


def smtp_login(s, user: str, refresh_token: str | None = None) -> None:
    s.ehlo()
    code, resp = s.docmd("AUTH", "XOAUTH2 " + base64.b64encode(xoauth2(user, refresh_token).encode()).decode())
    if code != 235:
        raise RuntimeError(f"SMTP XOAUTH2 failed: {code} {resp!r}")


_flows: dict = {}  # user -> {"state", "message", "user_code", "verification_uri", "expires", "error"}


def _poll(user: str, d: dict) -> None:
    f = _flows[user]
    deadline = time.time() + int(d.get("expires_in", 900))
    while time.time() < deadline:
        time.sleep(d.get("interval", 5))
        try:
            t = requests.post(_url("token"), timeout=30, data={
                "client_id": E("MS_CLIENT_ID", ""), "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "device_code": d["device_code"]}).json()
        except requests.RequestException:
            continue
        if "refresh_token" in t:
            who = _signed_in_as(t.get("id_token", ""))
            if who and who != user and who.split("@")[0] != user.split("@")[0]:
                f.update(state="error", error=f"signed in as {who}, not {user}. Try again and pick {user}.")
                return
            try:
                save(user, t["refresh_token"])
            except OSError as e:
                f.update(state="error", error=f"signed in, but the token couldn't be saved to {token_dir()}: {e}")
                return
            _cache.pop(user, None)
            f.update(state="done")
            return
        if t.get("error") not in ("authorization_pending", "slow_down"):
            f.update(state="error", error=t.get("error_description", str(t))[:300])
            return
    f.update(state="error", error="the code expired; start again")


def _signed_in_as(id_token: str) -> str:
    try:
        part = id_token.split(".")[1]
        claims = json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))
        return (claims.get("preferred_username") or claims.get("email") or "").lower()
    except (IndexError, ValueError):
        return ""


def start_login(user: str) -> dict:
    """Start a device-code sign-in for a mailbox in the background; the token is saved when it completes."""
    user = user.lower()
    cur = _flows.get(user)
    if cur and cur.get("state") == "pending" and cur.get("expires", 0) > time.time():
        return cur
    r = requests.post(_url("devicecode"), timeout=30,
                      data={"client_id": E("MS_CLIENT_ID", ""), "scope": SCOPE + " openid profile"})
    if r.status_code >= 400:
        raise RuntimeError(r.json().get("error_description", r.text)[:300])
    d = r.json()
    _flows[user] = {"state": "pending", "message": d["message"], "user_code": d["user_code"],
                    "verification_uri": d["verification_uri"], "expires": time.time() + int(d.get("expires_in", 900))}
    threading.Thread(target=_poll, args=(user, d), daemon=True).start()
    return _flows[user]


def status(user: str) -> dict:
    user = user.lower()
    f = _flows.get(user)
    if f and f.get("state") == "pending" and f.get("expires", 0) < time.time():
        f.update(state="error", error="the code expired; start again")
    if f and f.get("state") in ("pending", "error"):
        return f
    return {"state": "done" if stored(user) else "none"}


def login(user: str = "") -> None:
    """Command-line sign-in. With a mailbox name the token is saved for it; without, it is printed."""
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
            if user:
                save(user, t["refresh_token"])
                print(f"\nSaved for {user} in {token_dir()}")
            else:
                print("\nStore this as the MS_REFRESH_TOKEN secret on the server:\n" + t["refresh_token"])
            return
        if t.get("error") not in ("authorization_pending", "slow_down"):
            sys.exit(f"login failed: {t.get('error_description', t)}")


if __name__ == "__main__" and sys.argv[1:2] == ["login"]:
    login(sys.argv[2] if len(sys.argv) > 2 else "")
