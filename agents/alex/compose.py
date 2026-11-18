"""Turn an audit into Alex's emails: a short first touch, two follow-ups, and replies.

Everything an email claims comes from the audit report, so nothing is made up.
"""
from __future__ import annotations

import html as H
import re

from jinja2 import Environment, FileSystemLoader

import config as C

env = Environment(loader=FileSystemLoader(C.HERE / "templates"), trim_blocks=True, lstrip_blocks=True,
                  keep_trailing_newline=True)

INDUSTRY = {  # category -> (how Alex refers to the group, what the business calls its customers)
    "dental": ("dental practices", "patients"), "medical": ("medical practices", "patients"),
    "home_healthcare": ("home care agencies", "families"), "real_estate": ("real estate offices", "clients"),
    "legal": ("law firms", "clients"), "accounting": ("accounting firms", "clients"),
    "beauty": ("salons and spas", "clients"), "fitness": ("gyms and studios", "members"),
    "contractor": ("contractors", "customers"), "restaurant": ("restaurants", "guests"),
    "veterinary": ("vet clinics", "pet owners"), "auto": ("auto shops", "customers"),
}
AREA_NAME = {"brooklyn": "Brooklyn", "queens": "Queens", "manhattan": "Manhattan", "nassau": "Nassau County",
             "suffolk": "Suffolk County", "long_island": "Long Island"}


def _num(title: str) -> str:
    m = re.search(r"(\d+(?:\.\d+)?)", title)
    return m.group(1) if m else ""


# Plain-English pitch lines, in the order Alex prefers to mention them (strongest case for a new site first).
# Lines are only built from findings the audit actually reported.
SECURITY_IDS = ("no_hsts", "no_csp", "no_clickjack_protection", "no_xcto", "server_version_exposed", "cookie_flags_insecure")
A11Y_IDS = ("inputs_no_labels", "links_no_text", "no_skip_or_landmarks", "img_alt", "missing_alt", "zoom_disabled", "psi_accessibility_low")


def _year(title: str) -> str:
    m = re.search(r"(19|20)\d\d", title)
    return m.group(0) if m else ""


