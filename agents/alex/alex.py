#!/usr/bin/env python3
"""Alex: Plen Dev's outbound sales agent.

Pipeline per prospect:
  new -> (robots/suppression/dedupe checks) -> audit -> qualify -> find public email -> draft 3-email sequence
      -> awaiting_approval -> approved -> in_sequence (email 1, follow-up day 3, follow-up day 7)
      -> replied_interested / replied_question -> reply drafted for approval -> booked / won / lost
  Exits: skipped, disqualified, no_contact, opted_out, bounced, not_interested, finished, rejected

Commands
  discover osm --area brooklyn --category dental [--limit 100]
  discover google --query "dentist in Bay Ridge Brooklyn" --category dental --area brooklyn
  discover csv --file list.csv [--category dental --area queens]
  add https://site.com --name "Biz" --category dental --area brooklyn
  process [--limit 10]          audit + qualify + find contact + draft (new prospects)
  queue                         list drafts awaiting approval
  show <id>                     full draft sequence and audit summary
  approve <id> [--subject S] [--note "personal line"]
  reject <id> [--reason R]
  send                          send approved first emails + due follow-ups (window, caps, preflight)
  inbox                         read replies over IMAP and act on them
  reply <id> --text "..."       record a reply by hand (for testing, or replies seen elsewhere)
  booked <id> | won <id> | lost <id>
  suppress <email-or-domain>
  report [--whatsapp]           daily numbers + funnel suggestions
  stats                         counts by status
  learn                         rewrite the playbook from recent replies (needs ALEX_LLM=on)
  work [--once]                 the all-day worker: 9 to 5 Eastern on weekdays it keeps finding, auditing,
                                drafting, sending approved emails and reading replies; daily report after 5
"""
from __future__ import annotations

import argparse
import json
import random
import secrets
import sys
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import config as C
import audit  # from audit-agent (path set in config)
import mailer
import compose
import contacts
import experiments
import mailboxes
import replies
import research
import writer
import sources
import store
from store import event, now

SALES_IDS = compose.PITCHABLE
# Alex's prospect categories as plain words the audit's industry detector and keyword research understand.
# Broad categories are left out so the audit works the industry out from the site itself.
AUDIT_INDUSTRY = {"dental": "dentist", "real_estate": "real estate", "home_healthcare": "home care",
                  "medical": "clinic", "legal": "law firm", "accounting": "accounting", "beauty": "salon",
                  "fitness": "gym", "contractor": "contractor", "trades": "contractor", "restaurant": "restaurant",
                  "auto": "auto repair"}


def log(*a):
    print(*a, flush=True)


# --------------------------------------------------------------------------- intake

def add_prospect(rec: dict) -> tuple[dict | None, str]:
    site = sources.clean_site(rec.get("website", ""))
    if not site:
        return None, "no usable website"
    domain = urlparse(site).hostname.removeprefix("www.")
    pid = store.pid_for(domain)
    if store.get(pid):
        return None, "already known"
    if store.is_suppressed(domain=domain):
        return None, "suppressed"
    p = {"id": pid, "domain": domain, "website": site, "status": "new", "created_at": now(),
         "business_name": rec.get("business_name") or domain, "category": rec.get("category", ""),
         "area": rec.get("area", ""), "address": rec.get("address", ""), "phone": rec.get("phone", ""),
         "listed_email": rec.get("email", ""), "source": rec.get("source", "manual"),
         "source_ref": rec.get("source_ref", ""), "report_token": secrets.token_urlsafe(18),
         "unsub_token": secrets.token_urlsafe(18), "history": [],
         "locations_listed": rec.get("locations_listed", 1)}
    event(p, "discovered", source=p["source"])
    return store.save(p), "added"


def cmd_discover(a):
    if a.source == "osm":
        recs = sources.osm(a.area, a.category, a.limit)
    elif a.source == "google":
        recs = sources.google_places(a.query, a.category, a.area, a.limit)
    else:
        recs = sources.from_csv(a.file, a.category or "", a.area or "")
    log(f"found {len(recs)}, added {ingest(recs)} new prospects")


