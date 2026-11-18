"""Deep checks: security, conversion & trust, design/technology age, accessibility (ADA).

All checks are passive: they only read pages the crawler already fetched, their response
headers, and the public TLS certificate. Nothing probes for hidden files or tries logins,
so they are safe to run on sites that did not ask for an audit.

Each check calls add(category, id, severity, title, detail, fix, pages, impact=...).
`detail` = what we found, `impact` = what it costs the business (client-facing),
`fix` = internal note for Plen Dev (not shown to clients, since we sell rebuilds).
"""
from __future__ import annotations

import re
import socket
import ssl
from datetime import datetime, timezone
from urllib.parse import urlparse

from bs4 import BeautifulSoup

NOW_YEAR = datetime.now().year


def _ver(s: str) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", s)[:3])


def ssl_days_left(host: str, port: int = 443) -> int | None:
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as s:
                exp = datetime.strptime(s.getpeercert()["notAfter"], "%b %d %H:%M:%S %Y %Z")
        return (exp.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)).days
    except Exception:  # noqa: BLE001  (network blocked, self-signed etc.: handled elsewhere)
        return None


def run(pages, facts, psi, add) -> None:
    html_pages = [p for p in pages if p.html and p.status == 200]
    if not html_pages:
        return
    home_pg = html_pages[0]
    home = BeautifulSoup(home_pg.html, "lxml")
    soups = [(p.final_url, BeautifulSoup(p.html, "lxml")) for p in html_pages]
    all_html = "\n".join(p.html for p in html_pages).lower()
    home_l = home_pg.html.lower()
    hdr = {k.lower(): v for k, v in home_pg.headers.items()}
    https = home_pg.final_url.startswith("https://")
    host = urlparse(home_pg.final_url).hostname or ""

    # ================================================================ SECURITY
    if https:
        if "strict-transport-security" not in hdr:
            add("security", "no_hsts", "medium", "No HSTS header",
                "The site doesn't force browsers to always use the secure connection.",
                "Add Strict-Transport-Security: max-age=31536000; includeSubDomains.",
                impact="Visitors on public Wi-Fi can be silently downgraded to an insecure connection.")
        days = ssl_days_left(host)
        if days is not None and days < 30:
            add("security", "ssl_expiring", "critical" if days < 14 else "high",
                f"SSL certificate {'has expired' if days < 0 else f'expires in {days} days'}",
                "When it lapses, every browser shows a full-page security warning.",
                "Enable automatic certificate renewal.",
                impact="An expired certificate blocks almost every visitor and every form submission.")
    if "content-security-policy" not in hdr:
        add("security", "no_csp", "medium", "No Content Security Policy",
            "Nothing limits which scripts can run on the site.",
            "Add a Content-Security-Policy header.",
            impact="If a plugin or ad script is compromised, it can inject spam, redirects or card skimmers.")
    csp = hdr.get("content-security-policy", "")
    if "x-frame-options" not in hdr and "frame-ancestors" not in csp:
        add("security", "no_clickjack_protection", "medium", "No clickjacking protection",
            "Any other website can load this site inside a hidden frame.",
            "Add X-Frame-Options: SAMEORIGIN or CSP frame-ancestors.",
            impact="Attackers can trick visitors into clicking buttons on your site without knowing it.")
    if hdr.get("x-content-type-options", "").lower() != "nosniff":
        add("security", "no_xcto", "low", "Missing X-Content-Type-Options header",
            "Browsers may guess file types, which opens the door to some script attacks.",
            "Add X-Content-Type-Options: nosniff.", impact="A small but easy-to-close security gap.")
    leak = [f"{k}: {hdr[k]}" for k in ("server", "x-powered-by", "x-aspnet-version") if re.search(r"\d", hdr.get(k, ""))]
    if leak:
        add("security", "server_version_exposed", "low", "Server software versions are public",
            f"The server announces exactly what it runs ({'; '.join(leak)}).",
            "Hide version numbers in server config.",
            impact="Attackers use these version numbers to find known exploits for your server.")

    # Outdated CMS
    gen = home.find("meta", attrs={"name": re.compile("^generator$", re.I)})
    gen_s = (gen.get("content") or "") if gen else ""
    m = re.search(r"wordpress\s*([\d.]+)", gen_s, re.I) or re.search(r"wp-includes/[^\"']+\?ver=([\d.]+)", home_l)
    cms_note = None
    if m and _ver(m.group(1)) and _ver(m.group(1)) < (6, 5):
        cms_note = f"WordPress {m.group(1)}"
    elif re.search(r"joomla!?\s*[1-3]\.", gen_s, re.I):
        cms_note = gen_s
    elif re.search(r"drupal\s*[5-7]\b", gen_s, re.I):
        cms_note = gen_s
    if cms_note:
        add("security", "outdated_cms", "high", f"Outdated, publicly visible CMS version ({cms_note})",
            "The site runs an old content-management system version and advertises it in the page code.",
            "Upgrade core and plugins, remove the generator tag.",
            impact="Old CMS versions are the #1 way small-business sites get hacked and blacklisted by Google.")
    elif "wp-content/" in home_l and gen_s and re.search(r"wordpress\s*[\d.]+", gen_s, re.I):
        add("security", "outdated_cms", "low", "WordPress version is publicly visible",
            f"The page code announces '{gen_s}'.", "Remove the generator meta tag.",
            impact="Makes it easier for automated bots to target the site.")

    # Outdated JS libraries (versions with published vulnerabilities)
    libs = []
    srcs = " ".join(s.get("src", "") for s in home.find_all("script", src=True)).lower()
    jq = re.search(r"jquery(?:[-.]|\.min\.js\?ver=|/)(\d+\.\d+(?:\.\d+)?)", srcs) or \
        re.search(r"jquery\.min\.js\?ver=(\d+\.\d+(?:\.\d+)?)", home_l)
    if jq and _ver(jq.group(1)) < (3, 5):
        libs.append(f"jQuery {jq.group(1)}")
    bs = re.search(r"bootstrap(?:@|/|-)(\d+\.\d+(?:\.\d+)?)", srcs)
    if bs and _ver(bs.group(1)) < (3, 4, 1):
        libs.append(f"Bootstrap {bs.group(1)}")
    if re.search(r"angular(?:\.min)?\.js|angularjs/1\.", srcs):
        libs.append("AngularJS 1.x (end of life)")
    if libs:
        add("security", "outdated_js_libs", "high", f"Outdated JavaScript libraries: {', '.join(libs)}",
            "These versions have publicly known security vulnerabilities.",
            "Upgrade or remove the libraries.",
            impact="Known vulnerabilities in old libraries let attackers run code in your visitors' browsers.")

    # Forms that send data insecurely
    insecure_forms = []
    for url, s in soups:
        for f in s.find_all("form"):
            action = f.get("action") or ""
            if action.startswith("http://") or (not url.startswith("https") and f.find("input", attrs={"type": re.compile("email|password|tel", re.I)})):
                insecure_forms.append(url)
                break
    if insecure_forms:
        add("security", "form_posts_insecure", "critical", "Forms send customer data without encryption",
            "Contact or login forms submit over plain http://.",
            "Serve and submit every form over HTTPS.", insecure_forms,
            impact="Names, phone numbers and messages your customers type can be read by anyone on the network.")

    cookie = hdr.get("set-cookie", "")
    if https and cookie and ("secure" not in cookie.lower() or "httponly" not in cookie.lower()):
        add("security", "cookie_flags_insecure", "low", "Cookies set without Secure/HttpOnly flags",
            "Session cookies can be exposed to scripts or insecure connections.",
            "Set Secure, HttpOnly and SameSite on cookies.",
            impact="Raises the risk of session hijacking for logged-in users and admins.")

    # Privacy & compliance
    has_privacy = any(re.search(r"privacy", (a.get_text(" ") + " " + a.get("href", "")), re.I)
                      for _, s in soups for a in s.find_all("a", href=True))
    collects = any(fa["form"] for fa in facts)
    tracks = any(k in all_html for k in ("googletagmanager.com", "gtag(", "fbq(", "connect.facebook.net",
                                         "google-analytics.com", "clarity.ms", "hotjar"))
    if (collects or tracks) and not has_privacy:
        add("security", "no_privacy_policy", "medium", "No privacy policy",
            "The site collects visitor data (forms or tracking) without a privacy policy.",
            "Publish a privacy policy and link it in the footer and next to forms.",
            impact="Required by Google Ads, Meta ads and privacy laws, and its absence reduces trust.")
    consent_kw = ("cookiebot", "onetrust", "termly", "cookieyes", "iubenda", "osano", "cookie-law-info",
                  "complianz", "accept cookies", "cookie consent", "cookie notice", "we use cookies")
    if tracks and not any(k in all_html for k in consent_kw):
        add("security", "no_cookie_consent", "low", "Tracking runs with no cookie notice",
            "Analytics or ad pixels load without any cookie notice or consent option.",
            "Add a consent banner wired to Google Consent Mode.",
            impact="A growing legal risk under state privacy laws, and Google now limits ad data without consent.")

    # ================================================================ CONVERSION & TRUST
    review_kw = ("testimonial", "reviews", "what our clients say", "what our patients say", "rated",
                 "trustpilot", "elfsight", "birdeye", "podium", "yelp.com/biz", "google reviews",
                 "aggregaterating", "★★★★", "5-star", "5 star")
    if not any(k in all_html for k in review_kw):
        add("conversion", "no_reviews", "high", "No reviews or testimonials on the site",
            "We found no customer reviews, testimonials or review widgets on any page we checked.",
            "Embed Google reviews and add testimonials near every call to action.",
            impact="Most people read reviews before contacting a local business. Without them, many leave to check a competitor.")
    booking_kw = ("calendly", "acuityscheduling", "zocdoc", "squareup.com/appointments", "booksy", "vagaro",
                  "mindbody", "opentable", "resy.com", "setmore", "localmed", "nexhealth", "jane.app",
                  "simplybook", "book online", "book now", "schedule online", "book an appointment", "request appointment")
    if not any(k in all_html for k in booking_kw):
        add("conversion", "no_online_booking", "medium", "No way to book online",
            "Visitors can't pick a time or request an appointment directly on the site.",
            "Add an online booking or appointment-request flow.",
            impact="People searching at night or on weekends can't book, so they book with whoever lets them.")
    trust_kw = ("licensed", "insured", "certified", "accredited", "award", "bbb", "years of experience",
                "family-owned", "family owned", "board-certified", "guarantee", r"since 19", r"since 20")
    if not any(re.search(k, all_html) for k in trust_kw):
        add("conversion", "no_trust_badges", "low", "No trust signals",
            "No licenses, certifications, awards, guarantees or 'years in business' anywhere on the site.",
            "Add a trust bar under the hero.",
            impact="Trust signals near the top of the page measurably raise the number of visitors who call.")
    top = home.find("header") or home.find("nav")
    top_html = str(top).lower() if top else home_l[: max(3000, len(home_l) // 8)]
    if not (re.search(r'href=["\']tel:', top_html) or re.search(
            r"(book|schedule|get a quote|free (quote|consultation|estimate)|contact us|call now|request)", top_html)):
        add("conversion", "contact_not_above_fold", "medium", "No phone or 'book' button at the top of the page",
            "The header has no click-to-call number or booking button.",
            "Add a sticky header with phone and primary CTA.",
            impact="Visitors who are ready to act have to scroll and search, and many give up first.")
    long_forms = []
    for url, s in soups:
        for f in s.find_all("form"):
            n = [i for i in f.find_all(["input", "select", "textarea"])
                 if (i.get("type") or "text").lower() not in ("hidden", "submit", "button", "image", "reset")]
            if len(n) > 6:
                long_forms.append(url)
                break
    if long_forms:
        add("conversion", "form_too_long", "medium", "Lead forms ask for too much",
            "Some forms have more than 6 fields.", "Cut forms to name, phone/email and one question.", long_forms,
            impact="Every extra field lowers the number of people who finish the form.")
    chat_kw = ("tawk.to", "intercom", "drift.com", "livechatinc", "crisp.chat", "tidio", "hs-scripts.com",
               "zdassets", "podium", "birdeye", "olark", "smartsupp", "chatra", "whatsapp")
    if not any(k in all_html for k in chat_kw):
        add("conversion", "no_live_chat", "low", "No chat or text option",
            "Visitors can't message the business from the site.", "Add web chat or text-us.",
            impact="Many younger customers would rather text than call, and chat captures leads after hours.")
    h1 = (facts[0]["h1"][0] if facts and facts[0]["h1"] else "").strip()
    if h1 and (len(h1.split()) <= 2 or re.match(r"^(welcome|home|hello|about us)\b", h1, re.I)):
        add("conversion", "generic_headline", "medium", f"Homepage headline doesn't say what you do (\"{h1[:40]}\")",
            "The main headline is generic and doesn't name the service, the area or the benefit.",
            "Rewrite the hero headline: service + area + benefit.",
            impact="Visitors decide in about 5 seconds whether they're in the right place.")

    # ================================================================ DESIGN & TECHNOLOGY AGE
    years = [int(y) for y in re.findall(r"(?:©|&copy;|copyright)\s*(?:\d{4}\s*[-–]\s*)?(\d{4})", home_l)]
    if years and max(years) < NOW_YEAR - 1:
        add("design", "old_copyright_year", "medium", f"Footer still says © {max(years)}",
            "The copyright year hasn't been updated in years.", "Update the year (or render it dynamically).",
            impact="Visitors read an old date as a sign the business may be closed or the site is neglected.")
    legacy = []
    if home.find(["marquee", "blink"]):
        legacy.append("<marquee>")
    if home.find("font"):
        legacy.append("<font> tags")
    if home.find("center"):
        legacy.append("<center> tags")
    if home.find(["frameset", "frame"]):
        legacy.append("frames")
    if re.search(r"\.swf|shockwave-flash", home_l):
        legacy.append("Flash")
    if home.body and home.body.get("bgcolor"):
        legacy.append("1990s-style HTML attributes")
    if legacy:
        add("design", "legacy_tech", "high", f"Built with outdated web technology ({', '.join(legacy)})",
            "The page uses HTML features that were retired over a decade ago.",
            "Rebuild on modern HTML/CSS.",
            impact="The site looks dated, renders inconsistently on new devices, and can't be patched into a modern design.")
    tables = home.find_all("table")
    if tables and (any(t.find("table") for t in tables) or
                   sum(1 for t in tables if t.get("cellpadding") or t.get("bgcolor") or t.get("width")) >= 2):
        add("design", "table_layout", "high", "Page layout is built with tables",
            "The design uses HTML tables for layout, a technique from the early 2000s.",
            "Rebuild with CSS grid/flexbox.",
            impact="Table layouts can't adapt to phones, so the site can't be made mobile-friendly without a rebuild.")
    imgs = home.find_all("img")
    if len(imgs) >= 4 and not home.find("picture") and not any(i.get("srcset") for i in imgs):
        add("design", "no_responsive_images", "medium", "Images aren't sized for phones",
            "Every device downloads the same full-size images.",
            "Use srcset/sizes and responsive image components.",
            impact="Phones download far more data than they need, which makes the site slow on mobile.")
    if len(imgs) >= 5 and not re.search(r"\.(webp|avif)\b|image/webp|image/avif", home_l):
        add("design", "no_modern_images", "low", "No modern image formats",
            "Images use older JPG/PNG formats only.", "Serve WebP/AVIF.",
            impact="Modern formats are typically 25-50% smaller, so pages load noticeably faster.")
    ext_scripts = home.find_all("script", src=True)
    if len(ext_scripts) > 25:
        add("design", "too_many_scripts", "medium", f"{len(ext_scripts)} separate scripts load on the homepage",
            "The page pulls in a very large number of separate JavaScript files.",
            "Consolidate and defer scripts.",
            impact="Each script delays the page, and heavy pages lose visitors on mobile data.")
    builders = [n for k, n in (("elementor", "Elementor"), ("et_pb_", "Divi"), ("vc_row", "WPBakery"),
                               ("wpb_", "WPBakery"), ("fusion-builder", "Avada"), ("oxygen-", "Oxygen"))
                if k in home_l]
    if builders and (home_pg.bytes > 150_000 or len(ext_scripts) > 20):
        add("design", "page_builder_bloat", "medium", f"Heavy page-builder code ({builders[0]})",
            f"The site is built with {builders[0]}, which adds a lot of extra code to every page.",
            "Rebuild with lean, custom components.",
            impact="Page-builder sites are typically much slower and harder to rank than custom-built ones.")
    diy = [n for k, n in (("wix.com", "Wix"), ("static.wixstatic", "Wix"), ("squarespace", "Squarespace"),
                          ("weebly", "Weebly"), ("godaddy website builder", "GoDaddy Website Builder"),
                          ("img1.wsimg.com", "GoDaddy Website Builder"), ("jimdo", "Jimdo"))
           if k in home_l]
    if diy:
        add("design", "diy_builder", "low", f"Built on a DIY website builder ({diy[0]})",
            f"The site runs on {diy[0]}, with limited control over speed, code and SEO.",
            "Migrate to a custom site.",
            impact="DIY templates look like thousands of other sites and limit how fast and how well you can rank.")

    # ================================================================ ACCESSIBILITY (ADA)
    unlabeled = []
    for url, s in soups:
        ids = {l.get("for") for l in s.find_all("label") if l.get("for")}
        for i in s.find_all(["input", "select", "textarea"]):
            if (i.get("type") or "text").lower() in ("hidden", "submit", "button", "image", "reset"):
                continue
            if not (i.get("aria-label") or i.get("aria-labelledby") or (i.get("id") in ids) or i.find_parent("label")):
                unlabeled.append(url)
                break
    if unlabeled:
        add("accessibility", "inputs_no_labels", "high", "Form fields without labels",
            "Screen readers can't tell blind visitors what to type in some form fields.",
            "Add <label> elements to every field.", unlabeled,
            impact="Missing form labels are one of the most cited problems in ADA website lawsuits.")
    empty_links = []
    for url, s in soups:
        for a in s.find_all(["a", "button"]):
            txt = a.get_text(" ", strip=True)
            alt = " ".join((i.get("alt") or "") for i in a.find_all("img")).strip()
            if not (txt or alt or a.get("aria-label") or a.get("title") or a.get("aria-labelledby")):
                empty_links.append(url)
                break
    if empty_links:
        add("accessibility", "links_no_text", "medium", "Links and buttons with no readable name",
            "Icon-only links/buttons have no text a screen reader can announce.",
            "Add aria-labels to icon links and buttons.", empty_links,
            impact="Blind visitors hear 'link, link, button' and can't navigate, which is a common ADA complaint.")
    if not (home.find("main") or home.find(attrs={"role": "main"})):
        add("accessibility", "no_skip_or_landmarks", "low", "No page landmarks",
            "The page has no <main> region, so keyboard and screen-reader users can't skip to content.",
            "Use semantic header/nav/main/footer and a skip link.",
            impact="Makes the site hard to use with assistive technology.")
    vp = home.find("meta", attrs={"name": "viewport"})
    vpc = (vp.get("content") or "").replace(" ", "").lower() if vp else ""
    if "user-scalable=no" in vpc or "user-scalable=0" in vpc or re.search(r"maximum-scale=1(\.0)?(,|$)", vpc):
        add("accessibility", "zoom_disabled", "medium", "Zooming is disabled on phones",
            "The site blocks pinch-to-zoom.", "Remove user-scalable=no / maximum-scale=1.",
            impact="Visitors with low vision can't enlarge text. This fails accessibility guidelines.")
    if home.find(["video", "audio"], autoplay=True) and not home.find("video", muted=True):
        add("accessibility", "autoplay_media", "low", "Media plays sound automatically",
            "Audio or video starts playing on load.", "Don't autoplay with sound.",
            impact="Annoys visitors and interferes with screen readers.")
    a11y = ((psi or {}).get("mobile") or {}).get("scores", {}).get("accessibility")
    if a11y is not None and a11y < 85:
        add("accessibility", "psi_accessibility_low", "high" if a11y < 70 else "medium",
            f"Google accessibility score is {a11y}/100",
            "Google's Lighthouse test found multiple accessibility failures (contrast, labels, names).",
            "Fix Lighthouse accessibility audits.",
            impact="New York sees more website accessibility (ADA) lawsuits than almost any other state.")
