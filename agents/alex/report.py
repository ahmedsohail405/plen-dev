"""Alex's daily report: numbers for the last 24 hours, running totals, and funnel suggestions.

Suggestions are rule-based on Alex's own numbers (reply, bounce, opt-out and booking rates,
which industries and which opening issues get replies). They are hints for Ahmed, not changes
Alex makes on its own.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

import config as C
import store

ISSUE_NAMES = {"no_viewport": "not mobile-friendly", "psi_mobile_poor": "slow on phones", "lcp": "slow on phones",
               "no_https": "no HTTPS / \"Not secure\"", "no_cta": "no clear call to action", "no_form": "no contact form",
               "no_phone": "no phone number on the homepage"}


def plural(n: int, one: str, many: str) -> str:
    return f"{n} {one if n == 1 else many}"


ACTIVE = ("reply_awaiting_approval", "in_conversation", "booked")


def _since(ts: str, hours: int) -> bool:
    return datetime.fromisoformat(ts) >= datetime.now(timezone.utc) - timedelta(hours=hours)


def numbers(hours: int = 24) -> dict:
    log = [json.loads(l) for l in store.SENDLOG.read_text().splitlines()] if store.SENDLOG.exists() else []
    ps = store.all_prospects()
    day = [r for r in log if _since(r["at"], hours)]
    sent = [r for r in day if r["event"] == "sent"]
    rep = [r for r in day if r["event"] == "reply"]
    all_sent = [r for r in log if r["event"] == "sent"]
    all_rep = [r for r in log if r["event"] == "reply"]
    status = Counter(p["status"] for p in ps)
    first_sends = [r for r in all_sent if r.get("step") == 1]
    return {
        "day": {
            "first_emails": sum(1 for r in sent if r.get("step") == 1),
            "follow_ups": sum(1 for r in sent if r.get("step") in (2, 3)),
            "replies_sent": sum(1 for r in sent if r.get("kind") == "reply"),
            "replies": Counter(r["kind"] for r in rep),
            "new_prospects": sum(1 for p in ps if _since(p["created_at"], hours)),
            "audited": sum(1 for p in ps for h in p.get("history", []) if h["event"] == "audited" and _since(h["at"], hours)),
            "booked": sum(1 for r in day if r["event"] == "booked"),
        },
        "total": {
            "contacted": len({r["id"] for r in first_sends}),
            "emails_sent": len(all_sent),
            "human_replies": sum(1 for r in all_rep if r["kind"] in ("interested", "question", "referral", "not_interested")),
            "positive_replies": sum(1 for r in all_rep if r["kind"] in ("interested", "question", "referral")),
            "bounces": sum(1 for r in all_rep if r["kind"] == "bounce"),
            "opt_outs": sum(1 for r in all_rep if r["kind"] == "unsubscribe"),
            "booked": status["booked"] + status["won"],
            "won": status["won"],
        },
        "pipeline": {
            "awaiting_your_approval": status["awaiting_approval"] + status["reply_awaiting_approval"],
            "in_conversation": sum(status[s] for s in ACTIVE),
            "in_sequence": status["in_sequence"] + status["approved"],
            "to_audit": status["new"],
            "no_contact_found": status["no_contact"],
            "disqualified": status["disqualified"],
        },
        "prospects": ps,
    }


def suggestions(n: dict) -> list[str]:
    t, ps, out = n["total"], n["prospects"], []
    c = max(t["contacted"], 1)
    reply_rate = t["human_replies"] / c
    pos_rate = t["positive_replies"] / c
    if t["contacted"] < 30:
        out.append(f"Too early to judge the funnel ({plural(t['contacted'], 'business', 'businesses')} contacted). Aim for 30+ before changing the pitch.")
    else:
        if reply_rate < 0.03:
            out.append(f"Reply rate is low ({reply_rate:.0%}). Test a new first email: shorter, one issue only, and ask a question instead of offering a call.")
        if t["positive_replies"] and t["booked"] / max(t["positive_replies"], 1) < 0.4:
            out.append("People reply but don't book. Add a booking link with 15-minute slots, or offer to send a 2-minute screen recording of their site first.")
        if pos_rate >= 0.05:
            out.append(f"Positive reply rate is healthy ({pos_rate:.0%}). Safe to raise the daily cap a little (current {C.DAILY_CAP}/day).")
    if t["emails_sent"] >= 20 and t["bounces"] / max(t["emails_sent"], 1) > 0.03:
        out.append("Bounce rate is above 3%. Pause and tighten email finding (prefer addresses on the business's own domain) to protect the sending domain.")
    if t["emails_sent"] >= 20 and t["opt_outs"] / max(t["emails_sent"], 1) > 0.02:
        out.append("Opt-outs are above 2%. Soften the first email or narrow targeting to businesses with clearer problems (score under 60).")
    # which industries and which opening issues earn replies
    by_cat, by_issue = defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0])
    for p in ps:
        if not (p.get("sequence") or {}).get("sent"):
            continue
        replied = any(r["kind"] in ("interested", "question", "referral") for r in p.get("replies", []))
        cat = p.get("category") or "other"
        by_cat[cat][0] += 1; by_cat[cat][1] += replied
        if p.get("audit", {}).get("pitch"):
            iss = p["audit"]["pitch"][0]["id"]
            by_issue[iss][0] += 1; by_issue[iss][1] += replied
    ranked = sorted(((r / s, k, s) for k, (s, r) in by_cat.items() if s >= 10), reverse=True)
    if len(ranked) >= 2 and ranked[0][0] > 0:
        out.append(f"Best industry so far: {ranked[0][1]} ({ranked[0][0]:.0%} positive replies). Weakest: {ranked[-1][1]} ({ranked[-1][0]:.0%}). Shift prospecting toward the best one.")
    issues = Counter(p["audit"]["pitch"][0]["id"] for p in ps if p.get("audit", {}).get("pitch") and p.get("sequence"))
    if sum(issues.values()) >= 10:
        top, k = issues.most_common(1)[0]
        share = k / sum(issues.values())
        offers = {"no_viewport": "a fixed-price \"Mobile-ready in 7 days\" offer",
                  "psi_mobile_poor": "a fixed-price \"Speed fix\" offer with a before/after speed score guarantee",
                  "lcp": "a fixed-price \"Speed fix\" offer with a before/after speed score guarantee",
                  "no_https": "a low-cost \"Secure site\" setup (HTTPS + redirects) as a foot in the door",
                  "no_cta": "a \"More calls from your site\" conversion refresh (buttons, forms, click-to-call)",
                  "no_form": "a \"More calls from your site\" conversion refresh (buttons, forms, click-to-call)",
                  "no_phone": "a \"More calls from your site\" conversion refresh (buttons, forms, click-to-call)"}
        if share >= 0.4 and top in offers:
            out.append(f"{share:.0%} of the sites Alex pitched share the same main problem ({ISSUE_NAMES.get(top, top)}). "
                       f"New offer idea: {offers[top]}, and lead the first email with it.")
    if n["pipeline"]["no_contact_found"] >= 10:
        out.append(f"{n['pipeline']['no_contact_found']} good prospects had no public email. A contact-form or phone follow-up funnel (done by you) could use them.")
    if n["pipeline"]["awaiting_your_approval"]:
        out.append(f"{n['pipeline']['awaiting_your_approval']} drafts are waiting for your approval.")
    if any(x.startswith(("Bounce rate", "Opt-outs")) for x in out):
        out = [x for x in out if not x.startswith("Positive reply rate is healthy")]
    return out or ["No changes suggested today."]


def build() -> str:
    n = numbers()
    d, t, pl = n["day"], n["total"], n["pipeline"]
    r = d["replies"]
    lines = [
        f"Alex daily report, {datetime.now().astimezone().strftime('%a %b %d')}",
        "",
        "Last 24 hours",
        f"- Emails sent: {d['first_emails'] + d['follow_ups'] + d['replies_sent']} ({plural(d['first_emails'], 'first email', 'first emails')}, {plural(d['follow_ups'], 'follow-up', 'follow-ups')}, {plural(d['replies_sent'], 'reply', 'replies')} to leads)",
        f"- Responses: {sum(r[k] for k in ('interested', 'question', 'referral', 'not_interested'))} ({r['interested']} interested, {r['question']} questions, {plural(r['referral'], 'referral to the right person', 'referrals to the right person')}, {r['not_interested']} not interested), {r['unsubscribe']} opt-outs, {r['bounce']} bounces",
        f"- Calls booked: {d['booked']}",
        f"- New prospects found: {d['new_prospects']}, audited: {d['audited']}",
        "",
        "Pipeline now",
        f"- Leads in conversation: {pl['in_conversation']}",
        f"- In follow-up sequence: {pl['in_sequence']}",
        f"- Waiting for your approval: {pl['awaiting_your_approval']}",
        f"- Queued to audit: {pl['to_audit']}",
        "",
        "All time",
        f"- {plural(t['contacted'], 'business', 'businesses')} contacted, {plural(t['emails_sent'], 'email', 'emails')}, {t['human_replies']} human replies, {plural(t['booked'], 'call', 'calls')} booked, {t['won']} won",
        "",
        "Suggestions",
    ] + [f"- {s}" for s in suggestions(n)]
    import experiments
    exp = experiments.summary()
    if exp:
        lines += ["", "What's working (A/B tests)"] + [f"- {x}" for x in exp]
    from writer import PLAYBOOK
    if PLAYBOOK.exists():
        tips = [l.strip("-* ").strip() for l in PLAYBOOK.read_text().splitlines() if l.strip().startswith(("-", "*"))][:3]
        if tips:
            lines += ["", "Lessons Alex is applying"] + [f"- {x}" for x in tips]
    return "\n".join(lines)
