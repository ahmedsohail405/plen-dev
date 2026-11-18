"""Deep SEO: does the site's structure match what the business needs to rank for?

Checks, all from the crawled pages and real search data:
- service + area page map: areas the site says it serves vs. pages that target them
- searches people actually type (Google autocomplete for "<service> <area>"), and whether a page targets each
  (autocomplete shows real demand but not volumes; exact monthly volumes need a paid keyword API)
- homepage title/H1 naming the service and the area
- heading hierarchy, near-duplicate pages, pages competing for the same keyword (cannibalization)
- internal linking: orphan pages from the sitemap, generic anchor text, weak homepage linking
- URL structure, breadcrumbs, Service schema, site size
"""
from __future__ import annotations

import json
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

# Areas Plen Dev targets first; any "City, ST" found on the site is added too.
NY_AREAS = [
    "brooklyn", "queens", "manhattan", "bronx", "staten island", "long island", "nassau", "suffolk", "new york city",
    "nyc", "williamsburg", "bushwick", "park slope", "bay ridge", "dumbo", "greenpoint", "bensonhurst", "flatbush",
    "astoria", "long island city", "flushing", "jamaica", "forest hills", "bayside", "jackson heights", "ridgewood",
    "harlem", "upper east side", "upper west side", "midtown", "soho", "tribeca", "chelsea", "hempstead", "garden city",
    "huntington", "hicksville", "great neck", "mineola", "levittown", "massapequa", "westchester", "yonkers",
    "jersey city", "hoboken", "newark",
]
GENERIC_ANCHORS = {"click here", "read more", "learn more", "more", "here", "this", "details", "more info", "continue reading"}
SKIP_TYPES = {"organization", "localbusiness", "website", "webpage", "corporation", "person", "place", "thing",
              "breadcrumblist", "imageobject", "sitenavigationelement", "searchaction", "readaction", "faqpage",
              "question", "answer", "article", "blogposting", "collectionpage", "aboutpage", "contactpage",
              "professionalservice", "homeandconstructionbusiness", "wpheader", "wpfooter", "postaladdress",
              "geocoordinates", "openinghoursspecification", "offer", "aggregaterating", "review", "rating",
              "contactpoint", "listitem", "itemlist", "service", "product", "videoobject", "event"}
BLOGGY = re.compile(r"/(blog|news|post|posts|category|tag|author|20\d\d|page/\d+)(/|$)", re.I)
UTILITY = re.compile(r"/(privacy|terms|cookie|cart|checkout|account|login|wp-|feed|sitemap|thank)", re.I)


def _main_text(soup: BeautifulSoup) -> str:
    s = BeautifulSoup(str(soup), "lxml")
    for t in s(["script", "style", "noscript", "header", "nav", "footer", "form", "svg"]):
        t.decompose()
    return re.sub(r"\s+", " ", s.get_text(" ")).strip().lower()


def _shingles(text: str, k: int = 5) -> set:
    w = re.findall(r"[a-z0-9']+", text)
    return {" ".join(w[i:i + k]) for i in range(max(0, len(w) - k + 1))}


def _core_title(t: str) -> str:
    t = re.split(r"\s[|\-–—:]\s", t or "")[0]
    return re.sub(r"[^a-z0-9 ]", "", t.lower()).strip()


def _service_term(lead: dict, pages_soup: list) -> str:
    ind = (lead.get("industry") or lead.get("category") or "").strip().lower()
    if ind:
        return re.sub(r"[^a-z &-]", "", ind)[:40]
    for _, soup in pages_soup[:1]:
        for t in soup.find_all("script", type="application/ld+json"):
            try:
                d = json.loads(t.string or "")
            except (ValueError, TypeError):
                continue
            for item in (d.get("@graph", [d]) if isinstance(d, dict) else d if isinstance(d, list) else []):
                ty = item.get("@type") if isinstance(item, dict) else None
                for x in ([ty] if isinstance(ty, str) else ty or []):
                    if isinstance(x, str) and x.lower() not in SKIP_TYPES:
                        return re.sub(r"(?<!^)(?=[A-Z])", " ", x).lower()
    return ""