def ingest(recs: list[dict]) -> int:
    """One prospect per domain. A domain listed at several places is a multi-location company: Alex
    pitches its headquarters (one site, one decision-maker) instead of skipping it."""
    counts = {}
    for r in recs:
        d = urlparse(r["website"]).hostname
        counts[d] = counts.get(d, 0) + 1
    added = 0
    for r in recs:
        n = counts[urlparse(r["website"]).hostname]
        p, why = add_prospect(r | ({"locations_listed": n} if n > 1 else {}))
        added += bool(p)
    return added


def cmd_add(a):
    p, why = add_prospect({"website": a.url, "business_name": a.name, "category": a.category, "area": a.area,
                           "email": a.email or "", "source": "manual"})
    log(why, p["id"] if p else "")


# --------------------------------------------------------------------------- processing

def politeness(site: str):
    """Make the shared audit engine obey robots.txt and crawl slowly for cold prospects."""
    rb = contacts.Robots(site, contacts.session())
    audit.URL_FILTER = rb.ok
    audit.CRAWL_DELAY = rb.delay
    return rb


def qualify(report: dict) -> tuple[bool, str, list]:
    """Rebuild candidates: a weak overall score, or several serious problems even if the score looks OK.
    Thresholds use only the overall score and finding severities, never category weights (which may change)."""
    sc = report["score"]["overall"]
    if report["findings"] and report["findings"][0]["id"] == "home_unreachable":
        return False, "site did not load", []
    p_issues = [f for f in report["findings"] if f["id"] in SALES_IDS and f["severity"] in ("critical", "high", "medium")]
    serious = [f for f in p_issues if f["severity"] in ("critical", "high")]
    if len(p_issues) < C.MIN_ISSUES:
        return False, f"only {len(p_issues)} issue(s) worth pitching", p_issues
    if sc <= C.MAX_SCORE or len(serious) >= C.MIN_SERIOUS:
        return True, f"score {sc}/100, {len(serious)} serious issues", p_issues
    return False, f"site is in good shape ({sc}/100, {len(serious)} serious issues)", p_issues


def process_one(p: dict) -> dict:
    site = p["website"]
    if not public_target(site):
        p["status"], p["reason"] = "skipped", "not a public website"
        return store.save(p)
    rb = politeness(site)
    if not rb.ok(site):
        p["status"], p["reason"] = "skipped", "robots.txt disallows our crawler"
        event(p, "skipped", reason=p["reason"])
        return store.save(p)
    out = store.path(p["id"]).parent / "audit"
    log(f"auditing {site} ...")
    report = audit.run_audit(site, {"name": "", "company": p["business_name"], "website_url": site,
                                    "industry": AUDIT_INDUSTRY.get(p.get("category") or "", ""), "category": ""}, out,
                             C.AUDIT_PAGES, C.PSI_KEY,
                             brand=audit.BRAND | {"booking_url": C.BOOKING_URL or C.SITE}, report_url="", visual=C.VISUAL)
    for f in ("email.html", "email.txt", "email.json"):  # inbound-audit email, not used for cold outreach
        (out / f).unlink(missing_ok=True)
    group, customers = compose.INDUSTRY.get(p.get("category", ""), ("", "customers"))
    p["audit"] = {"score": report["score"]["overall"], "grade": audit.grade(report["score"]["overall"]),
                  "counts": report["counts"], "categories": report["score"]["categories"],
                  "pages": report["pages_crawled"], "at": report["generated_at"],
                  "pitch": compose.pitch_points(report, customers)}
    event(p, "audited", score=p["audit"]["score"])
    ok, why, _ = qualify(report)
    if not ok:
        p["status"], p["reason"] = "disqualified", why
        event(p, "disqualified", reason=why)
        return store.save(p)
    try:
        p["research"] = research.research(site)
    except Exception as e:  # noqa: BLE001
        p["research"] = {"error": str(e)[:200]}
    p["audit"]["more"] = [compose.PITCH[k](f, customers) for k, f in compose.extra_points(report, customers, skip=p["audit"]["pitch"])]
    c = contacts.find_contact(site, p.get("listed_email", ""))
    local = c["email"].split("@")[0] if c["email"] else ""
    people = (p.get("research") or {}).get("people", [])
    p["contact"] = {"email": c["email"], "source_url": c["source_url"], "candidates": c["candidates"][:5],
                    "general": (local.split(".")[0] in contacts.ROLE) or not people,
                    "person": next((f"{x['name']} ({x['role']})" for x in people
                                    if x["name"].split()[-1].lower() in local.lower()), None)}
    if not c["email"]:
        p["status"], p["reason"] = "no_contact", "no publicly listed email found"
        event(p, "no_contact")
        return store.save(p)
    if store.is_suppressed(c["email"], p["domain"]):
        p["status"], p["reason"] = "skipped", "suppressed"
        return store.save(p)
    p["variant"] = experiments.choose()
    draft_sequence(p)
    p["status"] = "awaiting_approval"
    event(p, "drafted", to=c["email"])
    store.save(p)
    notify(f"Alex drafted outreach to {p['business_name']} ({p['domain']}), score {p['audit']['score']}/100, "
           f"to {c['email']}. Review: alex.py show {p['id']}")
    return p


