"""Classify replies to Alex and read them from the mailbox (IMAP)."""
from __future__ import annotations

import email
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


def imap_login(m) -> None:
    if C.E("MS_AUTH", "").lower() == "oauth":
        import ms_oauth  # from audit-agent
        m.authenticate("XOAUTH2", lambda _: ms_oauth.xoauth2(C.IMAP_USER).encode())
    else:
        m.login(C.IMAP_USER, C.IMAP_PASS)


def fetch_unseen() -> list[dict]:
    """Unread messages in the Alex mailbox. Needs ALEX_IMAP_HOST/USER/PASS."""
    oauth = C.E("MS_AUTH", "").lower() == "oauth"
    if not (C.IMAP_HOST and C.IMAP_USER and (C.IMAP_PASS or oauth)):
        raise RuntimeError("IMAP is not configured (ALEX_IMAP_HOST / ALEX_IMAP_USER / ALEX_IMAP_PASS or MS_AUTH=oauth)")
    out = []
    with imaplib.IMAP4_SSL(C.IMAP_HOST) as m:
        imap_login(m)
        m.select("INBOX")
        _, ids = m.search(None, "UNSEEN")
        for i in ids[0].split():
            _, data = m.fetch(i, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])
            out.append({
                "from": parseaddr(msg.get("From", ""))[1].lower(),
                "subject": str(make_header(decode_header(msg.get("Subject", "")))),
                "in_reply_to": msg.get("In-Reply-To", ""), "references": msg.get("References", ""),
                "text": _text_of(msg), "date": msg.get("Date", ""),
            })
    return out
