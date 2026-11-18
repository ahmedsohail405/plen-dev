"""Classify replies to Alex and read them from the mailbox (IMAP)."""
from __future__ import annotations

import email
from datetime import datetime, timedelta
import json
import imaplib
import re
from email.header import decode_header, make_header
from email.utils import parseaddr

import config as C

RULES = [  # first match wins
    ("bounce", r"(mailer-daemon|postmaster@|delivery status notification|undeliverable|address not found|delivery has failed|550 5\.)"),
    ("unsubscribe", r"\b(unsubscribe|remove me|take me off|stop emailing|do not (contact|email)|don'?t (contact|email)|opt.?out)\b|^\s*stop[.!]?\s*$"),
    ("out_of_office", r"\b(out of (the )?office|on vacation|away until|auto.?reply|automatic reply|currently away)\b"),
    ("not_interested", r"\b(not interested|no thanks|no thank you|we'?re (all )?(good|set|fine)|already have (a|someone|an agency|a developer)|not at this time|pass on this|please don'?t)\b"),
    ("identity", r"\b(are you (a |an )?(real|human|bot|robot|person|ai|machine)|is this (a |an )?(bot|robot|automated|ai|real person|human)|(written|sent) by (a |an )?(bot|ai|chatgpt)|chat ?gpt|automated (email|message))\b"),
    ("interested", r"\b(interested|sounds good|let'?s (talk|chat|set|do)|call me|give me a call|book|schedule|set up a (call|time|meeting)|available|how much|pricing|price|quote|cost|what would it|send (me )?(more|details|info|some|ideas|designs|examples)|ideas|mock.?ups?|designs?|examples|show me|yes)\b"),
]


def strip_quoted(text: str) -> str:
    keep = []
    for line in text.splitlines():
        if line.startswith(">") or re.match(r"^On .+ wrote:$", line.strip()) or line.strip() in ("--", "-- "):
            break
        keep.append(line)
    return "\n".join(keep).strip()


REFERRAL_RE = re.compile(r"(reach out to|contact|talk to|speak (with|to)|email|get in touch with|forward(ed)? (this|it|you)|"
                         r"cc'?d|copying|looping in|loop in|(right|best) person|handles (our|the) (website|marketing)|in charge of)", re.I)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,24}")


def referral_email(text: str, sender: str = "") -> str:
    """An address the prospect pointed us to ('talk to jim@acme.com'), if any."""
    body = strip_quoted(text)
    if not REFERRAL_RE.search(body):
        return ""
    for e in EMAIL_RE.findall(body):
        if e.lower() != sender.lower() and not e.lower().endswith(("plendev.com", "getplendev.com")):
            return e.lower()
    return ""


def classify(text: str, sender: str = "", subject: str = "") -> str:
    if referral_email(text, sender):
        return "referral"
    body = strip_quoted(text).lower()
    hay = f"{sender} {subject}".lower() + " " + body
    for label, pat in RULES:
        if re.search(pat, hay if label in ("bounce", "out_of_office") else body, re.I):
            return label
    return "question"  # anything else is a human reply Ahmed should see