def draft_sequence(p: dict) -> None:
    """Emails 1-3. Claude writes them when ALEX_LLM=on (falls back to templates on any error)."""
    p["sequence"] = {"subject": compose.subject_for(p, p["audit"]["pitch"]), "step": 0, "sent": []}
    if writer.enabled():
        try:
            drafts = {}
            for step in (1, 2, 3):
                w = writer.write(p | {"variant_instructions": experiments.instructions(p.get("variant", {}))}, step)
                if step == 1:
                    p["sequence"]["subject"] = w["subject"]
                drafts[str(step)] = compose.finish(step, p, w["subject"] if step == 1 else f"Re: {p['sequence']['subject']}", w["body"])
            p["drafts"], p["writer"] = drafts, writer.MODEL
            return
        except Exception as e:  # noqa: BLE001
            log("writer failed, using templates:", e)
    p["drafts"], p["writer"] = {str(s): compose.render(s, p) for s in (1, 2, 3)}, "templates"


def public_target(url: str) -> bool:
    import ipaddress, socket
    if C.E("ALLOW_PRIVATE_TARGETS", "false") == "true":
        return True
    host = urlparse(url).hostname or ""
    try:
        return all(ipaddress.ip_address(ai[4][0]).is_global for ai in socket.getaddrinfo(host, None))
    except (socket.gaierror, ValueError):
        return False


def cmd_process(a):
    todo = store.all_prospects("new")[: a.limit]
    for p in todo:
        try:
            p = process_one(p)
            log(f"  {p['id']}: {p['status']} {p.get('reason', '')}")
        except Exception as e:  # noqa: BLE001
            p["status"], p["reason"] = "error", str(e)[:300]
            event(p, "error", error=str(e)[:300])
            store.save(p)
            log(f"  {p['id']}: error {e}")


# --------------------------------------------------------------------------- approval

def cmd_queue(a):
    items = store.all_prospects("awaiting_approval")
    if not items:
        return log("nothing awaiting approval")
    for p in items:
        log(f"{p['id']:<34} {p['audit']['score']:>3}/100  {p['contact']['email']:<32} {p['drafts']['1']['subject']}")


def cmd_show(a):
    p = store.get(a.id)
    if not p:
        return log("unknown id")
    log(f"{p['business_name']}  {p['website']}  status={p['status']}  {p.get('reason', '')}")
    if p.get("audit"):
        log(f"score {p['audit']['score']}/100  counts {p['audit']['counts']}")
    if p.get("contact"):
        log(f"to: {p['contact']['email']}  (found on {p['contact']['source_url']})")
    for s, d in (p.get("drafts") or {}).items():
        log(f"\n===== email {s}: {d['subject']}\n{d['text']}")
    if p.get("reply_draft"):
        d = p["reply_draft"]
        log(f"\n===== reply draft ({d['step']}): {d['subject']}\n{d['text']}")


