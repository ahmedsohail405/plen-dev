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
ENGINE_VERSION = "2026-11-18.3-industry"  # shown on /healthz so the live version can be checked

# Category weights for the overall score (sum = 100)
WEIGHTS = {
    "conversion": 15,
    "performance": 12,
    "mobile": 12,
    "security": 10,
    "seo_structure": 10,
    "technical": 9,
    "design": 9,
    "on_page": 8,
    "accessibility": 7,
    "local_seo": 5,
    "ai_readiness": 3,
}
CATEGORY_LABELS = {
    "conversion": "Conversion & trust",
    "performance": "Speed & Core Web Vitals",
    "mobile": "Mobile experience",
    "seo_structure": "SEO structure & keywords",
    "security": "Security & privacy",
    "technical": "Technical SEO",
    "design": "Design & technology age",
    "accessibility": "Accessibility (ADA)",
    "on_page": "On-page SEO",
    "local_seo": "Local SEO",
    "ai_readiness": "AI search readiness",
}
# Points a category loses per finding. One critical problem alone takes a category to 65,
# two high problems to 64, so a category only scores well when it has little wrong.
SEVERITY_POINTS = {"critical": 35, "high": 18, "medium": 8, "low": 3}
# The overall score can't hide serious problems behind good averages:
CAPS = [("critical", 1, 64, "a critical problem"), ("high", 4, 74, "4 or more serious problems")]


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
    evidence: dict | None = None  # {"marker": n, "where": "phone"|"desktop"|"close-up"} for annotated screenshots


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
    if extras["sitemap"].status != 200:
        # Many sites (WordPress/Yoast/Rank Math) publish the sitemap elsewhere and list it in robots.txt
        cands = re.findall(r"^\s*sitemap:\s*(\S+)", extras["robots"].html or "", re.I | re.M)
        cands += [f"{site}/sitemap_index.xml", f"{site}/wp-sitemap.xml"]
        for c in cands[:5]:
            if urlparse(c).netloc.lower().removeprefix("www.") != base_host.removeprefix("www."):
                continue
            alt = fetch(sess, c)
            if alt.status == 200:
                extras["sitemap"] = alt
                break
    sm = extras["sitemap"]
    sitemap_urls: list[str] = []
    if sm.status == 200 and sm.bytes:
        try:
            locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", sess.get(sm.final_url, timeout=TIMEOUT).text)
            posts: list[str] = []
            for child in [u for u in locs if u.endswith(".xml")][:4]:  # sitemap index: read the page/post sitemaps
                try:
                    got = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", sess.get(child, timeout=TIMEOUT).text)
                except requests.RequestException:
                    continue
                (posts if re.search(r"post|blog|news|article|categor|tag|author", child.split("/")[-1], re.I) else locs).extend(got)
            sitemap_urls[:] = [u for u in locs if not u.endswith(".xml")][:500]
            extras["sitemap_post_urls"] = posts[:500]
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
    extras["sitemap_urls"] = sitemap_urls
    return pages, extras


# --------------------------------------------------------------------------- PageSpeed