def _areas(text: str, soup_home) -> list[str]:
    found = []
    for a in NY_AREAS:
        if re.search(rf"\b{re.escape(a)}\b", text):
            found.append(a)
    for m in re.finditer(r"\b([A-Z][a-z]+(?: [A-Z][a-z]+)?),\s?(NY|NJ|CT|CA|TX|FL|PA|MA|IL|GA|NC|VA|WA|AZ|CO|OH|MI|MD)\b",
                         soup_home.get_text(" ") if soup_home else ""):
        c = m.group(1).lower()
        if c not in found and c not in ("new york",):
            found.append(c)
    # "nyc" / "new york city" are the same place; keep the first one
    if "nyc" in found and "new york city" in found:
        found.remove("nyc")
    return found[:12]


def autocomplete(q: str) -> list[str]:
    try:
        r = requests.get("https://suggestqueries.google.com/complete/search",
                         params={"client": "firefox", "hl": "en", "gl": "us", "q": q}, timeout=8,
                         headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            return [s for s in r.json()[1] if isinstance(s, str)][:8]
    except (requests.RequestException, ValueError, IndexError):
        pass
    return []


def run(pages, facts, extras, lead: dict, add) -> dict:
    ok = [(p, BeautifulSoup(p.html, "lxml")) for p in pages if p.html and p.status < 400]
    if not ok:
        return {}
    home_p, home = ok[0]
    hf = facts[0] if facts else {}
    site_text = " ".join(_main_text(s) for _, s in ok)
    full_text = " ".join(re.sub(r"\s+", " ", s.get_text(" ")).lower() for _, s in ok)
    page_meta = []  # (url, title, h1, path)
    for (p, s), f in zip(ok, facts):
        page_meta.append({"url": p.final_url, "path": urlparse(p.final_url).path.lower(), "title": f.get("title", ""),
                          "h1": (f.get("h1") or [""])[0] if f.get("h1") else "", "words": f.get("word_count", 0)})
    service = _service_term(lead, ok)
    areas = _areas(full_text, home)
    out = {"service": service, "areas": areas, "searches": [], "page_count": len(set(extras.get("sitemap_urls", [])) | {m["url"] for m in page_meta})}

    def targets(term: str) -> list[str]:
        t = term.lower()
        return [m["url"] for m in page_meta if t in (m["title"] + " " + m["h1"]).lower() or t.replace(" ", "-") in m["path"]]

    # ---- areas served vs. pages for them
    inner = [m for m in page_meta[1:]]
    area_pages = {a: [m["url"] for m in inner if a in (m["title"] + " " + m["h1"]).lower() or a.replace(" ", "-") in m["path"]]
                  for a in areas}
    sm_paths = [urlparse(u).path.lower() for u in extras.get("sitemap_urls", [])]
    for a in areas:
        if not area_pages[a] and any(a.replace(" ", "-") in sp for sp in sm_paths):
            area_pages[a] = ["(in sitemap)"]
    served_no_page = [a for a in areas if not area_pages[a]]
    out["area_pages"] = area_pages
    if len(areas) >= 2 and len(served_no_page) >= 2:
        add("seo_structure", "no_location_pages", "high",
            f"No pages for {len(served_no_page)} of the {len(areas)} areas you mention",
            "The site mentions " + ", ".join(a.title() for a in areas[:6]) + " but has no page built to rank in "
            + ", ".join(a.title() for a in served_no_page[:5]) + ".",
            "Create one location page per area with unique content, map, reviews and LocalBusiness schema.",
            impact="Google ranks pages, not businesses. Without a page for an area, you rarely show up when people there search.")

    # ---- what people search (Google autocomplete), and whether a page targets it
    if service:
        for a in (areas[:3] or [""]):
            for q in [f"{service} {a}".strip(), f"{service} near {a}".strip() if a else ""]:
                if not q:
                    continue
                for sug in autocomplete(q)[:4]:
                    if sug not in [x["query"] for x in out["searches"]]:
                        words = [w for w in re.findall(r"[a-z]+", sug) if len(w) > 3 and w not in ("near", "best", "with")]
                        has = [m["url"] for m in page_meta if words and all(w in (m["title"] + " " + m["h1"] + " " + m["path"]).lower() for w in words)]
                        out["searches"].append({"query": sug, "page": has[0] if has else ""})
        missing = [s for s in out["searches"] if not s["page"]]
        if len(out["searches"]) >= 3 and len(missing) / len(out["searches"]) >= 0.5:
            add("seo_structure", "keyword_gaps", "high",
                f"No page targets {len(missing)} of {len(out['searches'])} searches people make for your service",
                "Google suggests these real searches: " + "; ".join(f"'{s['query']}'" for s in missing[:4])
                + ". No page on your site has them in its title, headline or address.",
                "Build a page per core service and service-area combination.",
                impact="These are searches your customers are typing right now. Without a matching page, competitors get those calls.")

    # ---- homepage targeting
    title_h1 = (hf.get("title", "") + " " + " ".join(hf.get("h1") or [])).lower()
    if areas and not any(a in title_h1 for a in areas + ["new york", "ny"]):
        add("seo_structure", "home_no_location", "medium", "Homepage title and headline don't say where you work",
            f"The site mentions {areas[0].title()}, but the homepage title (\"{hf.get('title', '')[:60]}\") and H1 don't name any area.",
            "Put the main service and area in the homepage title and H1.",
            impact="The title is the strongest signal Google uses to match your homepage to local searches.")
    if service and service.split()[-1] not in title_h1:
        add("seo_structure", "home_no_service", "medium", f"Homepage title and headline don't mention '{service}'",
            f"Neither the title (\"{hf.get('title', '')[:60]}\") nor the H1 contains the main service.",
            "Lead the title with the service people search for.")

    # ---- site size / service pages
    content_pages = [m for m in inner if not BLOGGY.search(m["path"]) and not UTILITY.search(m["path"])
                     and not re.search(r"/(about|contact|team|careers|faq|gallery|portfolio)", m["path"])]
    if out["page_count"] < 6:
        add("seo_structure", "too_few_pages", "high", f"Only {out['page_count']} page{'s' if out['page_count'] != 1 else ''} for Google to rank",
            f"We found {out['page_count']} pages in total (crawl + sitemap). Each service and area needs its own page to rank.",
            "Plan a page map: one page per service, one per area, plus FAQs and proof.",
            impact="A small site can only rank for a handful of searches, no matter how good the business is.")
    thin = [m["url"] for m in content_pages if m["words"] < 500]
    if content_pages and len(thin) >= max(2, len(content_pages) // 2):
        add("seo_structure", "thin_service_pages", "medium", f"{len(thin)} service pages are too short to rank",
            "These pages have under 500 words. Pages that rank for competitive local services usually cover the service, process, pricing, FAQs and proof.",
            "Write in-depth service pages.", thin)

    # ---- headings
    skips, no_h2 = [], []
    for (p, s), m in zip(ok, page_meta):
        lv = [int(h.name[1]) for h in s.find_all(re.compile(r"^h[1-6]$"))]
        if any(b - a > 1 for a, b in zip(lv, lv[1:])) or (lv and lv[0] > 2):
            skips.append(p.final_url)
        if m["words"] > 400 and 2 not in lv:
            no_h2.append(p.final_url)
    if len(skips) >= max(2, len(ok) // 3):
        add("seo_structure", "heading_hierarchy", "low", f"Heading structure is out of order on {len(skips)} pages",
            "Headings skip levels (for example H1 straight to H4), which is usually headings used for styling rather than structure.",
            "Use H1 > H2 > H3 in order.", skips)
    if no_h2:
        add("seo_structure", "no_subheadings", "low", f"{len(no_h2)} long page{'s have' if len(no_h2) != 1 else ' has'} no H2 subheadings",
            "Long pages without subheadings are harder for people to skim and for Google to understand.",
            "Break content into H2 sections that answer specific questions.", no_h2)

    # ---- duplicates and cannibalization
    sh = [(p.final_url, _shingles(_main_text(s))) for p, s in ok]
    dups = []
    for i in range(len(sh)):
        for j in range(i + 1, len(sh)):
            a, b = sh[i][1], sh[j][1]
            if len(a) > 80 and len(b) > 80 and len(a & b) / len(a | b) > 0.8:
                dups.append(f"{sh[i][0]} ≈ {sh[j][0]}")
    if dups:
        add("seo_structure", "near_duplicate_pages", "medium", f"{len(dups)} pair{'s' if len(dups) != 1 else ''} of near-identical pages",
            "These pages share over 80% of their text. Google usually shows only one of them and may ignore the rest.",
            "Rewrite with unique content per page.", dups)
    seen = {}
    for m in page_meta:
        key = re.sub(r"[^a-z0-9 ]", "", (m["h1"] or "").lower()).strip()
        if key and len(key) > 4:
            seen.setdefault(key, []).append(m["url"])
    cann = {k: v for k, v in seen.items() if len(v) > 1}
    if cann:
        k, v = next(iter(cann.items()))
        add("seo_structure", "cannibalization", "medium", f"{sum(len(v) for v in cann.values())} pages compete for the same headline",
            f"Several pages use the same H1 (e.g. \"{k[:50]}\" on {len(v)} pages), so they compete with each other for the same search.",
            "Give every page one distinct keyword focus.", [u for v in cann.values() for u in v])

    # ---- internal linking
    linked, generic = set(), 0
    for p, s in ok:
        for a in s.find_all("a", href=True):
            href = a["href"].split("#")[0]
            if href:
                from urllib.parse import urljoin
                linked.add(urljoin(p.final_url, href).rstrip("/").lower())
            if a.get_text(" ", strip=True).lower() in GENERIC_ANCHORS:
                generic += 1
    orphans = [u for u in extras.get("sitemap_urls", [])
               if u.rstrip("/").lower() not in linked and not BLOGGY.search(urlparse(u).path) and not UTILITY.search(urlparse(u).path)]
    if len(orphans) >= 3:
        add("seo_structure", "orphan_pages", "medium", f"{len(orphans)} pages aren't linked from the rest of the site",
            "These pages are listed in the sitemap but nothing on the pages we checked links to them, so they get little ranking value.",
            "Link every service and area page from the menu, footer or related pages.", orphans)
    if generic >= 5:
        add("seo_structure", "generic_anchors", "low", f"{generic} links say 'read more' or 'click here'",
            "Link text tells Google what the target page is about; generic text wastes that signal.",
            "Use descriptive link text such as 'emergency plumbing in Queens'.")
    home_links = {u for u in (urljoin_all(home_p.final_url, home)) if urlparse(u).netloc.lower() == urlparse(home_p.final_url).netloc.lower()}
    if len(home_links) < 6:
        add("seo_structure", "weak_home_linking", "low", f"The homepage links to only {len(home_links)} other pages",
            "The homepage passes the most ranking value; linking it to few pages leaves service pages weak.",
            "Link the homepage to every core service and area page.")

    # ---- URLs and schema
    ugly = [m["url"] for m in page_meta if re.search(r"[?&](p|page_id|id)=\d+", m["url"]) or "_" in m["path"]
            or re.search(r"[A-Z]", urlparse(m["url"]).path) or len(m["path"]) > 90]
    if ugly:
        add("seo_structure", "ugly_urls", "low", f"{len(ugly)} page address{'es aren' if len(ugly) != 1 else ' isn'}'t search-friendly",
            "Addresses with IDs, underscores, capitals or excessive length say nothing about the page to Google or visitors.",
            "Use short, lowercase, hyphenated slugs like /service-area/.", ugly)
    types = {t.lower() for f in facts for t in f.get("jsonld", [])}
    if len(ok) > 3 and "breadcrumblist" not in types:
        add("seo_structure", "no_breadcrumbs", "low", "No breadcrumb data",
            "Breadcrumb schema shows the page path in Google results and helps it understand site structure.",
            "Add BreadcrumbList schema to inner pages.")
    if service and "service" not in types and not any("service" in t for t in types):
        add("seo_structure", "no_service_schema", "low", "No Service schema",
            "Structured data describing each service helps Google and AI search match you to service queries.",
            "Add Service schema to each service page.")
    return out


def urljoin_all(base: str, soup) -> set:
    from urllib.parse import urljoin
    return {urljoin(base, a["href"]).split("#")[0].rstrip("/") for a in soup.find_all("a", href=True)
            if not a["href"].startswith(("mailto:", "tel:", "#", "javascript:"))} - {base.rstrip("/")}