def cmd_approve(a):
    p = store.get(a.id)
    if not p or p["status"] not in ("awaiting_approval", "reply_awaiting_approval"):
        return log(f"cannot approve: status is {p and p['status']}")
    if p["status"] == "reply_awaiting_approval":
        d = p["reply_draft"]
        if a.text:
            d["text"], d["html"] = a.text, compose.to_html(a.text)
        if "[Ahmed:" in d["text"]:
            raise SystemExit("this draft still has a placeholder for your answer; send it with edited text (WhatsApp: edit <id>: <text>)")
        return send_email(p, d, kind="reply")
    if a.subject:
        p["sequence"]["subject"] = a.subject
        p["drafts"] = {str(s): compose.render(s, p) for s in (1, 2, 3)}
    if a.note:
        d = p["drafts"]["1"]
        first, rest = d["text"].split("\n\n", 1)
        d["text"] = f"{first}\n\n{a.note.strip()}\n\n{rest}"
        d["html"] = compose.to_html(d["text"])
    p["status"] = "approved"
    event(p, "approved", by="ahmed")
    store.save(p)
    log(f"approved {p['id']}; it goes out in the next send window")


def cmd_reject(a):
    p = store.get(a.id)
    p["status"], p["reason"] = "rejected", a.reason or ""
    event(p, "rejected", reason=a.reason)
    store.save(p)
    log("rejected")


# --------------------------------------------------------------------------- sending

def local_now() -> datetime:
    return datetime.now(ZoneInfo(C.TZ))


def in_window(t: datetime) -> bool:
    return t.weekday() in C.SEND_DAYS and C.SEND_HOURS[0] <= t.hour < C.SEND_HOURS[1]


def send_email(p: dict, d: dict, kind: str = "sequence", box: dict | None = None) -> bool:
    to = d.get("to") or p["contact"]["email"]
    if store.is_suppressed(to, p["domain"] if to == p["contact"]["email"] else ""):
        if to == p["contact"]["email"]:
            p["status"] = "opted_out"
            store.save(p)
        return False
    t = local_now()
    box = box or mailboxes.for_prospect(p, t) or (mailboxes.pool() or [None])[0]
    unsub_http = f"{C.PUBLIC_BASE}/u/{p['unsub_token']}"
    headers = {"List-Unsubscribe": f"<{unsub_http}>", "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"}
    if p["sequence"].get("message_ids") and to == p["contact"]["email"]:  # keep the thread together
        headers["In-Reply-To"] = p["sequence"]["message_ids"][-1]
        headers["References"] = " ".join(p["sequence"]["message_ids"])
    prov = C.E("MAIL_PROVIDER", "dryrun")
    if C.SEND_ENABLED and prov != "dryrun":
        errs = C.preflight_errors(box)
        if errs:
            raise SystemExit("refusing to send, missing: " + "; ".join(errs))
    elif prov != "dryrun":
        raise SystemExit("ALEX_SEND_ENABLED is false; set MAIL_PROVIDER=dryrun or enable sending")
    mid = mailer.send(to=to, subject=d["subject"], html=d["html"], text=d["text"], headers=headers,
                      from_addr=box["from"] if box else C.MAIL_FROM, reply_to=C.REPLY_TO, bcc=C.BCC,
                      smtp=mailboxes.smtp_settings(box) if box else None)
    p["mailbox"] = box["id"] if box else p.get("mailbox")
    if to != p["contact"]["email"]:  # referral: the conversation continues with the person they pointed us to
        p["contact"] = {"email": to, "source_url": f"referred by {p['contact']['email']}", "general": False,
                        "candidates": [], "person": None}
        p["sequence"]["message_ids"] = []
    p["sequence"].setdefault("message_ids", []).append(mid if mid.startswith("<") else f"<{mid}>")
    if kind == "sequence":
        p["sequence"]["step"] = d["step"]
        p["sequence"]["sent"].append({"step": d["step"], "at": now(), "id": mid, "subject": d["subject"]})
        gaps = C.FOLLOWUP_DAYS
        if d["step"] <= len(gaps):
            p["sequence"]["next_due"] = (datetime.now(timezone.utc) + timedelta(days=gaps[d["step"] - 1])).isoformat(timespec="seconds")
            p["status"] = "in_sequence"
        else:
            p["sequence"]["next_due"] = None
            p["status"] = "finished"
    else:
        p.setdefault("replies_sent", []).append({"at": now(), "id": mid, "kind": d["step"], "to": to})
        p["status"] = "in_conversation"
        p.pop("reply_draft", None)
        wa(f"Alex sent your approved reply to {p['business_name']} ({to}).")
    event(p, "sent", step=d["step"], provider_id=mid, to=to)
    store.save(p)
    store.log({"event": "sent", "id": p["id"], "to": to, "step": d["step"], "kind": kind,
               "local_day": t.strftime("%Y-%m-%d"), "provider": prov, "mailbox": box["id"] if box else ""})
    log(f"sent {d['step']} to {to} ({p['id']}) via {prov} from {box['id'] if box else '-'}")
    return True