def pagespeed(url: str, key: str | None, strategy: str) -> dict | None:
    params = {"url": url, "strategy": strategy, "category": ["performance", "seo", "accessibility", "best-practices"]}
    if key:
        params["key"] = key
    try:
        url_psi = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
        r = requests.get(url_psi, params=params, timeout=120)
        if r.status_code in (429, 500, 502, 503):
            time.sleep(5)
            r = requests.get(url_psi, params=params, timeout=120)
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
            re.search(r'(?:\b(?:src|data-src|data-lazy-src|data-bg|srcset|data-srcset)=["\'][^"\']*?|\burl\(\s*["\']?)'
                      r'http://(?!www\.w3\.org|schemas\.)', pg.html or "", re.I)),
        "tel_link": bool(soup.find("a", href=re.compile(r"^tel:", re.I))),
        "phone_text": bool(re.search(r"\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}", text)),
        "form": bool(soup.find("form")),
        "cta": bool(re.search(r"\b(book|schedule|get a quote|free (quote|consultation|estimate)|contact us|call now|request)\b",
                               text, re.I)),
        "analytics": any(k in html_l for k in ("googletagmanager.com", "gtag(", "google-analytics.com", "plausible.io",
                                                 "clarity.ms")),
        "favicon": bool(soup.find("link", rel=lambda v: v and "icon" in " ".join(v).lower())),
        "address_text": bool(re.search(r"\b\d{1,5}\s+(?:[A-Za-z0-9.'-]+\s+){0,4}(?:st|street|ave|avenue|rd|road|blvd|boulevard|ln|lane|dr|drive|pl|place|pkwy|parkway|hwy|highway|way|ct|court|sq|square|ter|terrace)\b\.?(?!\s+(?:results|more|traffic|sales|growth|leads))",
                                       text, re.I)),
        "dead_nav_links": sum(1 for a in (soup.select("nav a, header a") or []) if (a.get("href") or "").strip() in ("#", "", "javascript:void(0)", "javascript:;")),
        "maps_embed": "google.com/maps" in html_l or "maps.googleapis" in html_l,
        "elapsed_ms": pg.elapsed_ms,
        "bytes": pg.bytes,
    }


