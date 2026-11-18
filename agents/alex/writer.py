"""Alex's writer: Claude drafts each email and reply from the audit + company research.

Uses the Anthropic API when ANTHROPIC_API_KEY (or another Anthropic credential) is configured and
ALEX_LLM=on; otherwise the Jinja templates in compose.py are used. Either way:
  * facts come only from the audit and research given to the model (no invented numbers, clients, reviews)
  * no em or en dashes (also stripped in code)
  * the signature and the CAN-SPAM footer are added by code, never by the model
  * Ahmed approves every first email and every reply before it is sent
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import config as C

MODEL = C.E("ALEX_MODEL", "claude-opus-5-5")
PLAYBOOK = C.DATA / "playbook.md"  # lessons learned from replies (see learn.py)

VOICE = """You are Alex H, a sales rep at Plen Dev, a web development company in Brooklyn, NY that builds new websites for businesses. Ahmed is the founder; he does the calls and runs every project.

How you write:
- Like a sharp, friendly American guy who knows websites and tech. Plain, conversational, confident, never pushy. Contractions are fine. Short sentences. No buzzwords, no hype, no flattery.
- Never use em dashes or en dashes. Use commas, periods or parentheses.
- No emojis, no exclamation marks in a first email, no ALL CAPS, no "I hope this email finds you well".
- Plain text only. Bullets with "- " are fine. No markdown headings or bold.
- Use only the facts you are given about the company and its website. Never invent numbers, clients, awards, reviews, discounts, deadlines or claims about what you looked at. If a fact is not given, don't mention it.
- Security issues: describe only what the audit found from public signals (headers, certificates, outdated software versions). Never claim you scanned ports, tested logins or got into anything.
- Plen Dev sells new websites, not patches. Explain simply why a new site beats fixing this one, tied to their business.
- Never say you are human. Never mention AI unless they asked; if they asked whether you're a bot or a real person, say honestly that you're an AI assistant on Plen Dev's sales team and that Ahmed reviews everything and is who they'd talk to.
- Don't write a signature or sign-off name and don't add an unsubscribe line; those are added automatically.
- Goal: a 15-minute call with Ahmed. If the email went to a general inbox or the reader isn't the decision-maker, politely ask them to point you to whoever handles the website or marketing.
- If is_bigger_company is true, you are writing to headquarters: talk about one consistent site across all their locations, and ask who owns the website or marketing for the whole group.
"""

SCHEMA = {
    "type": "object",
    "properties": {"subject": {"type": "string"}, "body": {"type": "string"}},
    "required": ["subject", "body"],
    "additionalProperties": False,
}

TASKS = {
    1: "Write the FIRST cold email. 90 to 140 words. Open with something specific to this company (from the research), "
       "then 2 or 3 of the audit findings in plain English and why they cost customers, then the case for a new site, "
       "then the call ask. Mention the free report link once. Subject: under 7 words, lowercase-friendly, specific, not clickbait.",
    2: "Write FOLLOW-UP 1, sent 3 days later in the same thread with no reply yet. 50 to 80 words. Don't repeat email 1. "
       "Lead with one different angle (a finding not used before, or what a new site would do for them), and offer to send "
       "2 or 3 free homepage designs. Subject must be exactly 'Re: ' + the first subject.",
    3: "Write the LAST follow-up, sent 7 days after follow-up 1, no reply yet. 40 to 60 words. Friendly close-out, leave the "
       "report link, ask if someone else handles the website. Subject must be exactly 'Re: ' + the first subject.",
    "reply": "Write a REPLY to the prospect's latest message. Answer what they actually said, in under 120 words. If they're "
             "interested or asked for designs, include the demo design links given. If they asked about price, say new sites "
             "start at {price_from} and Ahmed gives a fixed quote on the call. If they pointed you to another person, thank "
             "them. Always end with one clear next step toward a 15-minute call with Ahmed. If you cannot answer a question "
             "from the facts given, say Ahmed will cover it on the call. Subject: 'Re: ' + the thread subject.",
}


def enabled() -> bool:
    return C.E("ALEX_LLM", "off").lower() == "on"


def clean(text: str) -> str:
    text = text.replace("—", ", ").replace("–", "-").replace(" -- ", ", ")
    text = re.sub(r" ,", ",", text)
    return re.sub(r",\s*,", ",", text).strip()


def _facts(p: dict) -> dict:
    a = p.get("audit", {})
    return {
        "company": p["business_name"], "website": p["domain"], "industry": p.get("category") or "unknown",
        "area": p.get("area") or "", "contact_email": p.get("contact", {}).get("email", ""),
        "contact_is_general_inbox": p.get("contact", {}).get("general", True),
        "contact_person": p.get("contact", {}).get("person") or None,
        "research": p.get("research", {}),
        "audit_score_out_of_100": a.get("score"), "total_issues_found": sum(a.get("counts", {}).values()) if a.get("counts") else None,
        "top_findings_plain_english": [x["line"] for x in a.get("pitch", [])],
        "more_findings": a.get("more", []),
        "report_link": p.get("report_url") or f"{C.PUBLIC_BASE}/r/{p['report_token']}",
        "booking_link": C.BOOKING_URL or None, "new_sites_start_at": C.PRICE_FROM,
        "first_subject": (p.get("sequence") or {}).get("subject"),
        "approach_to_use": p.get("variant_instructions") or None,
        "referred_by": p.get("referred_by") or None,
        "locations_listed": p.get("locations_listed", 1),
        "states_mentioned_on_site": (p.get("research") or {}).get("states", []),
        "is_bigger_company": p.get("locations_listed", 1) > 1 or len((p.get("research") or {}).get("states", [])) > 1,
    }


def write(p: dict, step, their_text: str = "", demos: list | None = None, thread: list | None = None) -> dict:
    """Returns {"subject", "body"}; raises if the API is not configured (caller falls back to templates)."""
    import anthropic

    client = anthropic.Anthropic()
    playbook = PLAYBOOK.read_text()[:4000] if PLAYBOOK.exists() else ""
    system = VOICE + (f"\nLessons from past replies (follow them):\n{playbook}\n" if playbook else "")
    task = TASKS["reply" if step == "reply" else step].format(price_from=C.PRICE_FROM)
    payload = {"facts": _facts(p), "demo_designs": demos or [], "thread_so_far": thread or [],
               "their_latest_message": their_text or None}
    resp = client.beta.messages.create(
        model=MODEL,
        max_tokens=4000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=system,
        output_config={"effort": "medium", "format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{"role": "user", "content": f"{task}\n\nEverything you know (JSON):\n{json.dumps(payload, indent=1)}"}],
    )
    if resp.stop_reason == "refusal":
        raise RuntimeError("model declined to write this email")
    text = next(b.text for b in resp.content if b.type == "text")
    out = json.loads(text)
    out["subject"], out["body"] = clean(out["subject"]), clean(out["body"])
    return out


def complete(prompt: str, system: str = "", effort: str = "medium", max_tokens: int = 4000) -> str:
    """Plain text completion (used by learn.py)."""
    import anthropic

    client = anthropic.Anthropic()
    resp = client.beta.messages.create(
        model=MODEL, max_tokens=max_tokens, betas=["server-side-fallback-2026-07-01"], fallbacks="default",
        system=system or "You are a concise sales analyst.", output_config={"effort": effort},
        messages=[{"role": "user", "content": prompt}])
    if resp.stop_reason == "refusal":
        raise RuntimeError("model declined")
    return clean("".join(b.text for b in resp.content if b.type == "text"))