def due_emails() -> list[tuple]:
    """Follow-ups first (they keep warm threads alive), then approved first emails."""
    due, nowu = [], datetime.now(timezone.utc)
    for p in store.all_prospects("in_sequence"):
        nd = p["sequence"].get("next_due")
        if nd and datetime.fromisoformat(nd) <= nowu:
            due.append((p, p["drafts"][str(p["sequence"]["step"] + 1)]))
    for p in store.all_prospects("approved"):
        due.append((p, p["drafts"]["1"]))
    return due


def send_some(limit: int | None = None, gap: bool = True) -> int:
    """Send what's due, within each mailbox's warm-up cap. Never two emails to one company domain per run."""
    t = local_now()
    sent, domains = 0, set()
    for p, d in due_emails():
        if limit is not None and sent >= limit:
            break
        dom = p["contact"]["email"].split("@")[-1]
        if dom in domains and dom not in contacts.FREEMAIL:
            continue
        box = mailboxes.for_prospect(p, t)
        if not box or mailboxes.remaining(box, t) <= 0:
            continue
        if sent and gap:
            time.sleep(C.MIN_GAP + random.randint(0, 60))
        if send_email(p, d, box=box):
            sent += 1
            domains.add(dom)
    return sent


def cmd_send(a):
    t = local_now()
    if not a.ignore_window and not in_window(t):
        return log(f"outside send window ({t:%a %H:%M} {C.TZ}); nothing sent")
    if mailboxes.total_remaining(t) <= 0:
        return log("daily cap reached (or warm-up not started: set warmup_start / ALEX_WARMUP_START)")
    log(f"sent {send_some(gap=not a.no_gap)}")


# --------------------------------------------------------------------------- replies

def match_prospect(msg: dict) -> dict | None:
    ref = f"{msg.get('in_reply_to', '')} {msg.get('references', '')}"
    for p in store.all_prospects():
        ids = (p.get("sequence") or {}).get("message_ids", [])
        if any(i and i in ref for i in ids):
            return p
        if p.get("contact", {}).get("email") == msg["from"]:
            return p
    return None


def wa(text: str) -> None:
    """Forward to Ahmed on WhatsApp (Ahmed 2026-11-17: every client reply and conversation)."""
    if C.WHATSAPP_FORWARD:
        import whatsapp
        try:
            whatsapp.send(text)
        except Exception as e:  # noqa: BLE001
            log("whatsapp failed:", e)


def draft_reply(p: dict, kind: str, said: str, demos_: list | None = None) -> dict:
    """Claude writes the reply when ALEX_LLM=on; templates otherwise. Identity questions always use the
    fixed honest template so the answer can't drift."""
    if writer.enabled() and kind != "identity":
        try:
            thread = [{"from": "Alex", "text": d.get("text", "")[:1500]} for d in (p.get("drafts") or {}).values()][:1]
            thread += [{"from": "them" if r.get("from") != C.MAIL_FROM else "Alex", "text": r["text"][:1500]} for r in p.get("replies", [])]
            w = writer.write(p, "reply", said, [{"name": d["name"], "url": d["url"]} for d in demos_ or []], thread)
            d = compose.finish(f"reply_{kind}", p, f"Re: {p['sequence']['subject']}", w["body"], reply=kind != "referral")
            return d
        except Exception as e:  # noqa: BLE001
            log("writer failed, using templates:", e)
    tmpl = {"identity": "identity", "interested": "interested", "referral": "referral"}.get(kind, "question")
    return compose.render_reply(tmpl, p, said, demos_)


