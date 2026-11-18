"""Alex learns which approaches get replies.

Each first email is tagged with one option per dimension below. After every reply, Thompson
sampling shifts traffic toward options with more positive replies (interested or question),
while still testing the others now and then. Results show in the daily report.
"""
from __future__ import annotations

import random

import store

ARMS = {
    "angle": {
        "issue_first": "Open with the single most costly problem on their site.",
        "business_first": "Open with one specific, true detail about their business from the research, then the problems.",
        "question": "Open with a short, genuine question about how many customers find them through the website, then the problems.",
    },
    "cta": {
        "call": "Ask for a 15-minute call with Ahmed.",
        "designs": "Offer to send 2 or 3 free homepage designs for their business, no strings attached.",
        "walkthrough": "Offer a quick walkthrough of the report so they can see exactly what's wrong.",
    },
}


def stats() -> dict:
    """{dimension: {option: [sent, positive]}} from all prospects that got a first email."""
    out = {d: {o: [0, 0] for o in opts} for d, opts in ARMS.items()}
    for p in store.all_prospects():
        v = p.get("variant") or {}
        if not (p.get("sequence") or {}).get("sent"):
            continue
        pos = any(r["kind"] in ("interested", "question", "referral") for r in p.get("replies", []))
        for d, o in v.items():
            if d in out and o in out[d]:
                out[d][o][0] += 1
                out[d][o][1] += pos
    return out


def choose() -> dict:
    st = stats()
    pick = {}
    for d, opts in st.items():
        draws = {o: random.betavariate(1 + pos, 1 + max(0, sent - pos)) for o, (sent, pos) in opts.items()}
        pick[d] = max(draws, key=draws.get)
    return pick


def instructions(v: dict) -> str:
    return " ".join(ARMS[d][o] for d, o in v.items() if d in ARMS and o in ARMS[d])


def summary() -> list[str]:
    lines, st = [], stats()
    if not any(sent for opts in st.values() for sent, _ in opts.values()):
        return []
    for d, opts in st.items():
        parts = [f"{o} {pos}/{sent}" for o, (sent, pos) in sorted(opts.items(), key=lambda kv: -kv[1][1] / max(kv[1][0], 1))]
        lines.append(f"{d}: " + ", ".join(parts))
    return lines
