# Alex: Plen Dev's outbound sales agent

Plan and decisions: https://claude.ai/artifact/DK7zSvundpNeTcQ6X3cBch

Finds local businesses -> robots-aware audit (reuses ../audit-agent) -> qualifies weak sites -> finds a publicly
listed email -> drafts a 3-email sequence -> Ahmed approves -> sends in a weekday window with caps ->
sorts replies, suppresses opt-outs, drafts answers to interested leads -> daily WhatsApp report.

    pip install -r requirements.txt ; cp .env.example .env   # fill in, keep ALEX_SEND_ENABLED=false until approved
    python3 alex.py discover osm --area brooklyn --category dental
    python3 alex.py process --limit 10
    python3 alex.py queue ; python3 alex.py show <id> ; python3 alex.py approve <id>
    python3 alex.py work          # the all-day worker (run it as a service). 9 to 5 Eastern on weekdays it
                                  # reads replies every 10 min, sends approved emails spread across the day
                                  # within each mailbox's warm-up cap, keeps ~2 days of drafts queued for
                                  # Ahmed by discovering + researching + auditing more businesses (every
                                  # industry, NYC metro + Long Island + Westchester + north NJ), and sends
                                  # the WhatsApp report after 5. Weekly it rewrites playbook.md from replies.
    # or the individual steps, if you prefer cron:
    python3 alex.py send ; python3 alex.py inbox ; python3 alex.py report --whatsapp ; python3 alex.py learn
    python3 server.py             # report + unsubscribe links, approval API

2026-11-17 update (Ahmed): pitch is always a NEW website; sign "Alex H, Sales, Plen Dev" (honest if asked
whether he's an AI); deep audit (security/design/accessibility/CRO) lives in ../audit-agent/deep_checks.py
(owned by the audit thread); interested leads get 3 homepage concepts (demos.py, templates/demos/) in the
reply draft; every reply + draft is forwarded to Ahmed on WhatsApp, who can approve/edit/reject by replying.
Inbound audit leads are handed to Alex after their email is sent: store.import_inbound(...).

Status 2026-11-17: built and tested in dry-run on local fixture sites. No accounts, keys or real email yet.
Changes made to ../audit-agent (backward compatible): audit.URL_FILTER / audit.CRAWL_DELAY hooks;
mailer.send() accepts headers / from_addr / reply_to / bcc.


## Round 3 (Nov 18): smarter, all day, every industry
- research.py reads the company's own about/team/locations pages: what they do, founding year, people and roles,
  how many locations and states, what the site is built on. That feeds the email (one true, specific detail).
- Bigger companies (several locations or states) are pitched at headquarters, and Alex asks to be pointed to whoever
  owns the website or marketing for the whole company. Any reply that names another address becomes a referral:
  Alex drafts an intro to that person ("Hi Jim, ... suggested I reach out") for Ahmed's approval.
- experiments.py tests openers (issue first, business detail first, question first) and calls to action (call, free
  designs, walkthrough) and shifts traffic to what earns replies. learn.py turns the replies into playbook.md.
- writer.py (ALEX_LLM=on, needs an Anthropic API key Ahmed approves) writes each email in a natural American voice.
  Code strips every em or en dash. Templates are used when it's off.
- Security findings are passive only (headers, SSL, outdated software visible in the page). Alex never port-scans
  or probes anyone's servers, and never claims he did.
- mailboxes.py rotates several warmed mailboxes, each on its own warm-up ramp. Volume grows by adding mailboxes,
  not by pushing one inbox harder.