def handle_reply(p: dict, text: str, sender: str = "", subject: str = "") -> str:
    kind = replies.classify(text, sender, subject)
    said = replies.strip_quoted(text)
    p.setdefault("replies", []).append({"at": now(), "kind": kind, "from": sender, "text": said[:4000]})
    event(p, "reply", kind=kind)
    store.log({"event": "reply", "id": p["id"], "kind": kind})
    head = f"{p['business_name']} ({p['domain']}) replied [{kind}]:\n\"{said[:700]}\""
    if kind == "bounce":
        p["status"] = "bounced"
        store.suppress(p["contact"]["email"], "bounce")
    elif kind == "unsubscribe":
        p["status"] = "opted_out"
        store.suppress(p["contact"]["email"], "unsubscribe reply")
        store.suppress(p["domain"], "unsubscribe reply")
        wa(head + "\n\nAlex removed them from all emails.")
    elif kind == "not_interested":
        p["status"] = "not_interested"
        store.suppress(p["domain"], "not interested")
        wa(head + "\n\nAlex marked them not interested and won't email again.")
    elif kind == "out_of_office":
        if p["status"] == "in_sequence":  # push the next follow-up back a week
            p["sequence"]["next_due"] = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(timespec="seconds")
    elif kind == "referral":
        ref = replies.referral_email(text, sender)
        p["status"] = "reply_awaiting_approval"
        p["sequence"]["next_due"] = None
        p["referral"] = {"email": ref, "from": sender, "at": now()}
        intro = draft_reply(p | {"referred_by": sender}, "referral", said)
        intro["to"] = ref
        p["reply_draft"] = intro
        wa(head + f"\n\nThey pointed Alex to {ref}. Draft intro to {ref}:\n{intro['text'][:900]}\n\n"
           f"Reply \"approve {p['id']}\" to send it, or \"reject {p['id']}\".")
    else:  # interested, question or "are you a bot?": stop the sequence, draft an answer, ask Ahmed
        p["status"] = "reply_awaiting_approval"
        p["sequence"]["next_due"] = None
        demos_ = []
        if kind in ("interested", "question"):
            try:
                import demos
                demos_ = p.get("demos") or demos.build(p)
            except Exception as e:  # noqa: BLE001
                log("demo build failed:", e)
        p["reply_draft"] = draft_reply(p, kind, said, demos_)
        msg = (head + f"\n\nAlex's draft reply:\n{p['reply_draft']['text'][:900]}\n\n"
               + (f"Demo designs ({len(demos_)}): " + "  ".join(d["url"] for d in demos_) + "\n\n" if demos_ else "")
               + f"Reply \"approve {p['id']}\" to send, \"reject {p['id']}\" to drop it, or \"edit {p['id']}: <new text>\".")
        wa(msg)
        notify(f"{p['business_name']} replied ({kind}). Draft waiting: alex.py show {p['id']}")
    store.save(p)
    return kind


def cmd_inbox(a):
    for msg in replies.fetch_unseen():
        p = match_prospect(msg)
        if p:
            log(p["id"], handle_reply(p, msg["text"], msg["from"], msg["subject"]))
        elif msg.get("inbox") in {b["id"] for b in mailboxes.pool()}:  # don't log other mail in shared inboxes
            log("unmatched reply from", msg["from"], msg["subject"])


def cmd_reply(a):
    p = store.get(a.id)
    log(handle_reply(p, a.text, p["contact"]["email"]))


def cmd_mark(a, status):
    p = store.get(a.id)
    p["status"] = status
    event(p, status)
    store.save(p)
    store.log({"event": status, "id": p["id"]})
    log(f"{p['id']} -> {status}")


def cmd_suppress(a):
    store.suppress(a.entry, "manual")
    log("suppressed", a.entry)