PITCH = {
    "no_viewport": lambda f, w: "The site isn't built for phones, so on mobile it shows up as a shrunken desktop page. That's where most people search for a local business.",
    "mobile_overflow": lambda f, w: "On a phone the page doesn't fit the screen, so people have to scroll sideways to read it.",
    "mobile_overlay": lambda f, w: f"On a phone a pop-up covers most of the screen, so many {w} leave before they see anything.",
    "no_cta_first_screen_mobile": lambda f, w: f"On a phone there's no call or book button on the first screen, so {w} who are ready to act have to hunt for it.",
    "outdated_cms": lambda f, w: "It runs on outdated software with known security holes, one of the most common ways small business sites get hacked.",
    "psi_mobile_poor": lambda f, w: f"It's slow on phones: Google's mobile speed score is {_num(f['title'])}/100. A lot of people give up on a page that takes more than about 3 seconds.",
    "no_https": lambda f, w: "It isn't on HTTPS, so Chrome shows \"Not secure\" next to your address.",
    "keyword_gaps": lambda f, w: f"There are no pages for some of the things {w} actually search for, so those searches go to your competitors.",
    "no_location_pages": lambda f, w: "There are no pages for the neighborhoods and towns you serve, which is how most local businesses show up in \"near me\" searches.",
    "too_few_pages": lambda f, w: (f"The site only has {_num(f['title'])} page{'' if _num(f['title']) == '1' else 's'}" if _num(f['title']) else "The site only has a handful of pages") + ", which gives Google very little to rank you for.",
    "_security": lambda f, w: "It's missing basic security protections that modern sites have by default, which leaves the site and your visitors more exposed.",
    "form_posts_insecure": lambda f, w: "The contact form sends visitors' details over an insecure connection.",
    "ssl_expiring": lambda f, w: "The site's security certificate is about to expire. When it does, visitors get a full-page warning instead of your site.",
    "outdated_js_libs": lambda f, w: "It loads old code libraries with publicly known security flaws.",
    "legacy_tech": lambda f, w: "It's built with outdated web technology that modern browsers and Google handle poorly.",
    "broken_images": lambda f, w: "Some images on the site are broken and show up as empty boxes.",
    "page_load_timeout": lambda f, w: "On our test the homepage didn't finish loading in a reasonable time.",
    "table_layout": lambda f, w: "The layout is built the way sites were in the early 2000s, which is why it's hard to make work on phones.",
    "diy_builder": lambda f, w: "It's built on a DIY site-builder template, so it looks like thousands of other sites and is hard to grow with.",
    "generic_headline": lambda f, w: f"The homepage headline is generic, so {w} can't tell in a few seconds what you do and where.",
    "old_copyright_year": lambda f, w: (f"The footer still says {_year(f['title'])}, " if _year(f['title']) else "The footer date is years out of date, ") + "which makes the business look like it isn't active.",
    "no_cta": lambda f, w: f"There's no clear \"book\" or \"call\" button on the homepage, so {w} who are ready to act have to hunt for it.",
    "no_cta_first_screen_desktop": lambda f, w: f"There's no call or book button on the first screen, so {w} who are ready to act have to hunt for it.",
    "small_text_mobile": lambda f, w: f"{_num(f['title']) or 'A lot of'}% of the text is too small to read on a phone without zooming.",
    "tap_targets_small": lambda f, w: "Buttons and links are too small to tap easily on a phone.",
    "headline_below_fold_mobile": lambda f, w: "On a phone the main headline doesn't show until you scroll, so the first thing people see doesn't say what you do.",
    "home_no_location": lambda f, w: "The homepage title and headline don't say where you work, which hurts you in local searches.",
    "home_no_service": lambda f, w: "The homepage title and headline don't say what you do, which hurts you in Google searches.",
    "stock_photos": lambda f, w: f"The site relies on stock photos, so {w} don't get a real look at your business.",
    "blurry_images": lambda f, w: "Some photos look blurry or stretched, which makes the business look less professional.",
    "stretched_images": lambda f, w: "Some photos look stretched, which makes the business look less professional.",
    "no_form": lambda f, w: f"There's no contact or quote form, so {w} who'd rather not call have nowhere to go.",
    "no_online_booking": lambda f, w: f"There's no way to book online, so {w} can only reach you by phone during office hours.",
    "no_care_request": lambda f, w: "There's no easy way for a family to request care or a free assessment, so they call the next agency on Google.",
    "no_caregiver_jobs": lambda f, w: "There's no careers page for caregivers, so job seekers go to agencies that make applying easy.",
    "no_payment_info": lambda f, w: "The site doesn't say how care is paid for (Medicaid, insurance, private pay), which is the first question most families have.",
    "no_tour_request": lambda f, w: "There's no way to schedule a tour online, and families decide after visiting.",
    "no_insurance_info": lambda f, w: f"The site doesn't say which insurance you take, which is one of the first things {w} check.",
    "no_case_evaluation": lambda f, w: "There's no free case evaluation form, so people with a case reach out to a firm that has one.",
    "no_quote_request": lambda f, w: f"There's no quick way to request a quote, so {w} who are ready to hire have to call during business hours.",
    "no_emergency_info": lambda f, w: f"The site doesn't make emergency or same-day service obvious, and that's exactly what many {w} are searching for.",
    "no_home_valuation": lambda f, w: "There's no \"what's my home worth\" tool, one of the best ways real estate sites turn visitors into seller leads.",
    "no_listing_search": lambda f, w: "Visitors can't search your listings on the site, so they go back to Zillow.",
    "no_order_or_reserve": lambda f, w: f"There's no way to order or reserve a table from the site, so {w} book through an app that takes a cut, or go elsewhere.",
    "menu_pdf_only": lambda f, w: "The menu is only a PDF, which is hard to read on a phone and invisible to Google.",
    "no_trial_signup": lambda f, w: f"There's no free trial or first-class signup, the easiest way to get new {w} in the door.",
    "no_service_booking": lambda f, w: f"There's no way to book a service appointment online, so {w} have to call during business hours.",
    "no_consult_booking": lambda f, w: f"There's no way to book a consultation online, so {w} who are ready to talk have to call or email and wait.",
    "no_tour_or_enroll": lambda f, w: "There's no way to book a tour or start enrollment online, and parents usually decide after a visit.",
    "no_reviews": lambda f, w: f"There are no reviews or testimonials on the site, and that's the first thing {w} look for before choosing.",
    "no_phone": lambda f, w: "The phone number isn't on the homepage, and it's usually the first thing people look for.",
    "contact_not_above_fold": lambda f, w: "Your phone number and contact options aren't visible without scrolling.",
    "lcp": lambda f, w: f"On a phone the main content takes about {_num(f['title'])} seconds to show up (Google's target is under 2.5).",
    "_a11y": lambda f, w: "It has accessibility gaps (for example form fields screen readers can't read). Those make the site harder to use, and ADA website claims are common in New York.",
    "robots_blocks_all": lambda f, w: "The site's robots.txt tells Google not to crawl any page, which can keep you out of search results.",
    "noindex": lambda f, w: f"{_num(f['title']) or 'Some'} page(s) are set to be hidden from Google.",
    "broken_pages": lambda f, w: f"{_num(f['title']) or 'Some'} links on the site lead to broken pages.",
    "js_only_content": lambda f, w: "Most of the text only appears after scripts run, so Google and AI search tools see an almost empty page.",
    "page_builder_bloat": lambda f, w: "Pages are weighed down by page-builder code, a big part of why it feels slow.",
    "too_many_scripts": lambda f, w: "Each page loads a pile of scripts, a big part of why it feels slow.",
    "no_modern_images": lambda f, w: "Images are large, old-format files that slow the site down on phones.",
    "no_responsive_images": lambda f, w: "Images aren't sized for phones, so mobile visitors download far more than they need.",
    "slow_ttfb": lambda f, w: f"The homepage took {_num(f['title'])} seconds just to start loading on our test.",
    "lcp_measured": lambda f, w: f"On a phone the main content takes about {_num(f['title']) or 'several'} seconds to show up (Google's target is under 2.5).",
    "page_weight": lambda f, w: f"The homepage downloads {f['title'].split('downloads ')[-1].split(' on a phone')[0]} on a phone, which is slow on a cell connection.",
    "heavy_images": lambda f, w: "Some images are huge files, a big part of why the site is slow on phones.",
    "thin_service_pages": lambda f, w: "The service pages are very short, so Google doesn't see them as a strong match for those searches.",
    "js_errors": lambda f, w: "The site throws code errors in the browser, which can break buttons and forms.",
    "no_tel_link": lambda f, w: "The phone number can't be tapped to call on a phone.",
    "no_http_redirect": lambda f, w: "The http:// version of the site doesn't forward to the secure one, so some visitors get a \"Not secure\" warning.",
    "no_privacy_policy": lambda f, w: "There's no privacy policy, even though the site collects visitors' details.",
    "no_localbusiness_schema": lambda f, w: "Google isn't given your business details (hours, address, services) in the format it uses for local results and the map pack.",
    "no_address": lambda f, w: "There's no street address on the site, which hurts you in \"near me\" searches.",
    "form_too_long": lambda f, w: f"The contact form asks for so much that many {w} won't finish it.",
    "no_sitemap": lambda f, w: "There's no sitemap, so Google has a harder time finding all of your pages.",
    "psi_mobile_avg": lambda f, w: f"Mobile speed is middling (Google score {_num(f['title'])}/100), with room to load a lot faster.",
    "mixed_content": lambda f, w: "Some images or scripts load over insecure http://, which can trigger browser warnings.",
    "cls": lambda f, w: "Things jump around while the page loads, which leads to mis-taps on phones.",
}
SEV = {"critical": 0, "high": 1, "medium": 2, "low": 3}
PITCHABLE = set(PITCH) | set(SECURITY_IDS) | set(A11Y_IDS)


