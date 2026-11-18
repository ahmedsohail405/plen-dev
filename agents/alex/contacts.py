"""Find a publicly listed business email on a prospect's own website.

Rules: obey robots.txt, fetch at most ~5 pages slowly, only use addresses the business
publishes (mailto links or visible text). Never guess addresses (no first.last@ patterns).
"""
from __future__ import annotations

import re
import time
import urllib.robotparser
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config import CRAWL_DELAY

UA = "PlenDevAuditBot/1.0 (+https://plendev.com/audit-bot)"
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,24}")
OBF_RE = re.compile(r"([A-Za-z0-9._%+-]+)\s*[\[(]\s*at\s*[\])]\s*([A-Za-z0-9-]+)\s*[\[(]\s*dot\s*[\])]\s*([A-Za-z]{2,10})", re.I)
ROLE = ("info", "contact", "hello", "office", "frontdesk", "front.desk", "appointments", "appts", "admin",
        "inquiries", "enquiries", "sales", "team", "reception", "booking", "bookings", "service", "support", "mail")
JUNK = ("example.", "domain.com", "yourdomain", "email.com", "sentry", "wixpress", "godaddy", "@2x", ".png", ".jpg",
        ".jpeg", ".gif", ".webp", ".svg", "noreply", "no-reply", "donotreply", "privacy@", "abuse@", "webmaster@",
        "postmaster@", "careers@", "jobs@", "hr@", "billing@", "u003e")
FREEMAIL = ("gmail.com", "yahoo.com", "aol.com", "hotmail.com", "outlook.com", "icloud.com", "verizon.net", "optonline.net", "msn.com", "live.com")
CONTACT_HINT = re.compile(r"contact|about|team|location|appointment|book|reach|get-in-touch", re.I)


class Robots:
    def __init__(self, site: str, session: requests.Session):
        self.rp = urllib.robotparser.RobotFileParser()
        try:
            r = session.get(urljoin(site, "/robots.txt"), timeout=15)
            self.rp.parse(r.text.splitlines() if r.status_code == 200 else [])
            if r.status_code in (401, 403):
                self.rp.disallow_all = True
        except requests.RequestException:
            self.rp.parse([])
        self.delay = max(CRAWL_DELAY, float(self.rp.crawl_delay(UA) or 0))

    def ok(self, url: str) -> bool:
        return self.rp.can_fetch(UA, url)


def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept": "text/html,*/*"})
    return s


def _emails_from(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    found = []
    for a in soup.select('a[href^="mailto:" i]'):
        found.append(a["href"].split(":", 1)[1].split("?")[0])
    text = soup.get_text(" ")
    found += EMAIL_RE.findall(text)
    found += [f"{a}@{b}.{c}" for a, b, c in OBF_RE.findall(text)]
    return found


def rank(email: str, site_host: str) -> int:
    local, _, dom = email.partition("@")
    host = site_host.removeprefix("www.")
    s = 0
    if dom == host or host.endswith("." + dom) or dom.endswith("." + host):
        s += 50
    elif dom in FREEMAIL:
        s += 20  # many small businesses publish a Gmail address; fine if it is on their own site
    else:
        s -= 30  # some other company's address (agency, platform): avoid
    if local.split(".")[0] in ROLE or local in ROLE:
        s += 30
    return s


def find_contact(site: str, known_email: str = "", max_pages: int = 5) -> dict:
    sess = session()
    host = (urlparse(site).hostname or "").lower()
    robots = Robots(site, sess)
    res = {"email": "", "source_url": "", "candidates": [], "robots_blocked": False, "pages_checked": 0}
    if not robots.ok(site):
        res["robots_blocked"] = True
        return res
    seen, queue, found = set(), [site], {}
    if known_email:
        found[known_email.lower()] = "directory listing"
    while queue and res["pages_checked"] < max_pages:
        url = queue.pop(0)
        if url in seen or not robots.ok(url):
            continue
        seen.add(url)
        if res["pages_checked"]:
            time.sleep(robots.delay)
        try:
            r = sess.get(url, timeout=20)
        except requests.RequestException:
            continue
        res["pages_checked"] += 1
        if "html" not in r.headers.get("content-type", ""):
            continue
        for e in _emails_from(r.text):
            e = e.strip().strip(".").lower()
            if EMAIL_RE.fullmatch(e) and not any(j in e for j in JUNK):
                found.setdefault(e, r.url)
        if url == site:  # queue likely contact/about pages from the homepage
            soup = BeautifulSoup(r.text, "lxml")
            links = [urljoin(r.url, a["href"]) for a in soup.find_all("a", href=True)
                     if CONTACT_HINT.search(a["href"] + " " + a.get_text(" "))]
            links += [urljoin(site, p) for p in ("/contact", "/contact-us", "/about")]
            for l in links:
                if urlparse(l).hostname and urlparse(l).hostname.lower().removeprefix("www.") == host.removeprefix("www.") and l not in queue:
                    queue.append(l.split("#")[0])
    ranked = sorted(found.items(), key=lambda kv: -rank(kv[0], host))
    res["candidates"] = [{"email": e, "source_url": u, "score": rank(e, host)} for e, u in ranked]
    if ranked and rank(ranked[0][0], host) > 0:
        res["email"], res["source_url"] = ranked[0]
    return res