# --------------------------------------------------------------------------- reporting

def notify(text: str) -> None:
    log("[notify]", text)
    if C.NOTIFY_WEBHOOK:
        import requests
        try:
            requests.post(C.NOTIFY_WEBHOOK, json={"text": text, "content": text}, timeout=10)
        except requests.RequestException:
            pass


def cmd_stats(a):
    c = {}
    for p in store.all_prospects():
        c[p["status"]] = c.get(p["status"], 0) + 1
    log(json.dumps(c, indent=2))


def cmd_report(a):
    import report
    text = report.build()
    if a.whatsapp:
        import whatsapp
        whatsapp.send(text)
    else:
        log(text)


# --------------------------------------------------------------------------- the all-day worker

def pipeline_size() -> int:
    return len(store.all_prospects("awaiting_approval")) + len(store.all_prospects("approved"))


def discover_next() -> int:
    """Next (area, category) from the plan, with a saved cursor so Alex covers every pair before repeating."""
    cur = store.state()
    plan = sources.plan()
    i = cur.get("cursor", 0) % len(plan)
    area, cat = plan[i]
    store.state(cursor=i + 1)
    if C.GOOGLE_PLACES_KEY:
        q = f"{cat.replace('_', ' ')} in {area.replace('_', ' ').title()}"
        recs = sources.google_places(q, cat, area, 60)
    else:
        recs = sources.osm(area, cat, 200)
    n = ingest(recs)
    log(f"discover {area}/{cat}: {len(recs)} found, {n} new")
    return n


def tick(t: datetime) -> dict:
    """One pass of the worker. Every step is safe to repeat."""
    did = {}
    st = store.state()
    # 1. replies come first: a lead waiting on Alex is worth more than a new prospect
    if time.time() - st.get("inbox_at", 0) >= C.INBOX_EVERY:
        try:
            for msg in replies.fetch_unseen():
                p = match_prospect(msg)
                if p:
                    did.setdefault("replies", []).append((p["id"], handle_reply(p, msg["text"], msg["from"], msg["subject"])))
        except Exception as e:  # noqa: BLE001
            log("inbox error:", e)
        store.state(inbox_at=time.time())
    # 2. send one due email if this is the right moment (spreads the day's budget across the window)
    left = mailboxes.total_remaining(t)
    end = t.replace(hour=C.SEND_HOURS[1], minute=0, second=0, microsecond=0)
    mins_left = max((end - t).total_seconds() / 60, 1)
    spacing = max(C.MIN_GAP / 60, mins_left / max(left, 1))
    # With MAIL_PROVIDER=dryrun the worker sends nothing (so approved emails aren't used up by fake sends),
    # unless ALEX_DRYRUN_SEND=true for testing.
    if C.E("MAIL_PROVIDER", "dryrun") == "dryrun":
        can_send = C.E("ALEX_DRYRUN_SEND", "false").lower() == "true"
    else:
        can_send = C.SEND_ENABLED and not C.preflight_errors()
    if left > 0 and time.time() - st.get("sent_at", 0) >= spacing * 60 and can_send:
        n = send_some(limit=1, gap=False)
        if n:
            store.state(sent_at=time.time())
            did["sent"] = n
    # 3. keep a buffer of drafts for Ahmed to approve: about two days of sending
    target = 2 * sum(mailboxes.cap_today(b, t) for b in mailboxes.pool()) or 2 * C.DAILY_CAP
    if pipeline_size() < target:
        todo = store.all_prospects("new")[:3]
        if not todo:
            try:
                did["discovered"] = discover_next()
            except Exception as e:  # noqa: BLE001
                log("discover error:", e)
        for p in todo:
            try:
                p = process_one(p)
            except Exception as e:  # noqa: BLE001
                p["status"], p["reason"] = "error", str(e)[:300]
                store.save(p)
            did.setdefault("processed", []).append((p["id"], p["status"]))
    return did


