"""Company research from the prospect's own public website (robots.txt respected, slow).

Collects what a good salesperson would skim before writing: what the company does, who runs it,
how big it is (locations, states), what the site is built on, and anything worth a personal
opening line. Only public pages on the company's own domain are read.
"""
from __future__ import annotations

import re
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

import contacts

PAGES_HINT = re.compile(r"about|our-story|who-we-are|team|leadership|staff|locations?|offices|contact|history", re.I)
ROLE_RE = re.compile(
    r"\b(owner|co-owner|founder|co-founder|ceo|chief executive|president|principal|managing partner|"
    r"partner|director of marketing|marketing (director|manager)|cmo|vp of marketing|office manager|"
    r"practice manager|general manager|operations manager|coo)\b", re.I)
NAME_RE = re.compile(r"\b(Dr\.?\s)?[A-Z][a-z]+(?:\s[A-Z]\.)?\s[A-Z][a-zA-Z'\-]+\b")
STATES = ("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND "
          "OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC").split()
STATE_RE = re.compile(r",\s*(" + "|".join(STATES) + r")\s+\d{5}\b")
TECH = [("WordPress", r"wp-content|wp-includes"), ("Wix", r"wixstatic|wix\.com"), ("Squarespace", r"squarespace"),
        ("GoDaddy Website Builder", r"img1\.wsimg\.com|godaddy"), ("Weebly", r"weebly"), ("Joomla", r"/media/jui/|joomla"),
        ("Drupal", r"drupal"), ("Shopify", r"cdn\.shopify"), ("Webflow", r"webflow"), ("Duda", r"dudaone|multiscreensite"),
        ("jQuery", r"jquery"), ("Elementor", r"elementor"), ("Divi", r"et_pb_|divi")]


def _text(soup: BeautifulSoup) -> str:
    for t in soup(["script", "style", "noscript"]):
        t.decompose()
    return re.sub(r"\s+", " ", soup.get_text(" ")).strip()


def research(site: str, max_pages: int = 6) -> dict:
    sess = contacts.session()
    rb = contacts.Robots(site, sess)
    host = (urlparse(site).hostname or "").removeprefix("www.")
    out = {"summary": "", "founded": "", "people": [], "locations": 0, "states": [], "tech": [],
           "copyright_year": "", "social": [], "notes": [], "pages": []}
    if not rb.ok(site):
        return out
    queue, seen, texts, raw = [site], set(), [], ""
    while queue and len(seen) < max_pages:
        url = queue.pop(0)
        if url in seen or not rb.ok(url):
            continue
        seen.add(url)
        if len(seen) > 1:
            time.sleep(rb.delay)
        try:
            r = sess.get(url, timeout=20)
        except requests.RequestException:
            continue
        if "html" not in r.headers.get("content-type", ""):
            continue
        raw += r.text[:300000]
        soup = BeautifulSoup(r.text, "lxml")
        if url == site:
            md = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
            out["summary"] = (md.get("content") or "").strip()[:300] if md else ""
            for a in soup.find_all("a", href=True):
                u = urljoin(r.url, a["href"]).split("#")[0]
                h = (urlparse(u).hostname or "").removeprefix("www.")
                if h == host and PAGES_HINT.search(u + " " + a.get_text(" ")) and u not in queue:
                    queue.append(u)
                if re.search(r"(facebook|instagram|linkedin|x|twitter|tiktok|youtube)\.com/", u) and u not in out["social"]:
                    out["social"].append(u)
        txt = _text(soup)
        texts.append(txt[:20000])
        out["pages"].append(r.url)
    full = " ".join(texts)
    if not out["summary"] and texts:
        out["summary"] = texts[0][:300]
    m = re.search(r"\b(?:since|established|est\.|founded in|serving .{0,40} since)\s*(18|19|20)(\d\d)\b", full, re.I)
    if m:
        out["founded"] = m.group(1) + m.group(2)
    years = [int(y) for y in re.findall(r"(?:©|&copy;|copyright)\s*(?:\d{4}\s*[-–]\s*)?((?:19|20)\d\d)", raw, re.I)]
    if years:
        out["copyright_year"] = str(max(years))
    # people with roles: "Jane Smith, Owner" / "Owner: Jane Smith" / "Dr. Jane Smith ... Founder"
    people = []
    for m in ROLE_RE.finditer(full):
        lo = max(0, m.start() - 60)
        window = full[lo: m.end() + 60]
        rs, re_ = m.start() - lo, m.end() - lo
        masked = ROLE_RE.sub(lambda x: "#" * len(x.group(0)), window)  # role words are never part of a name
        names = list(NAME_RE.finditer(masked))
        # the name closest to the role ("Jane Smith, Owner" or "Owner: Jane Smith")
        nm = min(names, key=lambda n: rs - n.end() if n.end() <= rs else (n.start() - re_) + 5, default=None)
        if nm and not ROLE_RE.fullmatch(nm.group(0)):
            p = {"name": window[nm.start():nm.end()].strip(), "role": m.group(0).title()}
            if p not in people and not re.search(r"(Our|The|Your|Contact|About|Read|Learn|Call|Book)\b", p["name"]):
                people.append(p)
    out["people"] = people[:6]
    out["states"] = sorted(set(STATE_RE.findall(full)))
    # distinct "City, ST 12345" endings = distinct addresses listed
    addrs = set(re.findall(r"([A-Z][A-Za-z .]{1,30},\s*(?:" + "|".join(STATES) + r")\s+\d{5})\b", full))
    out["locations"] = len(addrs)
    out["tech"] = [name for name, pat in TECH if re.search(pat, raw, re.I)]
    if len(out["states"]) > 1:
        out["notes"].append(f"multi-state: {', '.join(out['states'])}")
    if out["locations"] > 2:
        out["notes"].append(f"about {out['locations']} street addresses listed (multi-location)")
    return out