def _key(fid: str) -> str:
    return "_security" if fid in SECURITY_IDS else "_a11y" if fid in A11Y_IDS else fid


def _line(k: str, f: dict, customers: str) -> str:
    return PITCH[k](f, customers)


def extra_points(report: dict, customers: str, skip: list, n: int = 4) -> list[tuple]:
    """More findings (beyond the top 3) for follow-ups, as (key, finding)."""
    used = {x["id"] for x in skip}
    seen, out = set(), []
    for f in sorted(report["findings"], key=lambda f: SEV[f["severity"]]):
        k = _key(f["id"])
        if k in PITCH and k not in used and k not in seen and f["severity"] in ("critical", "high", "medium"):
            seen.add(k)
            out.append((k, f))
    return out[:n]


def nodash(t: str) -> str:
    return t.replace("\u2014", ", ").replace("\u2013", "-").replace(" ,", ",")


def finish(step, p: dict, subject: str, body: str, reply: bool = False) -> dict:
    """Body written by the writer + signature (+ CAN-SPAM footer on sequence emails), added by code."""
    c = ctx(p)
    tail = env.get_template("_sig.txt.j2" if reply else "_footer.txt.j2").render(**c)
    text = nodash(body.strip()) + "\n\n" + tail
    return {"step": step, "subject": nodash(subject), "text": text, "html": to_html(text)}


def pitch_points(report: dict, customers: str, n: int = 3) -> list[dict]:
    order = list(PITCH)
    best = {}  # one line per key (security and accessibility findings collapse into one point each)
    for f in report["findings"]:
        k = _key(f["id"])
        if k in PITCH and f["severity"] in ("critical", "high", "medium"):
            if k not in best or SEV[f["severity"]] < SEV[best[k]["severity"]]:
                best[k] = f
    ranked = sorted(best.items(), key=lambda kv: (SEV[kv[1]["severity"]], order.index(kv[0])))
    return [{"id": k, "severity": f["severity"], "line": PITCH[k](f, customers)} for k, f in ranked[:n]]


