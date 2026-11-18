"""Turn real replies into lessons Alex follows (data/playbook.md), refreshed weekly.

Reads the last 60 days of replies (what Alex sent, what they answered, how it was classified) and
asks Claude for short, concrete lessons: objections to pre-empt, phrasing that worked, industries
that respond. The playbook is shown to the writer for every new email. Ahmed sees it in the report
and can edit or delete the file at any time.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import experiments
import store
import writer


def collect(days: int = 60) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = []
    for p in store.all_prospects():
        for r in p.get("replies", []):
            if datetime.fromisoformat(r["at"]) >= since and r["kind"] not in ("bounce", "out_of_office"):
                first = (p.get("drafts") or {}).get("1", {})
                rows.append({"industry": p.get("category"), "variant": p.get("variant"), "score": p.get("audit", {}).get("score"),
                             "our_first_email": first.get("text", "")[:900], "their_reply": r["text"][:600], "kind": r["kind"]})
    return rows


def run() -> str:
    rows = collect()
    if len(rows) < 8:
        return f"Not enough replies yet to learn from ({len(rows)}; need 8+)."
    prompt = ("Here are replies to our cold emails offering new websites to small and mid-size US businesses, with the email "
              "we sent and how each reply was classified. Experiment results so far: " + "; ".join(experiments.summary()) +
              "\n\nWrite at most 10 short, concrete lessons for the sales rep's next emails (what to keep, what to drop, "
              "objections to pre-empt, which industries respond). Each lesson one line starting with '- '. Base every "
              "lesson on the data; don't invent.\n\n" + json.dumps(rows, indent=1))
    lessons = writer.complete(prompt, effort="high")
    writer.PLAYBOOK.write_text(f"Updated {datetime.now().date()} from {len(rows)} replies\n{lessons}\n")
    return lessons