def run_checks(pages: list[Page], extras: dict, psi: dict, lead: dict | None = None, vis: dict | None = None,
               out: Path | None = None, more: dict | None = None) -> tuple[list[Finding], list[dict]]:
    F: list[Finding] = []
    html_pages = [p for p in pages if p.html and p.status == 200]
    facts = [page_facts(p) for p in html_pages]
    home = facts[0] if facts else None

    def add(cat, fid, sev, title, detail, fix, pgs=None, impact="", evidence=None):
        F.append(Finding(cat, fid, sev, title, detail, fix, (pgs or [])[:10], impact, evidence))

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
        add("technical", "no_sitemap", "high", "No XML sitemap found",
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
    dead_nav = [f["url"] for f in facts if f.get("dead_nav_links")]
    if home and home.get("dead_nav_links"):
        add("technical", "dead_menu_links", "low", "Menu items that go nowhere",
            f"{home['dead_nav_links']} link(s) in the header menu point to '#' and don't open a page.",
            "Point every menu item to a real page.", dead_nav)
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
    import industry
    more = more if more is not None else {}
    ind = {"key": "general", "label": "General business", "search_term": "", "source": "none"}
    if home:
        home_soup = BeautifulSoup(html_pages[0].html, "lxml")
        ind = industry.detect(lead or {}, home_soup.get_text(" ").lower(),
                              (home["title"] + " " + " ".join(home["h1"])).lower(),
                              [t for f in facts for t in f["jsonld"]])
    more["industry"] = ind
    deep_checks.run(pages, facts, psi, add, ind)
    if facts:
        import seo_deep
        more["seo"] = seo_deep.run(pages, facts, extras, lead or {}, add, ind)
    if vis and vis.get("ok") and out is not None:
        import visual
        more["visual"] = visual.findings(vis, out, add, ind)
    F[:] = dedupe(F, psi, bool(vis and vis.get("ok")))
    for f in F:  # industry wording for "what it costs you"
        f.impact = industry.IMPACT.get(ind["key"], {}).get(f.id, f.impact)
    return F, facts


def dedupe(F: list[Finding], psi: dict, measured_cta: bool = False) -> list[Finding]:
    """Measured checks replace heuristic guesses of the same thing, so nothing is counted twice."""
    ids = {f.id for f in F}
    drop = set()
    if ids & {"no_cta_first_screen_mobile", "no_cta_first_screen_desktop"} or measured_cta:
        drop.add("contact_not_above_fold")
    if "no_cta" in ids:
        drop |= {"no_cta_first_screen_mobile", "no_cta_first_screen_desktop"}
    if "performance" in ((psi.get("mobile") or {}).get("scores") or {}):
        drop |= {"lcp_measured", "cls_measured"}  # Google's numbers take precedence
    if "no_modern_images" in ids:
        drop.add("old_image_formats")
    return [f for f in F if f.id not in drop]


# Checks that run on every audit, shown as a pass/fail checklist. "needs" = only listed when that data exists.
CHECKLIST = [
    ("no_https", "Secure HTTPS connection", None), ("no_http_redirect", "Redirects http to https", None),
    ("no_hsts", "Forces HTTPS (HSTS)", None), ("no_csp", "Content Security Policy", None),
    ("no_clickjack_protection", "Clickjacking protection", None), ("outdated_cms", "Up-to-date CMS", None),
    ("outdated_js_libs", "No outdated JavaScript libraries", None), ("no_privacy_policy", "Privacy policy", None),
    ("no_viewport", "Mobile viewport set", None), ("mobile_overflow", "No sideways scrolling on phones", "visual"),
    ("small_text_mobile", "Readable text size on phones", "visual"), ("tap_targets_small", "Tap targets big enough", "visual"),
    ("mobile_overlay", "No pop-up covering the phone screen", "visual"),
    ("no_cta_first_screen_mobile", "Call/book button on the first phone screen", "visual"),
    ("no_cta_first_screen_desktop", "Call/book button on the first desktop screen", "visual"),
    ("lcp_measured", "Main content shows within 2.5s on a phone", "speed"),
    ("cls_measured", "Page doesn't jump while loading", "speed"), ("page_weight", "Homepage under 2.5 MB", "visual"),
    ("heavy_images", "No oversized image files", "visual"), ("broken_images", "No broken images", "visual"),
    ("stretched_images", "No stretched images", "visual"), ("blurry_images", "No blurry images", "visual"),
    ("stock_photos", "Real photos, not stock", "visual"), ("js_errors", "No JavaScript errors", "visual"),
    ("no_robots", "robots.txt present", None), ("no_sitemap", "XML sitemap", None),
    ("broken_pages", "No broken internal links", None), ("noindex", "No pages accidentally hidden from Google", None),
    ("no_canonical", "Canonical tags", None), ("mixed_content", "No insecure resources", None),
    ("no_analytics", "Analytics installed", None), ("dup_titles", "Unique page titles", None),
    ("no_og", "Social sharing tags", None), ("no_location_pages", "Pages for each area served", None),
    ("keyword_gaps", "Pages for what customers search", "service"), ("home_no_location", "Area named in homepage title", None),
    ("too_few_pages", "Enough pages to rank", None), ("heading_hierarchy", "Headings in order", None),
    ("near_duplicate_pages", "No duplicate pages", None), ("cannibalization", "No pages competing for one keyword", None),
    ("orphan_pages", "All pages linked internally", None), ("ugly_urls", "Search-friendly page addresses", None),
    ("no_localbusiness_schema", "LocalBusiness schema", None), ("no_phone", "Phone number on homepage", None),
    ("no_address", "Street address on site", None), ("no_map", "Google Map", None),
    ("no_cta", "Clear call to action", None), ("no_form", "Contact or quote form", None),
    ("no_reviews", "Reviews or testimonials", None), ("no_verified_reviews", "Verifiable reviews (Google, Yelp)", None),
    ("no_trust_badges", "Trust signals", None),
    ("inputs_no_labels", "Form fields labeled", None), ("links_no_text", "Links have readable names", None),
    ("zoom_disabled", "Zoom allowed on phones", None), ("old_copyright_year", "Content kept up to date", None),
    ("legacy_tech", "Modern code", None), ("no_llms_txt", "llms.txt for AI search", None),
    ("ai_bots_blocked", "AI search engines allowed", None), ("no_structured_data", "Structured data", None),
]


def checklist(findings: list[dict], have: set, industry_key: str = "general") -> list[dict]:
    import industry
    failed = {f["id"]: f["severity"] for f in findings}
    alias = {"no_cta_first_screen_mobile": "no_cta", "no_cta_first_screen_desktop": "no_cta"}
    # checks that can't run when another one failed (no HTTPS -> no redirect/HSTS to test)
    blocked = {"no_http_redirect", "no_hsts", "mixed_content"} if "no_https" in failed else set()
    if "home_unreachable" in failed:
        return []
    rows = []
    for fid, label, needs in CHECKLIST + industry.checklist_rows(industry_key):
        if (needs and needs not in have) or fid in blocked:
            continue
        sev = failed.get(fid) or (failed.get(alias[fid]) if fid in alias else None)
        rows.append({"id": fid, "label": label, "ok": sev is None, "severity": sev})
    return rows


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


def score(findings: list[Finding], psi: dict, measured: set | None = None) -> dict:
    """measured: categories that were actually tested this run ("performance", "mobile").
    A category we couldn't test is left out rather than given a free 100."""
    measured = measured or set()
    cats = {}
    for cat in WEIGHTS:
        lost = sum(SEVERITY_POINTS[f.severity] for f in findings if f.category == cat)
        cats[cat] = max(0, 100 - lost)
    m = (psi.get("mobile") or {}).get("scores", {})
    if "performance" in m:  # blend in real Lighthouse score when available
        cats["performance"] = round(0.6 * m["performance"] + 0.4 * cats["performance"])
    elif "performance" not in measured and not any(f.category == "performance" for f in findings):
        cats.pop("performance")
    if "mobile" not in measured and not any(f.category == "mobile" for f in findings):
        cats.pop("mobile")
    avg = round(sum(cats[c] * WEIGHTS[c] for c in cats) / sum(WEIGHTS[c] for c in cats))
    overall, cap_reason = avg, ""
    for sev, count, cap, why in CAPS:
        if sum(1 for f in findings if f.severity == sev) >= count and overall > cap:
            overall, cap_reason = cap, f"Capped at {cap} because the site has {why}."
    return {"overall": overall, "average": avg, "cap_reason": cap_reason, "categories": cats}


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
              brand: dict | None = None, report_url: str = "", visual: bool | None = None) -> dict:
    """visual: render the homepage in headless Chromium for screenshots, layout, image and measured-speed
    checks (adds ~20-40 s). Defaults to the VISUAL_AUDIT env var (on unless set to 0)."""
    if visual is None:
        visual = os.environ.get("VISUAL_AUDIT", "1") != "0"
    if not url.startswith("http"):
        url = "https://" + url
    out.mkdir(parents=True, exist_ok=True)
    pages, extras = crawl(url, max_pages)
    psi = {}
    if pages[0].html:
        psi = {"mobile": pagespeed(pages[0].final_url, psi_key, "mobile"),
               "desktop": pagespeed(pages[0].final_url, psi_key, "desktop")}
    vis = {}
    if visual and pages[0].html:
        import visual as visual_mod
        vis = visual_mod.run(pages[0].final_url, out)
    more: dict = {}
    findings, facts = run_checks(pages, extras, psi, lead, vis, out, more)
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    findings.sort(key=lambda f: (order[f.severity], -WEIGHTS[f.category]))
    vm = (more.get("visual") or {}).get("measured") or {}
    speed_measured = "performance" in ((psi.get("mobile") or {}).get("scores") or {}) or bool(vm.get("lcp_s") or vm.get("timed_out"))
    measured = ({"performance"} if speed_measured else set()) | ({"mobile"} if vis.get("ok") else set())
    sc = score(findings, psi, measured)
    fd = [asdict(f) for f in findings]
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "url": pages[0].final_url,
        "site_host": urlparse(pages[0].final_url).netloc or urlparse(url).netloc,
        "pages_crawled": len(pages),
        "score": sc,
        "pagespeed": psi,
        "speed_measured": speed_measured,
        "visual": more.get("visual") or ({"error": vis.get("error")} if vis else {}),
        "seo": more.get("seo") or {},
        "industry": more.get("industry") or {},
        "checklist": checklist(fd, ({"visual"} if vis.get("ok") else set()) | ({"speed"} if speed_measured else set())
                               | ({"service"} if (more.get("seo") or {}).get("searches") else set()),
                               (more.get("industry") or {}).get("key", "general")),
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
