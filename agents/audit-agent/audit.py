#!/usr/bin/env python3
"""Plen Dev website audit engine.

Crawls a prospect's site, runs technical / on-page / local / AI-readiness /
conversion checks, optionally pulls Google PageSpeed Insights (Core Web Vitals),
and produces a scored JSON report plus an HTML report and an email draft.

Usage:
  python3 audit.py https://example.com --name "Jane" --company "Acme Dental" \
      --out ./outbox/lead_123 [--max-pages 15] [--psi-key $PAGESPEED_API_KEY]

Requires: requests, beautifulsoup4, lxml, jinja2
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup

UA = "PlenDevAuditBot/1.0 (+https://plendev.com/audit-bot)"
TIMEOUT = 20
# Optional politeness hooks (used by the Alex outbound agent; inbound audits leave them unset):
#   URL_FILTER(url) -> bool  : return False to skip a URL (e.g. disallowed by robots.txt)
#   CRAWL_DELAY             : seconds to wait between page fetches
URL_FILTER = None
CRAWL_DELAY = 0.0
HERE = Path(__file__).resolve().parent

# Category weights for the overall score (sum = 100)
WEIGHTS = {
    "conversion": 15,
    "performance": 15,
    "security": 15,
    "technical": 12,
    "design": 10,
    "accessibility": 10,
    "on_page": 10,
    "local_seo": 8,
    "ai_readiness": 5,
}
CATEGORY_LABELS = {
    "conversion": "Conversion & trust",
    "performance": "Speed & Core Web Vitals",
    "security": "Security & privacy",
    "technical": "Technical SEO",
    "design": "Design & technology age",
    "accessibility": "Accessibility (ADA)",
    "on_page": "On-page SEO",
    "local_seo": "Local SEO",
    "ai_readiness": "AI search readiness",
}
SEVERITY_POINTS = {"critical": 10, "high": 6, "medium": 3, "low": 1}


@dataclass
class Finding:
    category: str
    id: str
    severity: str  # critical | high | medium | low
    title: str
    detail: str
    fix: str  # internal note for Plen Dev; client-facing copy uses detail + impact
    pages: list[str] = field(default_factory=list)
    impact: str = ""  # business impact, shown to clients


@dataclass
class Page:
    url: str
    status: int
    final_url: str
    elapsed_ms: int
    bytes: int
    html: str | None
    headers: dict


# --------------------------------------------------------------------------- fetch

def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,*/*"})
    return s


def fetch(sess: requests.Session, url: str) -> Page:
    t0 = time.time()
    try:
        r = sess.get(url, timeout=TIMEOUT, allow_redirects=True)
    except requests.RequestException as e:
        return Page(url, 0, url, int((time.time() - t0) * 1000), 0, None, {"error": str(e)})
    ctype = r.headers.get("content-type", "")
    html = r.text if "html" in ctype else None
    return Page(url, r.status_code, r.url, int((time.time() - t0) * 1000), len(r.content), html,
                dict(r.headers))


def normalize(url: str) -> str:
    url, _ = urldefrag(url)
    p = urlparse(url)
    path = p.path or "/"
    return f"{p.scheme}://{p.netloc.lower()}{path}" + (f"?{p.query}" if p.query else "")


def crawl(start: str, max_pages: int) -> tuple[list[Page], dict]:
    sess = _session()
    home = fetch(sess, start)
    base_host = urlparse(home.final_url).netloc.lower()
    pages = [home]
    seen = {normalize(start), normalize(home.final_url)}
    queue: deque[str] = deque()

    def enqueue_links(pg: Page):
        if not pg.html:
            return
        soup = BeautifulSoup(pg.html, "lxml")
        for a in soup.find_all("a", href=True):
            href = urljoin(pg.final_url, a["href"])
            if not href.startswith("http"):
                continue
            if urlparse(href).netloc.lower() != base_host:
                continue
            if re.search(r"\.(pdf|jpe?g|png|gif|webp|svg|zip|mp4|docx?)$", href, re.I):
                continue
            n = normalize(href)
            if n not in seen:
                seen.add(n)
                queue.append(n)

    enqueue_links(home)
    # Seed from sitemap too
    site = f"{urlparse(home.final_url).scheme}://{base_host}"
    extras = {
        "robots": fetch(sess, f"{site}/robots.txt"),
        "sitemap": fetch(sess, f"{site}/sitemap.xml"),
        "llms": fetch(sess, f"{site}/llms.txt"),
        "http": fetch(sess, f"http://{base_host}/"),
        "notfound": fetch(sess, f"{site}/plendev-audit-404-check-{int(time.time())}"),
    }
    sm = extras["sitemap"]
    if sm.status == 200 and sm.bytes:
        try:
            locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", sess.get(sm.final_url, timeout=TIMEOUT).text)
            for loc in locs[:200]:
                n = normalize(loc)
                if urlparse(n).netloc.lower() == base_host and n not in seen and not n.endswith(".xml"):
                    seen.add(n)
                    queue.append(n)
        except requests.RequestException:
            pass

    while queue and len(pages) < max_pages:
        nxt = queue.popleft()
        if URL_FILTER and not URL_FILTER(nxt):
            continue
        if CRAWL_DELAY:
            time.sleep(CRAWL_DELAY)
        pg = fetch(sess, nxt)
        pages.append(pg)
        enqueue_links(pg)
    return pages, extras


# --------------------------------------------------------------------------- PageSpeed

def pagespeed(url: str, key: str | None, strategy: str) -> dict | None:
    params = {"url": url, "strategy": strategy, "category": ["performance", "seo", "accessibility", "best-practices"]}
    if key:
        params["key"] = key
    try:
        r = requests.get("https://www.googleapis.com/pagespeedonline/v5/runPagespeed", params=params, timeout=120)
        if r.status_code != 200:
            return {"error": f"HTTP {r.status_code}"}
        d = r.json()
    except (requests.RequestException, ValueError) as e:
        return {"error": str(e)}
    lh = d.get("lighthouseResult", {})
    cats = lh.get("categories", {})
    audits = lh.get("audits", {})

    def num(aid):
        return audits.get(aid, {}).get("numericValue")

    field_data = d.get("loadingExperience", {}).get("metrics", {})
    return {
        "scores": {k: round((v.get("score") or 0) * 100) for k, v in cats.items()},
        "lcp_ms": num("largest-contentful-paint"),
        "cls": num("cumulative-layout-shift"),
        "tbt_ms": num("total-blocking-time"),
        "fcp_ms": num("first-contentful-paint"),
        "field": {k: v.get("category") for k, v in field_data.items()},
        "opportunities": [
            {"id": k, "title": a.get("title"), "savings_ms": a.get("details", {}).get("overallSavingsMs")}
            for k, a in audits.items()
            if a.get("details", {}).get("type") == "opportunity" and (a.get("score") or 1) < 0.9
        ][:6],
    }


# --------------------------------------------------------------------------- checks

def page_facts(pg: Page) -> dict:
    soup = BeautifulSoup(pg.html or "", "lxml")
    title = (soup.title.string or "").strip() if soup.title and soup.title.string else ""
    md = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    robots = soup.find("meta", attrs={"name": re.compile("^robots$", re.I)})
    canon = soup.find("link", rel=lambda v: v and "canonical" in v)
    jsonld_types = []
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(s.string or "{}")
        except ValueError:
            continue
        items = data if isinstance(data, list) else data.get("@graph", [data]) if isinstance(data, dict) else []
        for it in items:
            if isinstance(it, dict):
                t = it.get("@type")
                jsonld_types += t if isinstance(t, list) else [t] if t else []
    imgs = soup.find_all("img")
    text = soup.get_text(" ", strip=True)
    html_l = (pg.html or "").lower()
    return {
        "url": pg.final_url,
        "status": pg.status,
        "title": title,
        "meta_description": (md.get("content") or "").strip() if md else "",
        "robots": (robots.get("content") or "").lower() if robots else "",
        "canonical": canon.get("href") if canon else "",
        "h1": [h.get_text(" ", strip=True) for h in soup.find_all("h1")],
        "h2_count": len(soup.find_all("h2")),
        "lang": (soup.html.get("lang") if soup.html else "") or "",
        "viewport": bool(soup.find("meta", attrs={"name": "viewport"})),
        "og": bool(soup.find("meta", property="og:title")),
        "jsonld": [t for t in jsonld_types if t],
        "img_total": len(imgs),
        "img_no_alt": sum(1 for i in imgs if not (i.get("alt") or "").strip()),
        "word_count": len(text.split()),
        "mixed_content": pg.final_url.startswith("https") and bool(
            re.search(r'(src|href)=["\']http://(?!www\.w3\.org)', pg.html or "", re.I)),
        "tel_link": bool(soup.find("a", href=re.compile(r"^tel:", re.I))),
        "phone_text": bool(re.search(r"\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}", text)),
        "form": bool(soup.find("form")),
        "cta": bool(re.search(r"\b(book|schedule|get a quote|free (quote|consultation|estimate)|contact us|call now|request)\b",
                               text, re.I)),
        "analytics": any(k in html_l for k in ("googletagmanager.com", "gtag(", "google-analytics.com", "plausible.io",
                                                 "clarity.ms")),
        "favicon": bool(soup.find("link", rel=lambda v: v and "icon" in " ".join(v).lower())),
        "address_text": bool(re.search(r"\b\d{2,5}\s+\w+.*\b(st|street|ave|avenue|rd|road|blvd|boulevard|ln|lane|dr|drive)\b",
                                       text, re.I)),
        "maps_embed": "google.com/maps" in html_l or "maps.googleapis" in html_l,
        "elapsed_ms": pg.elapsed_ms,
        "bytes": pg.bytes,
    }


def run_checks(pages: list[Page], extras: dict, psi: dict) -> tuple[list[Finding], list[dict]]:
    F: list[Finding] = []
    html_pages = [p for p in pages if p.html and p.status == 200]
    facts = [page_facts(p) for p in html_pages]
    home = facts[0] if facts else None

    def add(cat, fid, sev, title, detail, fix, pgs=None, impact=""):
        F.append(Finding(cat, fid, sev, title, detail, fix, (pgs or [])[:10], impact))

    # ---- Technical
    if not pages[0].html or pages[0].status >= 400 or pages[0].status == 0:
        add("technical", "home_unreachable", "critical", "Homepage did not load",
            f"Our crawler got status {pages[0].status} {pages[0].headers.get('error', '')}".strip(),
            "Check hosting, DNS and firewall rules so search engines can reach the site.")
    if not pages[0].final_url.startswith("https://"):
        add("technical", "no_https", "critical", "Site is not served over HTTPS",
            "Browsers mark the site 'Not secure' and Google uses HTTPS as a ranking signal.",
            "Install an SSL certificate and 301-redirect all http:// URLs to https://.")
    elif extras["http"].final_url.startswith("http://"):
        add("technical", "no_http_redirect", "high", "http:// version does not redirect to https://",
            "Two versions of the site can be indexed, splitting ranking signals.",
            "Add a site-wide 301 redirect from http to https.")
    if extras["robots"].status != 200:
        add("technical", "no_robots", "medium", "No robots.txt file",
            "Search engines and AI crawlers have no crawl guidance.",
            "Publish /robots.txt that allows crawling and points to the XML sitemap.")
    elif re.search(r"^disallow:\s*/\s*$", extras["robots"].html or "", re.I | re.M):
        add("technical", "robots_blocks_all", "critical", "robots.txt blocks the entire site",
            "A 'Disallow: /' rule tells search engines not to crawl any page.",
            "Remove the blanket Disallow rule.")
    if extras["sitemap"].status != 200:
        add("technical", "no_sitemap", "high", "No XML sitemap at /sitemap.xml",
            "Google discovers new and updated pages more slowly without a sitemap.",
            "Generate an XML sitemap and submit it in Google Search Console.")
    if extras["notfound"].status == 200:
        add("technical", "soft_404", "medium", "Missing pages return 200 instead of 404",
            "'Soft 404s' waste crawl budget and can get thin pages indexed.",
            "Configure the server to return a real 404 status for unknown URLs.")
    broken = [p.url for p in pages if p.status >= 400 or p.status == 0]
    if broken:
        add("technical", "broken_pages", "high", f"{len(broken)} broken internal link{'s' if len(broken) != 1 else ''}",
            "Visitors and crawlers hit error pages.", "Fix or 301-redirect these URLs.", broken)
    noindex = [f["url"] for f in facts if "noindex" in f["robots"]]
    if noindex:
        add("technical", "noindex", "high", f"{len(noindex)} page{'s' if len(noindex) != 1 else ''} hidden from Google (noindex)",
            "These pages are excluded from Google.", "Remove noindex from pages that should rank.", noindex)
    no_canon = [f["url"] for f in facts if not f["canonical"]]
    if facts and len(no_canon) > len(facts) / 2:
        add("technical", "no_canonical", "low", "Most pages have no canonical tag",
            "Duplicate URL variants may compete with each other.",
            "Add a self-referencing rel=canonical on every page.", no_canon)
    mixed = [f["url"] for f in facts if f["mixed_content"]]
    if mixed:
        add("technical", "mixed_content", "medium", "Insecure (http://) resources on HTTPS pages",
            "Can trigger browser security warnings.", "Load every asset over https.", mixed)
    if home and not home["viewport"]:
        add("technical", "no_viewport", "critical", "Not mobile-friendly (no viewport tag)",
            "Google indexes the mobile version first; this page will render poorly on phones.",
            "Make the layout responsive so it adapts to phone screens (starting with a viewport meta tag).")
    if home and not home["analytics"]:
        add("technical", "no_analytics", "medium", "No analytics detected",
            "You can't measure traffic, rankings impact or leads.",
            "Install Google Analytics 4 (via Tag Manager) and connect Search Console.")

    # ---- On-page
    def bad(pred):
        return [f["url"] for f in facts if pred(f)]
    for fid, sev, title, detail, fix, pred in [
        ("missing_title", "high", "Pages missing a title tag", "The title is the #1 on-page ranking element.",
         "Write a unique 50-60 character title with the main keyword and city.", lambda f: not f["title"]),
        ("title_length", "low", "Title tags too long or too short", "Titles over ~60 chars get cut off in Google.",
         "Keep titles between 30 and 60 characters.", lambda f: f["title"] and not 30 <= len(f["title"]) <= 60),
        ("missing_meta_desc", "medium", "Pages missing a meta description",
         "Google writes its own snippet, usually lowering click-through.",
         "Write a 140-160 character description with a call to action.", lambda f: not f["meta_description"]),
        ("missing_h1", "high", "Pages with no H1 heading", "Search engines use the H1 to understand the topic.",
         "Add one descriptive H1 per page.", lambda f: not f["h1"]),
        ("multiple_h1", "low", "Pages with more than one H1", "Dilutes the page's main topic.",
         "Use a single H1 and H2/H3 for sub-sections.", lambda f: len(f["h1"]) > 1),
        ("thin_content", "medium", "Thin content (under 300 words)", "Short pages rarely rank for competitive terms.",
         "Expand key service pages to 600+ useful words, with FAQs.", lambda f: f["word_count"] < 300),
        ("img_alt", "medium", "Images missing alt text", "Hurts accessibility and image search visibility.",
         "Add short descriptive alt text to every meaningful image.", lambda f: f["img_no_alt"] > 0),
    ]:
        hits = bad(pred)
        if hits:
            add("on_page", fid, sev, f"{title} ({len(hits)})", detail, fix, hits)
    titles = [f["title"] for f in facts if f["title"]]
    dupes = {t for t in titles if titles.count(t) > 1}
    if dupes:
        add("on_page", "dup_titles", "medium", f"{len(dupes)} duplicate page title{'s' if len(dupes) != 1 else ''}",
            "Pages with identical titles compete with each other.", "Give every page a unique title.",
            [f["url"] for f in facts if f["title"] in dupes])
    if home and not home["og"]:
        add("on_page", "no_og", "low", "No Open Graph tags",
            "Links shared on Facebook, LinkedIn and iMessage show no image or proper title.",
            "Add og:title, og:description and og:image.")

    # ---- Performance
    if psi.get("mobile") and "scores" in psi["mobile"]:
        m = psi["mobile"]
        perf = m["scores"].get("performance", 0)
        if perf < 50:
            add("performance", "psi_mobile_poor", "critical", f"Mobile speed score is {perf}/100",
                "Slow mobile pages lose visitors and rankings.", "See the speed opportunities below.")
        elif perf < 90:
            add("performance", "psi_mobile_avg", "medium", f"Mobile speed score is {perf}/100",
                "Room to improve load time on phones.", "Compress images, defer scripts, use caching/CDN.")
        if m.get("lcp_ms") and m["lcp_ms"] > 2500:
            add("performance", "lcp", "high", f"Largest Contentful Paint is {m['lcp_ms'] / 1000:.1f}s (target < 2.5s)",
                "This Core Web Vital measures how fast the main content appears.",
                "Optimize the hero image, preload key assets, reduce server response time.")
        if m.get("cls") and m["cls"] > 0.1:
            add("performance", "cls", "medium", f"Layout shift (CLS) is {m['cls']:.2f} (target < 0.1)",
                "Content jumps around while loading.", "Set width/height on images and reserve space for embeds.")
        if m.get("tbt_ms") and m["tbt_ms"] > 300:
            add("performance", "tbt", "medium", f"Main thread blocked for {m['tbt_ms']:.0f}ms",
                "The page feels unresponsive to taps.", "Remove unused JavaScript and defer third-party scripts.")
    else:
        # Fallback heuristics when PageSpeed is unavailable
        if home and home["elapsed_ms"] > 2000:
            add("performance", "slow_ttfb", "high", f"Homepage took {home['elapsed_ms'] / 1000:.1f}s to download",
                "Slow server response delays everything else.", "Upgrade hosting, enable caching and a CDN.")
        if home and home["bytes"] > 500_000:
            add("performance", "heavy_html", "medium", f"Homepage HTML is {home['bytes'] // 1024} KB",
                "Heavy pages load slowly on mobile.", "Trim inline code and page builder bloat.")

    # ---- Local SEO
    types = {t for f in facts for t in f["jsonld"]}
    local_types = {"LocalBusiness", "Organization", "Dentist", "MedicalBusiness", "RealEstateAgent",
                   "HomeAndConstructionBusiness", "ProfessionalService", "Store", "Restaurant",
                   "LegalService", "MedicalClinic", "HomeHealthCare", "Physician"}
    if not types & local_types:
        add("local_seo", "no_localbusiness_schema", "high", "No LocalBusiness / Organization schema",
            "Structured data helps Google show your hours, reviews and location in the map pack.",
            "Add LocalBusiness JSON-LD with name, address, phone, hours, geo and sameAs links.")
    if home and not (home["tel_link"] or home["phone_text"]):
        add("local_seo", "no_phone", "high", "No phone number on the homepage",
            "A consistent Name/Address/Phone (NAP) is a core local ranking factor.",
            "Show the phone number in the header/footer as a click-to-call link.")
    elif home and not home["tel_link"]:
        add("local_seo", "no_tel_link", "medium", "Phone number is not click-to-call",
            "Most local searches happen on mobile.", "Wrap the number in a tel: link.")
    if not any(f["address_text"] for f in facts):
        add("local_seo", "no_address", "medium", "No street address found on the site",
            "Google needs to match your site to your Google Business Profile.",
            "Add the full address in the footer and on a contact page.")
    if not any(f["maps_embed"] for f in facts):
        add("local_seo", "no_map", "low", "No Google Map embedded",
            "A map on the contact page reinforces your location.", "Embed your Google Business Profile map.")
    if home and not home["lang"]:
        add("local_seo", "no_lang", "low", "No language declared on <html>",
            "Helps search engines serve the page to the right audience.", "Add lang=\"en-US\".")

    # ---- AI readiness
    if extras["llms"].status != 200:
        add("ai_readiness", "no_llms_txt", "low", "No /llms.txt file",
            "An emerging standard that tells AI assistants what your business does and which pages matter.",
            "Publish /llms.txt with a summary of services, locations and key URLs.")
    robots_txt = (extras["robots"].html or "") if extras["robots"].status == 200 else ""
    blocked_ai = [b for b in ("GPTBot", "ClaudeBot", "PerplexityBot", "Google-Extended", "OAI-SearchBot")
                  if re.search(rf"user-agent:\s*{b}\s*\n\s*disallow:\s*/\s*$", robots_txt, re.I | re.M)]
    if blocked_ai:
        add("ai_readiness", "ai_bots_blocked", "medium", f"AI crawlers blocked: {', '.join(blocked_ai)}",
            "ChatGPT, Claude and Perplexity can't read or recommend your site.",
            "Allow AI search crawlers in robots.txt if you want to appear in AI answers.")
    if not types:
        add("ai_readiness", "no_structured_data", "medium", "No structured data at all",
            "AI tools and Google rely on schema to understand services, FAQs and reviews.",
            "Add Organization, Service and FAQPage schema.")
    elif "FAQPage" not in types:
        add("ai_readiness", "no_faq_schema", "low", "No FAQ content marked up",
            "Question-and-answer content is what AI assistants quote most often.",
            "Add an FAQ section to service pages with FAQPage schema.")
    if home and home["word_count"] < 150:
        add("ai_readiness", "js_only_content", "high", "Very little readable text in the page HTML",
            "If content only appears after JavaScript runs, many crawlers and AI tools see a blank page.",
            "Server-render or pre-render the main content.")

    # ---- Conversion
    if home and not home["cta"]:
        add("conversion", "no_cta", "high", "No clear call to action on the homepage",
            "Visitors don't know the next step, so traffic doesn't become leads.",
            "Add a prominent 'Book a consultation' / 'Get a free quote' button above the fold.")
    if not any(f["form"] for f in facts):
        add("conversion", "no_form", "high", "No contact or quote form found",
            "Many visitors prefer a form to calling.", "Add a short lead form on the homepage and contact page.")
    if home and not home["favicon"]:
        add("conversion", "no_favicon", "low", "No favicon",
            "Looks unfinished in browser tabs and Google results.", "Add a favicon and apple-touch-icon.")

    import deep_checks
    deep_checks.run(pages, facts, psi, add)
    return F, facts


def rebuild_case(findings: list[dict], cats: dict) -> list[str]:
    """Plain-English reasons a new site beats patching, derived only from real findings."""
    ids = {f["id"] for f in findings}
    weak = [CATEGORY_LABELS[c] for c, v in cats.items() if v < 70]
    out = []
    if len(weak) >= 3:
        out.append(f"The problems aren't in one place: {len(weak)} of {len(cats)} areas score below 70 "
                   f"({', '.join(weak[:4])}{'...' if len(weak) > 4 else ''}). Fixing them one by one means "
                   "touching almost every page and template.")
    old_names = {"legacy_tech": "retired HTML", "table_layout": "a table-based layout",
                 "outdated_cms": "an outdated CMS", "outdated_js_libs": "old JavaScript libraries",
                 "page_builder_bloat": "heavy page-builder code", "diy_builder": "a DIY template",
                 "no_viewport": "a desktop-only layout", "old_copyright_year": "content that hasn't been updated in years"}
    old = [n for k, n in old_names.items() if k in ids]
    if old:
        out.append("The site is built on outdated foundations (" + ", ".join(old[:4]) + "). Patching old code "
                   "usually costs more than building new, and the result still looks dated.")
    sec = [f for f in findings if f["category"] == "security" and f["severity"] in ("critical", "high", "medium")]
    if sec:
        out.append(f"We found {len(sec)} security and privacy gaps. A modern build closes them by default "
                   "instead of one at a time.")
    conv = [f for f in findings if f["category"] == "conversion"]
    if len(conv) >= 2:
        out.append(f"{len(conv)} conversion problems mean visitors who find you are leaving without calling or "
                   "booking. A new site can be designed around turning visitors into customers.")
    if ids & {"psi_mobile_poor", "lcp", "no_viewport", "no_responsive_images", "slow_ttfb"}:
        out.append("It's slow or awkward on phones, which is where most local customers search.")
    if ids & {"inputs_no_labels", "links_no_text", "psi_accessibility_low", "zoom_disabled"}:
        out.append("Accessibility gaps create ADA lawsuit risk. A new build can meet WCAG 2.1 AA from day one.")
    return out


def score(findings: list[Finding], psi: dict) -> dict:
    cats = {}
    for cat in WEIGHTS:
        lost = sum(SEVERITY_POINTS[f.severity] * 2 for f in findings if f.category == cat)
        cats[cat] = max(0, 100 - lost)
    m = (psi.get("mobile") or {}).get("scores", {})
    if "performance" in m:  # blend in real Lighthouse score when available
        cats["performance"] = round(0.6 * m["performance"] + 0.4 * cats["performance"])
    elif not any(f.category == "performance" for f in findings):
        cats.pop("performance")  # PageSpeed unavailable and no heuristic hits: don't claim 100
    overall = round(sum(cats[c] * WEIGHTS[c] for c in cats) / sum(WEIGHTS[c] for c in cats))
    return {"overall": overall, "categories": cats}


def grade(n: int) -> str:
    return "A" if n >= 90 else "B" if n >= 80 else "C" if n >= 70 else "D" if n >= 55 else "F"


# --------------------------------------------------------------------------- render

def render(report: dict, out: Path, lead: dict, brand: dict, report_url: str = "") -> None:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    env = Environment(loader=FileSystemLoader(HERE / "templates"),
                      autoescape=select_autoescape(["html.j2"], default_for_string=False, default=False))
    env.filters["grade"] = grade
    ctx = {"r": report, "lead": lead, "brand": brand, "labels": CATEGORY_LABELS, "report_url": report_url}
    (out / "report.html").write_text(env.get_template("report.html.j2").render(**ctx))
    (out / "email.html").write_text(env.get_template("email.html.j2").render(**ctx))
    (out / "email.txt").write_text(env.get_template("email.txt.j2").render(**ctx))
    subject = (f"Your website audit: {report['site_host']} scored {report['score']['overall']}/100 "
               f"({report['counts']['critical'] + report['counts']['high']} serious issues)")
    (out / "email.json").write_text(json.dumps({
        "to": lead.get("email"), "subject": subject, "html_file": "email.html", "text_file": "email.txt",
        "status": "awaiting_approval"}, indent=2))


def run_audit(url: str, lead: dict, out: Path, max_pages: int = 15, psi_key: str | None = None,
              brand: dict | None = None, report_url: str = "") -> dict:
    if not url.startswith("http"):
        url = "https://" + url
    out.mkdir(parents=True, exist_ok=True)
    pages, extras = crawl(url, max_pages)
    psi = {}
    if pages[0].html:
        psi = {"mobile": pagespeed(pages[0].final_url, psi_key, "mobile"),
               "desktop": pagespeed(pages[0].final_url, psi_key, "desktop")}
    findings, facts = run_checks(pages, extras, psi)
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    findings.sort(key=lambda f: (order[f.severity], -WEIGHTS[f.category]))
    sc = score(findings, psi)
    fd = [asdict(f) for f in findings]
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "url": pages[0].final_url,
        "site_host": urlparse(pages[0].final_url).netloc or urlparse(url).netloc,
        "pages_crawled": len(pages),
        "score": sc,
        "pagespeed": psi,
        "counts": {s: sum(1 for f in findings if f.severity == s) for s in order},
        "findings": fd,
        "top_issues": fd[:5],
        "rebuild_case": rebuild_case(fd, sc["categories"]),
        "total_issues": len(fd),
        "pages": facts,
    }
    (out / "report.json").write_text(json.dumps(report, indent=2))
    render(report, out, lead, brand or BRAND, report_url)
    return report


BRAND = {
    "name": "Plen Dev",
    "site": os.environ.get("PLENDEV_SITE", "https://plendev.com"),
    "phone": os.environ.get("PLENDEV_PHONE", ""),  # added later
    "email": os.environ.get("PLENDEV_EMAIL", "info@plendev.com"),
    "booking_url": os.environ.get("PLENDEV_BOOKING_URL", "https://plendev.com/book"),
    "sender_name": os.environ.get("PLENDEV_SENDER_NAME", "Alex H"),
    "sender_title": os.environ.get("PLENDEV_SENDER_TITLE", "Sales, Plen Dev"),
    "pitch": "rebuild",  # Plen Dev sells new websites, not fixes
    "address": os.environ.get("PLENDEV_ADDRESS", ""),
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("--name", default="")
    ap.add_argument("--email", default="")
    ap.add_argument("--company", default="")
    ap.add_argument("--out", default="./outbox/manual")
    ap.add_argument("--max-pages", type=int, default=15)
    ap.add_argument("--psi-key", default=os.environ.get("PAGESPEED_API_KEY"))
    a = ap.parse_args()
    lead = {"name": a.name, "email": a.email, "company": a.company, "website_url": a.url}
    r = run_audit(a.url, lead, Path(a.out), a.max_pages, a.psi_key)
    print(json.dumps({"overall": r["score"]["overall"], "categories": r["score"]["categories"],
                      "counts": r["counts"], "out": str(Path(a.out).resolve())}, indent=2))


if __name__ == "__main__":
    sys.exit(main())