def _text_of(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and "attachment" not in str(part.get("Content-Disposition")):
                return part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", "replace")
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                html = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", "replace")
                return re.sub(r"<[^>]+>", " ", html)
        return ""
    return msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8", "replace")


def inboxes() -> list[dict]:
    """Every inbox Alex reads replies from.

    - Each ALEX_MAILBOXES entry (sending mailboxes; an entry with "send": false is read-only).
    - ALEX_READ_INBOXES: extra read-only inboxes, same JSON shape, for example the info@ mailbox that
      receives replies to audit@plendev.com emails:
        [{"user": "info@plendev.com", "refresh_env": "AUDIT_MS_REFRESH_TOKEN", "folder": "INBOX"}]
    - Without ALEX_MAILBOXES, the single mailbox from ALEX_IMAP_USER (or SMTP_USER).
    Optional per entry: "imap_host" (default ALEX_IMAP_HOST, else outlook.office365.com), "password_env".
    Alex only PEEKS: nothing is marked read or moved, so shared inboxes look the same to people.
    """
    out = []
    if C.E("ALEX_MAILBOXES"):
        out += json.loads(C.E("ALEX_MAILBOXES"))
    elif C.IMAP_USER or C.E("SMTP_USER"):
        out.append({"user": C.IMAP_USER or C.E("SMTP_USER"),
                    "refresh_env": "MS_REFRESH_TOKEN" if C.E("MS_AUTH", "").lower() == "oauth" else "",
                    "password_env": "" if C.E("MS_AUTH", "").lower() == "oauth" else "ALEX_IMAP_PASS"})
    if C.E("ALEX_READ_INBOXES"):
        out += [b | {"send": False} for b in json.loads(C.E("ALEX_READ_INBOXES"))]
    seen, res = set(), []
    for b in out:
        if b["user"].lower() not in seen:
            seen.add(b["user"].lower())
            res.append(b)
    return res


def imap_login(m, box: dict) -> None:
    if box.get("refresh_env"):
        import ms_oauth  # from audit-agent
        tok = C.E(box["refresh_env"], "")
        if not tok:
            raise RuntimeError(f"{box['refresh_env']} is not set")
        m.authenticate("XOAUTH2", lambda _: ms_oauth.xoauth2(box["user"], tok).encode())
    else:
        pw = C.E(box.get("password_env") or "ALEX_IMAP_PASS", "")
        if not pw:
            raise RuntimeError(f"no password or refresh token for {box['user']}")
        m.login(box["user"], pw)


def _fetch_box(box: dict, days: int = 4) -> list[dict]:
    import store
    host = box.get("imap_host") or C.IMAP_HOST or "outlook.office365.com"
    key = f"imap:{box['user'].lower()}"
    st = store.state().get(key, {})
    out = []
    with imaplib.IMAP4_SSL(host) as m:
        imap_login(m, box)
        m.select(box.get("folder", "INBOX"), readonly=True)
        validity = (m.response("UIDVALIDITY")[1] or [b""])[0]
        validity = validity.decode() if isinstance(validity, bytes) else str(validity or "")
        done = set(st.get("uids", [])) if st.get("validity") == validity else set()
        since = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
        _, ids = m.uid("SEARCH", None, f"SINCE {since}")
        uids = [u.decode() for u in (ids[0] or b"").split()]
        for uid in uids:
            if uid in done:
                continue
            _, data = m.uid("FETCH", uid, "(BODY.PEEK[])")
            raw = next((d[1] for d in data if isinstance(d, tuple)), None)
            done.add(uid)
            if not raw:
                continue
            msg = email.message_from_bytes(raw)
            out.append({
                "from": parseaddr(msg.get("From", ""))[1].lower(),
                "subject": str(make_header(decode_header(msg.get("Subject", "")))),
                "in_reply_to": msg.get("In-Reply-To", ""), "references": msg.get("References", ""),
                "text": _text_of(msg), "date": msg.get("Date", ""), "inbox": box["user"].lower(),
            })
        keep = sorted(done & set(uids), key=int)  # only uids still in the search window
        store.state(**{key: {"validity": validity, "uids": keep}})
    return out


def fetch_unseen() -> list[dict]:
    """New messages from every inbox Alex reads (see inboxes()). Each inbox is read on its own, so one
    bad login doesn't stop the others; errors are raised after the rest are read."""
    boxes = inboxes()
    if not boxes:
        raise RuntimeError("no inbox configured (ALEX_IMAP_USER, ALEX_MAILBOXES or ALEX_READ_INBOXES)")
    out, errs = [], []
    for b in boxes:
        try:
            out += _fetch_box(b)
        except Exception as e:  # noqa: BLE001
            errs.append(f"{b['user']}: {e}")
    if errs and not out:
        raise RuntimeError("; ".join(errs))
    for e in errs:
        print("inbox error:", e)
    return out