def after_hours(t: datetime) -> None:
    """Once a day after 5 PM: WhatsApp report. Once a week: refresh the playbook."""
    st, day = store.state(), t.strftime("%Y-%m-%d")
    if st.get("report_day") != day:
        import report
        import whatsapp
        try:
            whatsapp.send(report.build())
        except Exception as e:  # noqa: BLE001
            log("report error:", e)
        store.state(report_day=day)
    if writer.enabled() and time.time() - st.get("learn_at", 0) > 7 * 86400:
        import learn
        try:
            learn.run()
        except Exception as e:  # noqa: BLE001
            log("learn error:", e)
        store.state(learn_at=time.time())


def cmd_work(a):
    """Runs until stopped. Outside 9 to 5 Eastern on weekdays it only reads replies (every 30 min) so
    Ahmed still hears about them, and sends nothing."""
    log(f"Alex at work. Window {C.SEND_HOURS[0]}:00 to {C.SEND_HOURS[1]}:00 {C.TZ}, days {C.SEND_DAYS}")
    probs = C.preflight_errors()
    if probs:
        log("sending is off until fixed:", "; ".join(probs))
    while True:
        t = local_now()
        if in_window(t):
            did = tick(t)
            if did:
                log(t.strftime("%H:%M"), json.dumps(did, default=str))
        else:
            if t.weekday() in C.SEND_DAYS and t.hour >= C.SEND_HOURS[1]:
                after_hours(t)
            if time.time() - store.state().get("inbox_at", 0) >= 1800:
                try:
                    for msg in replies.fetch_unseen():
                        p = match_prospect(msg)
                        if p:
                            handle_reply(p, msg["text"], msg["from"], msg["subject"])
                except Exception as e:  # noqa: BLE001
                    log("inbox error:", e)
                store.state(inbox_at=time.time())
        if a.once:
            return
        time.sleep(C.TICK)


def cmd_learn(a):
    import learn
    log(learn.run())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    d = sp.add_parser("discover"); d.add_argument("source", choices=["osm", "google", "csv"])
    d.add_argument("--area", default="brooklyn"); d.add_argument("--category", default="dental")
    d.add_argument("--query"); d.add_argument("--file"); d.add_argument("--limit", type=int, default=100)
    x = sp.add_parser("add"); x.add_argument("url"); x.add_argument("--name", default="")
    x.add_argument("--category", default=""); x.add_argument("--area", default=""); x.add_argument("--email")
    x = sp.add_parser("process"); x.add_argument("--limit", type=int, default=10)
    sp.add_parser("queue"); sp.add_parser("stats"); sp.add_parser("inbox")
    x = sp.add_parser("show"); x.add_argument("id")
    x = sp.add_parser("approve"); x.add_argument("id"); x.add_argument("--subject"); x.add_argument("--note"); x.add_argument("--text")
    x = sp.add_parser("reject"); x.add_argument("id"); x.add_argument("--reason")
    x = sp.add_parser("send"); x.add_argument("--ignore-window", action="store_true"); x.add_argument("--no-gap", action="store_true")
    x = sp.add_parser("reply"); x.add_argument("id"); x.add_argument("--text", required=True)
    for s in ("booked", "won", "lost"):
        x = sp.add_parser(s); x.add_argument("id")
    x = sp.add_parser("suppress"); x.add_argument("entry")
    x = sp.add_parser("report"); x.add_argument("--whatsapp", action="store_true")
    sp.add_parser("learn")
    x = sp.add_parser("work"); x.add_argument("--once", action="store_true")
    a = ap.parse_args()
    fn = {"discover": cmd_discover, "add": cmd_add, "process": cmd_process, "queue": cmd_queue, "show": cmd_show,
          "approve": cmd_approve, "reject": cmd_reject, "send": cmd_send, "inbox": cmd_inbox, "reply": cmd_reply,
          "suppress": cmd_suppress, "report": cmd_report, "stats": cmd_stats,
          "learn": cmd_learn, "work": cmd_work,
          "booked": lambda a: cmd_mark(a, "booked"), "won": lambda a: cmd_mark(a, "won"),
          "lost": lambda a: cmd_mark(a, "lost")}[a.cmd]
    fn(a)


if __name__ == "__main__":
    sys.exit(main())
