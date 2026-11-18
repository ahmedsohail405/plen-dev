"""Demo homepage concepts for interested leads.

Alex builds 2-3 homepage concepts from the prospect's real details (name, phone, address, services,
area) and industry defaults, hosts them at /d/<token>/<n>, and screenshots them for Ahmed's review.
Nothing is invented about the business: no fake reviews, awards, years or stats. Where real content
is missing the concept shows a clearly marked placeholder (for example "Your Google reviews here").
"""
from __future__ import annotations

import re
import secrets
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader, select_autoescape

import config as C
import contacts
import store

env = Environment(loader=FileSystemLoader(C.HERE / "templates" / "demos"), autoescape=select_autoescape(["html", "j2"]))

STYLES = [
    {"file": "clean.html.j2", "name": "Clean and modern"},
    {"file": "bold.html.j2", "name": "Bold and confident"},
    {"file": "warm.html.j2", "name": "Warm and friendly"},
]

INDUSTRY = {
    "dental": {"noun": "dental practice", "headline": "Gentle, modern dental care for the whole family",
               "cta": "Book an appointment", "services": ["Cleanings and checkups", "Teeth whitening", "Invisalign and clear aligners", "Implants", "Emergency visits", "Kids' dentistry"]},
    "medical": {"noun": "practice", "headline": "Care that fits your life, close to home", "cta": "Book a visit",
                "services": ["Primary care", "Annual physicals", "Same-day visits", "Telehealth", "Lab work", "Vaccinations"]},
    "home_healthcare": {"noun": "home care agency", "headline": "Trusted care at home for the people you love",
                        "cta": "Get a free care consultation", "services": ["Personal care", "Companionship", "Skilled nursing", "Respite care", "Dementia care", "Care coordination"]},
    "real_estate": {"noun": "real estate office", "headline": "Find your place in the neighborhood", "cta": "Talk to an agent",
                    "services": ["Buying", "Selling", "Rentals", "Free home valuation", "Investment properties", "Relocation help"]},
    "legal": {"noun": "law firm", "headline": "Clear advice when it matters most", "cta": "Request a free consultation",
              "services": ["Personal injury", "Real estate law", "Family law", "Wills and estates", "Business law", "Immigration"]},
    "accounting": {"noun": "accounting firm", "headline": "Taxes and books, handled", "cta": "Schedule a consultation",
                   "services": ["Tax preparation", "Bookkeeping", "Payroll", "Business advisory", "IRS representation", "Small business setup"]},
    "beauty": {"noun": "salon", "headline": "Look and feel your best", "cta": "Book now",
               "services": ["Haircuts and styling", "Color", "Nails", "Facials", "Brows and lashes", "Bridal"]},
    "fitness": {"noun": "studio", "headline": "Stronger every week", "cta": "Book a free class",
                "services": ["Personal training", "Group classes", "Strength", "HIIT", "Yoga", "Nutrition coaching"]},
    "contractor": {"noun": "contractor", "headline": "Done right, on time, at a fair price", "cta": "Get a free estimate",
                   "services": ["Repairs", "Installations", "Renovations", "Emergency service", "Inspections", "Maintenance plans"]},
    "restaurant": {"noun": "restaurant", "headline": "Your new favorite table", "cta": "Reserve a table",
                   "services": ["Dine in", "Takeout", "Delivery", "Private events", "Catering", "Brunch"]},
    "veterinary": {"noun": "vet clinic", "headline": "Caring for the pets you love", "cta": "Book a visit",
                   "services": ["Wellness exams", "Vaccinations", "Dental care", "Surgery", "Urgent care", "Puppy and kitten care"]},
    "auto": {"noun": "auto shop", "headline": "Honest repairs, back on the road fast", "cta": "Book a service",
             "services": ["Oil changes", "Brakes", "Diagnostics", "Tires", "Inspections", "AC repair"]},
}
DEFAULT = {"noun": "business", "headline": "Serving the neighborhood with care", "cta": "Get in touch",
           "services": ["Our services", "Consultations", "Appointments", "Support"]}
GENERIC = re.compile(r"^(home|about( us)?|contact( us)?|blog|news|gallery|faq|faqs|menu|login|careers|privacy.*|terms.*|"
                     r"search|shop|cart|more|services|our services|team|our team|testimonials|reviews|locations?|book.*|"
                     r"call.*|skip to.*|read more|learn more|click here|\W*)$", re.I)