def subject_for(p: dict, points: list[dict]) -> str:
    name = p["business_name"]
    poss = f"{name}'" if name.endswith("s") else f"{name}'s"
    top = points[0]["id"] if points else ""
    if top in ("no_viewport", "psi_mobile_poor", "lcp", "cls"):
        return f"{poss} website on phones"
    if top in ("_security", "outdated_cms", "outdated_js_libs", "ssl_expiring", "form_posts_insecure"):
        return f"Security gaps on {p['domain']}"
    if top in ("legacy_tech", "table_layout", "old_copyright_year"):
        return f"{poss} website is showing its age"
    if top in ("no_https", "no_http_redirect", "mixed_content"):
        return f"\"Not secure\" warning on {p['domain']}"
    if top in ("no_cta", "no_form", "no_phone", "no_tel_link"):
        return f"Quick idea for {poss} website"
    return f"A few things I noticed on {p['domain']}"


def ctx(p: dict) -> dict:
    group, customers = INDUSTRY.get(p.get("category", ""), ("local businesses", "customers"))
    area = AREA_NAME.get(p.get("area", ""), p.get("area", "") or "New York")
    return {
        "p": p, "a": p.get("audit", {}), "group": group, "customers": customers, "area": area,
        "points": p.get("audit", {}).get("pitch", []),
        "report_url": p.get("report_url") or f"{C.PUBLIC_BASE}/r/{p['report_token']}",
        "more_issues": max(0, sum(p.get("audit", {}).get("counts", {}).values()) - len(p.get("audit", {}).get("pitch", []))),
        "unsub_url": f"{C.PUBLIC_BASE}/u/{p['unsub_token']}",
        "agent": C.AGENT_NAME, "agent_title": C.AGENT_TITLE, "company": C.COMPANY, "site": C.SITE,
        "contact_email": C.CONTACT_EMAIL, "phone": C.PHONE, "address": C.ADDRESS or "[BUSINESS ADDRESS REQUIRED]",
        "booking_url": C.BOOKING_URL, "home_area": C.HOME_AREA,
        "v": p.get("variant") or {}, "general": (p.get("contact") or {}).get("general", True),
        "bigger": _bigger(p), "fact": _fact(p),
    }


def _bigger(p: dict) -> bool:
    return p.get("locations_listed", 1) > 1 or len((p.get("research") or {}).get("states", [])) > 1 \
        or (p.get("research") or {}).get("locations", 0) > 1


def _fact(p: dict) -> str:
    """One true, specific line from the research for the business_first opener (template mode)."""
    r = p.get("research") or {}
    if len(r.get("states", [])) > 1:
        return f"I saw {p['business_name']} operates in {len(r['states'])} states, which is impressive."
    n = max(p.get("locations_listed", 1), r.get("locations", 0))
    if n > 1:
        return f"I saw {p['business_name']} has {n} locations, which is impressive."
    if r.get("founded"):
        return f"I saw {p['business_name']} has been around since {r['founded']}. That kind of track record is hard to come by."
    return ""


def to_html(text: str) -> str:
    """Simple personal-looking HTML version of a plain-text email (no images, no tracking pixels)."""
    out = []
    for block in text.strip().split("\n\n"):
        esc = H.escape(block)
        esc = re.sub(r"(https?://[^\s<]+)", r'<a href="\1">\1</a>', esc)
        if block.lstrip().startswith("- "):
            items = "".join(f"<li style=\"margin:0 0 6px\">{l.strip()[2:]}</li>" for l in esc.splitlines() if l.strip())
            out.append(f'<ul style="margin:0 0 14px;padding-left:20px">{items}</ul>')
        elif block.startswith("--"):
            out.append(f'<p style="margin:24px 0 0;font-size:12px;color:#777">{esc[2:].strip().replace(chr(10), "<br>")}</p>')
        else:
            out.append(f'<p style="margin:0 0 14px">{esc.replace(chr(10), "<br>")}</p>')
    return ('<div style="font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.5;color:#222;max-width:600px">'
            + "".join(out) + "</div>")


def render(step: int, p: dict) -> dict:
    """step 1 = first email, 2 and 3 = follow-ups (sent as replies in the same thread)."""
    c = ctx(p)
    text = env.get_template(f"step{step}.txt.j2").render(**c)
    first_subject = p.get("sequence", {}).get("subject") or subject_for(p, c["points"])
    subject = first_subject if step == 1 else f"Re: {first_subject}"
    text, subject = nodash(text), nodash(subject)
    return {"step": step, "subject": subject, "text": text, "html": to_html(text)}


def render_reply(kind: str, p: dict, their_text: str = "", demos: list | None = None) -> dict:
    asks_price = bool(re.search(r"\b(price|pricing|cost|how much|quote|budget|rates?)\b", their_text, re.I))
    c = ctx(p) | {"their_text": their_text, "asks_price": asks_price, "price_from": C.PRICE_FROM, "demos": demos or []}
    text = nodash(env.get_template(f"reply_{kind}.txt.j2").render(**c))
    return {"step": f"reply_{kind}", "subject": f"Re: {p['sequence']['subject']}", "text": text, "html": to_html(text)}