def scrape(site: str) -> dict:
    """Public facts from the homepage (robots.txt respected)."""
    sess = contacts.session()
    if not contacts.Robots(site, sess).ok(site):
        return {}
    try:
        r = sess.get(site, timeout=20)
    except requests.RequestException:
        return {}
    soup = BeautifulSoup(r.text, "lxml")
    md = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    tel = soup.find("a", href=re.compile(r"^tel:", re.I))
    cands = [h.get_text(" ", strip=True) for h in soup.select("nav a, header a, h2, h3")]
    services = []
    for c in cands:
        c = re.sub(r"\s+", " ", c).strip(" -|•")
        if 3 <= len(c) <= 40 and not GENERIC.match(c) and not re.search(r"\d{3}.*\d{4}|@", c) and c not in services:
            services.append(c)
    return {"tagline": (md.get("content") or "").strip()[:180] if md else "",
            "phone": tel["href"][4:].strip() if tel else "", "services": services[:6]}


def build(p: dict, count: int | None = None) -> list[dict]:
    count = count or C.DEMO_COUNT
    info = INDUSTRY.get(p.get("category", ""), DEFAULT)
    facts = scrape(p["website"]) if not C.E("ALEX_DEMO_NO_SCRAPE") else {}
    services = facts.get("services") or []
    if len(services) < 3:
        services = info["services"]
    area = {"brooklyn": "Brooklyn", "queens": "Queens", "manhattan": "Manhattan", "nassau": "Nassau County",
            "suffolk": "Suffolk County"}.get(p.get("area", ""), p.get("area", "") or "New York")
    ctx = {"name": p["business_name"], "noun": info["noun"], "headline": info["headline"], "cta": info["cta"],
           "services": services[:6], "area": area, "phone": p.get("phone") or facts.get("phone", ""),
           "address": p.get("address", ""), "email": p.get("contact", {}).get("email", ""),
           "tagline": facts.get("tagline") or f"A {info['noun']} serving {area}.", "company": C.COMPANY}
    p.setdefault("demo_token", secrets.token_urlsafe(18))
    out_dir = store.path(p["id"]).parent / "demos"
    out_dir.mkdir(parents=True, exist_ok=True)
    demos = []
    for i, st in enumerate(STYLES[:count], 1):
        (out_dir / f"{i}.html").write_text(env.get_template(st["file"]).render(**ctx))
        demos.append({"n": i, "name": st["name"], "url": f"{C.PUBLIC_BASE}/d/{p['demo_token']}/{i}",
                      "image": f"{C.PUBLIC_BASE}/d/{p['demo_token']}/{i}.png"})
    shoot(out_dir, len(demos))
    p["demos"] = demos
    store.event(p, "demos_built", count=len(demos))
    return demos


def shoot(out_dir: Path, n: int) -> None:
    """Desktop screenshots (top of page) for Ahmed's WhatsApp/approval preview. Skipped if Playwright is missing."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return _shoot_node(out_dir, n)
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            pg = b.new_page(viewport={"width": 1280, "height": 800})
            for i in range(1, n + 1):
                pg.goto((out_dir / f"{i}.html").resolve().as_uri(), wait_until="load", timeout=20000)
                pg.screenshot(path=str(out_dir / f"{i}.png"))
                mp = b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
                mp.goto((out_dir / f"{i}.html").resolve().as_uri(), wait_until="load", timeout=20000)
                mp.screenshot(path=str(out_dir / f"{i}-mobile.png"))
                mp.close()
            b.close()
    except Exception as e:  # noqa: BLE001
        print("demo screenshots skipped:", e)


NODE_SHOT = """
const {chromium} = require('playwright');
(async () => { const [dir, n] = process.argv.slice(1); const b = await chromium.launch();
  for (let i = 1; i <= Number(n); i++) {
    const p = await b.newPage({viewport: {width: 1280, height: 800}});
    await p.goto('file://' + dir + '/' + i + '.html'); await p.waitForTimeout(400);
    await p.screenshot({path: dir + '/' + i + '.png'});
    const m = await b.newPage({viewport: {width: 390, height: 844}, deviceScaleFactor: 2});
    await m.goto('file://' + dir + '/' + i + '.html'); await m.waitForTimeout(300);
    await m.screenshot({path: dir + '/' + i + '-mobile.png'});
  }
  await b.close(); })();
"""


def _shoot_node(out_dir: Path, n: int) -> None:
    import shutil
    import subprocess
    if not shutil.which("node"):
        return
    try:
        subprocess.run(["node", "-e", NODE_SHOT, str(out_dir.resolve()), str(n)], timeout=120, check=True,
                       capture_output=True)
    except Exception as e:  # noqa: BLE001
        print("demo screenshots skipped:", e)
