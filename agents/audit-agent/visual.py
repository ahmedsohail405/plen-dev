"""Visual audit: loads the homepage in a real browser (headless Chromium) as a phone and as a desktop,
takes screenshots and measures what a visitor actually sees.

Everything reported here is measured, never guessed:
- layout: sideways scrolling, text too small to read on a phone, tap targets too small or too close,
  pop-ups covering the screen, headline / call-to-action / phone visible on the first screen
- images: broken, stretched, blurry (shown larger than the file), oversized files, old formats, stock photos
- speed: Largest Contentful Paint, layout shift, page weight and request count, measured on a simulated
  mid-range phone on a slow 4G connection (the throttling Google's mobile test uses)

Screenshots are annotated with numbered markers (Pillow) and saved next to the report.
Needs `pip install playwright pillow` and `playwright install --with-deps chromium`.
If the browser can't start, run() returns {"ok": False, "error": ...} and the audit continues without it.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import urlparse

MOBILE = {"viewport": {"width": 390, "height": 844}, "device_scale_factor": 2, "is_mobile": True, "has_touch": True,
          "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 "
                        "(KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1 PlenDevAudit/1.0"}
DESKTOP = {"viewport": {"width": 1366, "height": 860}, "device_scale_factor": 1,
           "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/131.0 Safari/537.36 PlenDevAudit/1.0"}
# Same throttling as Lighthouse's mobile preset: 150 ms RTT, 1.6 Mbps down, 750 kbps up, 4x slower CPU
SLOW_4G = {"offline": False, "latency": 150, "downloadThroughput": 1.6 * 1024 * 1024 / 8,
           "uploadThroughput": 750 * 1024 / 8}
LOAD_TIMEOUT_MS = int(os.environ.get("VISUAL_TIMEOUT_MS", "45000"))

STOCK_RE = re.compile(r"(shutterstock|istockphoto|istock[-_]|gettyimages|adobestock|stock\.adobe|depositphotos|"
                      r"dreamstime|123rf|bigstock|pexels|unsplash|pixabay|freepik|stocksy|envato)", re.I)
CTA_RE = r"\b(book|schedule|call|get (a |your )?(free )?(quote|estimate|started|consultation|appointment)|contact|request|" \
         r"appointment|consult|buy|shop|order|reserve|sign up|start|enroll|apply|donate|free (quote|estimate|consultation))\b"

MEASURE_JS = r"""
([ctaPattern, deviceW]) => {
  const CTA = new RegExp(ctaPattern, 'i');
  // What the visitor actually sees: the visual viewport. If the browser zoomed the page out to fit
  // something too wide, scale < 1 and everything on screen is that much smaller.
  const vv = window.visualViewport;
  const k = vv ? Math.min(1, vv.scale) : 1;
  const vw = vv ? vv.width : innerWidth, vh = vv ? vv.height : innerHeight;
  const vis = el => {
    const s = getComputedStyle(el);
    if (s.visibility === 'hidden' || s.display === 'none' || parseFloat(s.opacity) === 0) return false;
    const r = el.getBoundingClientRect();
    return r.width > 1 && r.height > 1;
  };
  const box = el => { const r = el.getBoundingClientRect();
    return [Math.round(r.left + scrollX), Math.round(r.top + scrollY), Math.round(r.width), Math.round(r.height)]; };
  const label = el => (el.innerText || el.value || el.getAttribute('aria-label') || el.getAttribute('title') || '')
    .trim().replace(/\s+/g, ' ').slice(0, 60);
  const out = {vw, vh, k, docW: document.documentElement.scrollWidth, docH: document.documentElement.scrollHeight};

  // sideways scrolling: the widest visible elements sticking out past the right edge
  out.wide = [];
  if (out.docW > deviceW + 4) {
    for (const el of document.body.querySelectorAll('*')) {
      const r = el.getBoundingClientRect();
      if (r.right > deviceW + 4 && r.width > 0 && r.height > 0 && vis(el)) out.wide.push({tag: el.tagName.toLowerCase(), box: box(el), right: Math.round(r.right)});
    }
    out.wide.sort((a, b) => b.right - a.right);
    out.wide = out.wide.slice(0, 5);
  }

  // text size: characters of visible text by font size
  let chars = 0, small = 0; const smallEls = [];
  for (const el of document.body.querySelectorAll('*')) {
    let own = '';
    for (const n of el.childNodes) if (n.nodeType === 3) own += n.textContent;
    own = own.replace(/\s+/g, ' ').trim();
    if (own.length < 3 || !vis(el)) continue;
    const fs = parseFloat(getComputedStyle(el).fontSize) * k;
    chars += own.length;
    if (fs < 12) { small += own.length; if (smallEls.length < 6 && own.length > 15) smallEls.push({box: box(el), size: fs, text: own.slice(0, 50)}); }
  }
  out.text = {chars, small_chars: small, small_els: smallEls};

  // tap targets
  const targets = [...document.querySelectorAll('a[href], button, input:not([type=hidden]), select, textarea, [role=button]')]
    .filter(vis).map(el => ({el, r: el.getBoundingClientRect()}));
  out.targets_total = targets.length;
  const tiny = [], crowded = [];
  for (const t of targets) {
    if (getComputedStyle(t.el).position === 'fixed') continue;
    const inline = t.el.tagName === 'A' && t.el.closest('p, li p, td') && t.r.height < 30;  // links inside sentences are exempt (WCAG)
    if (inline) continue;
    // a checkbox or radio with a clickable label is a big target in practice (WCAG exception)
    if (/^(checkbox|radio)$/i.test(t.el.type || '') && t.el.labels && t.el.labels.length) continue;
    const tw = t.r.width * k, th = t.r.height * k;
    if (tw < 24 || th < 24) { tiny.push({box: box(t.el), w: Math.round(tw), h: Math.round(th), text: label(t.el)}); continue; }
    if (th < 40) {
      for (const o of targets) {
        if (o === t || o.el.contains(t.el) || t.el.contains(o.el)) continue;
        const gapY = Math.max(o.r.top - t.r.bottom, t.r.top - o.r.bottom);
        const overlapX = Math.min(o.r.right, t.r.right) - Math.max(o.r.left, t.r.left);
        const gapX = Math.max(o.r.left - t.r.right, t.r.left - o.r.right);
        if ((gapY >= 0 && gapY * k < 4 && overlapX > 0) || (gapX >= 0 && gapX < 4 && Math.min(o.r.bottom, t.r.bottom) - Math.max(o.r.top, t.r.top) > 0)) {
          crowded.push({box: box(t.el), text: label(t.el)}); break;
        }
      }
    }
  }
  out.tiny_targets = tiny.slice(0, 40); out.tiny_count = tiny.length;
  out.crowded_targets = crowded.slice(0, 40); out.crowded_count = crowded.length;

  // first screen: headline, call to action, phone
  const h1 = [...document.querySelectorAll('h1')].find(vis);
  out.h1 = h1 ? {box: box(h1), size: parseFloat(getComputedStyle(h1).fontSize), text: label(h1)} : null;
  // A call to action must look like a button (filled or outlined), or be a tap-to-call link; a plain menu link doesn't count.
  const buttonish = el => { const s = getComputedStyle(el);
    const bg = s.backgroundColor, hasBg = bg && bg !== 'transparent' && !/rgba\(.*,\s*0\)$/.test(bg);
    return el.tagName === 'BUTTON' || el.getAttribute('role') === 'button' || hasBg || s.backgroundImage !== 'none' || parseFloat(s.borderTopWidth) >= 1; };
  const ctas = targets.filter(t => /^tel:/i.test(t.el.getAttribute('href') || '') || (CTA.test(label(t.el)) && buttonish(t.el)));
  const firstCta = ctas.find(t => t.r.top + scrollY < vh && t.r.top + scrollY >= 0);
  out.cta_first_screen = firstCta ? {box: box(firstCta.el), text: label(firstCta.el)} : null;
  out.cta_any = ctas.length ? {box: box(ctas[0].el), text: label(ctas[0].el)} : null;
  const tel = targets.find(t => /^tel:/i.test(t.el.getAttribute('href') || '') && t.r.top + scrollY < vh);
  out.tel_first_screen = !!tel;

  // pop-ups / bars covering the screen
  out.overlays = [];
  for (const el of document.body.querySelectorAll('*')) {
    const s = getComputedStyle(el);
    if (!(s.position === 'fixed' || s.position === 'sticky') || !vis(el)) continue;
    const r = el.getBoundingClientRect();
    const w = Math.max(0, Math.min(r.right, vw) - Math.max(r.left, 0)), h = Math.max(0, Math.min(r.bottom, vh) - Math.max(r.top, 0));
    const share = (w * h) / (vw * vh);
    if (share >= 0.25) out.overlays.push({box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], share: Math.round(share * 100), text: label(el)});
  }
  out.overlays = out.overlays.sort((a, b) => b.share - a.share).slice(0, 3);

  // images
  out.images = [...document.images].map(img => {
    const r = img.getBoundingClientRect(), s = getComputedStyle(img);
    return {src: img.currentSrc || img.src || '', nw: img.naturalWidth, nh: img.naturalHeight, w: Math.round(r.width), h: Math.round(r.height),
            box: box(img), complete: img.complete, fit: s.objectFit, loading: img.getAttribute('loading') || '',
            visible: vis(img), alt: img.getAttribute('alt')};
  }).filter(i => i.src && !i.src.startsWith('data:'));
  return out;
}
"""

PERF_JS = r"""
() => new Promise(resolve => {
  const res = {lcp: null, cls: 0};
  try { new PerformanceObserver(l => { for (const e of l.getEntries()) res.lcp = e.startTime; })
          .observe({type: 'largest-contentful-paint', buffered: true}); } catch (e) {}
  try { new PerformanceObserver(l => { for (const e of l.getEntries()) if (!e.hadRecentInput) res.cls += e.value; })
          .observe({type: 'layout-shift', buffered: true}); } catch (e) {}
  const nav = performance.getEntriesByType('navigation')[0];
  if (nav) { res.ttfb = nav.responseStart; res.dcl = nav.domContentLoadedEventEnd; res.load = nav.loadEventEnd; }
  setTimeout(() => resolve(res), 300);
})
"""


def _launch(p):
    exe = os.environ.get("CHROMIUM_PATH") or None
    return p.chromium.launch(executable_path=exe, args=["--no-sandbox", "--disable-dev-shm-usage"])


def _scroll_through(page):
    """Scroll to the bottom and back so lazy-loaded images and late layout show up, like a real visitor."""
    page.evaluate("""async () => { const step = innerHeight * 0.8;
        for (let y = 0; y < Math.min(document.body.scrollHeight, 20000); y += step) { scrollTo(0, y); await new Promise(r => setTimeout(r, 120)); }
        scrollTo(0, 0); }""")
    page.wait_for_timeout(900)


def _visit(browser, url: str, device: dict, throttle: bool, out: Path, name: str) -> dict:
    ctx = browser.new_context(**device, ignore_https_errors=True, locale="en-US")
    page = ctx.new_page()
    net, reqs = {}, {}
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)[:160]))
    # Bytes actually transferred, from Chrome's own network log (Content-Length is often missing)
    cdp = ctx.new_cdp_session(page)
    cdp.send("Network.enable")

    def on_resp(e):
        r = e["response"]
        reqs[e["requestId"]] = r["url"]
        net[r["url"]] = {"status": r["status"], "type": (r.get("mimeType") or "").lower(), "bytes": 0}

    def on_done(e):
        u = reqs.get(e["requestId"])
        if u in net:
            net[u]["bytes"] = int(e.get("encodedDataLength") or 0)

    cdp.on("Network.responseReceived", on_resp)
    cdp.on("Network.loadingFinished", on_done)
    if throttle:
        cdp.send("Network.emulateNetworkConditions", SLOW_4G)
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
    res = {"device": name, "timed_out": False}
    try:
        page.goto(url, wait_until="load", timeout=LOAD_TIMEOUT_MS)
    except Exception as e:  # noqa: BLE001 - a slow page is a finding, not a crash
        if "Timeout" not in type(e).__name__ and "Timeout" not in str(e):
            ctx.close()
            raise
        res["timed_out"] = True
    page.wait_for_timeout(2500)
    res["perf"] = page.evaluate(PERF_JS)
    res["load_bytes"], res["load_requests"] = sum(n["bytes"] for n in net.values()), len(net)  # before any scrolling
    if throttle:  # measure layout with full speed so scrolling doesn't take minutes
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
        cdp.send("Network.emulateNetworkConditions", {"offline": False, "latency": 0, "downloadThroughput": -1, "uploadThroughput": -1})
    shot = out / f"shot-{name}.jpg"
    page.screenshot(path=str(shot), type="jpeg", quality=72)  # first screen, exactly as a visitor lands
    res["shot"] = shot.name
    _scroll_through(page)
    res["m"] = page.evaluate(MEASURE_JS, [CTA_RE, device["viewport"]["width"]])
    res["errors"] = errors[:5]
    res["final_url"] = page.url
    # sizes of resources that didn't send Content-Length (compressed responses)
    res["net"] = net
    res["_page"], res["_ctx"] = page, ctx
    return res


def _clip(page, box, out: Path, fname: str, pad: int = 90) -> str | None:
    x, y, w, h = box
    vw = page.viewport_size["width"]
    top = max(0, y - pad)
    height = min(max(h + 2 * pad, 260), 900)
    try:
        page.screenshot(path=str(out / fname), type="jpeg", quality=72, full_page=True,
                        clip={"x": 0, "y": top, "width": vw, "height": height})
        return fname
    except Exception:  # noqa: BLE001
        return None


def run(url: str, out: Path) -> dict:
    """Load the page as a phone (throttled) and a desktop. Returns measurements + screenshot names."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"ok": False, "error": "playwright not installed"}
    out.mkdir(parents=True, exist_ok=True)
    result = {"ok": False}
    try:
        with sync_playwright() as p:
            browser = _launch(p)
            try:
                mob = _visit(browser, url, MOBILE, True, out, "mobile")
                result["mobile"] = _summarize(mob)
                # close-up shots of problems below the first screen (phone only, max 3)
                clips = []
                for kind, item in (_below_fold_targets(result["mobile"]) if result["mobile"]["k"] >= 0.99 else []):
                    if len(clips) >= 3:
                        break
                    f = _clip(mob["_page"], item["box"], out, f"clip-{len(clips) + 1}.jpg")
                    if f:
                        top = max(0, item["box"][1] - 90)
                        clips.append({"kind": kind, "file": f, "offset_y": top})
                result["mobile"]["clips"] = clips
                mob["_ctx"].close()
                desk = _visit(browser, url, DESKTOP, False, out, "desktop")
                result["desktop"] = _summarize(desk)
                desk["_ctx"].close()
                result["ok"] = True
            finally:
                browser.close()
    except Exception as e:  # noqa: BLE001 - the rest of the audit must still run
        result["error"] = f"{type(e).__name__}: {str(e)[:200]}"
    return result


def _summarize(v: dict) -> dict:
    m, net = v["m"], v["net"]
    imgs = []
    for i in m["images"]:
        info = net.get(i["src"], {})
        imgs.append(i | {"bytes": info.get("bytes", 0), "ctype": info.get("type", "")})
    total = sum(n["bytes"] for n in net.values())
    img_bytes = sum(n["bytes"] for n in net.values() if n["type"].startswith("image/"))
    return {"shot": v["shot"], "timed_out": v["timed_out"], "perf": v["perf"], "errors": v["errors"],
            "vw": m["vw"], "vh": m["vh"], "k": m["k"], "doc_w": m["docW"], "doc_h": m["docH"], "wide": m["wide"],
            "text": m["text"], "tiny_targets": m["tiny_targets"], "tiny_count": m["tiny_count"],
            "crowded_targets": m["crowded_targets"], "crowded_count": m["crowded_count"],
            "targets_total": m["targets_total"], "h1": m["h1"], "cta_first_screen": m["cta_first_screen"],
            "cta_any": m["cta_any"], "tel_first_screen": m["tel_first_screen"], "overlays": m["overlays"],
            "images": imgs, "requests": v["load_requests"], "bytes": v["load_bytes"], "image_bytes": img_bytes,
            "bytes_after_scroll": total,
            "host": urlparse(v["final_url"]).netloc}


def _below_fold_targets(mv: dict):
    vh = mv["vh"]
    for w in mv["wide"][:1]:
        if w["box"][1] > vh:
            yield "wide", w
    for t in mv["tiny_targets"]:
        if t["box"][1] > vh:
            yield "tiny", t
            break
    for s in mv["text"]["small_els"]:
        if s["box"][1] > vh:
            yield "small_text", s
            break


# --------------------------------------------------------------------------- image analysis

def image_problems(mv: dict, dpr: int = 2) -> dict:
    """Classify images from one device's measurements. Only flags what the numbers prove."""
    broken, stretched, blurry, oversized, heavy, old_fmt, stock, no_lazy = [], [], [], [], [], [], [], []
    for i in mv["images"]:
        src = i["src"]
        if i["complete"] and i["nw"] == 0:
            broken.append(i)
            continue
        if not i["visible"] or i["w"] < 40 or i["h"] < 40 or not i["nw"]:
            continue
        ext = urlparse(src).path.lower().rsplit(".", 1)[-1] if "." in urlparse(src).path else ""
        is_svg = ext == "svg" or "svg" in i["ctype"]
        if is_svg:
            continue
        nat_ratio, ren_ratio = i["nw"] / max(i["nh"], 1), i["w"] / max(i["h"], 1)
        if i["fit"] in ("fill", "") and abs(nat_ratio - ren_ratio) / nat_ratio > 0.08 and i["w"] >= 80:
            stretched.append(i)
        if i["w"] >= 200 and i["nw"] < i["w"] * 0.9:  # shown bigger than the file itself, even on a 1x screen
            blurry.append(i)
        if i["nw"] > i["w"] * dpr * 2 and i["nw"] >= 1200:
            oversized.append(i)
        if i["bytes"] > 300_000:
            heavy.append(i)
        if (i["ctype"] in ("image/jpeg", "image/png") or ext in ("jpg", "jpeg", "png")) and i["bytes"] > 60_000:
            old_fmt.append(i)
        if STOCK_RE.search(src):
            stock.append(i)
        if i["box"][1] > mv["vh"] * 1.5 and i["loading"] != "lazy" and "lazy" not in src:
            no_lazy.append(i)
    return {"broken": broken, "stretched": stretched, "blurry": blurry, "oversized": oversized, "heavy": heavy,
            "old_format": old_fmt, "stock": stock, "no_lazy": no_lazy}


# --------------------------------------------------------------------------- annotation

COLORS = ["#e11d48", "#f59e0b", "#7c3aed", "#0891b2", "#16a34a", "#db2777", "#ea580c", "#2563eb"]


def annotate(out: Path, shot: str, marks: list[dict], dpr: int, offset_y: int = 0, dest: str | None = None,
             scale: float = 1.0) -> str | None:
    """Draw numbered boxes on a screenshot. marks: [{"n": 1, "box": [x, y, w, h]}] in CSS pixels, page coordinates."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None
    src = out / shot
    if not src.exists():
        return None
    im = Image.open(src).convert("RGB")
    d = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 15 * dpr)
    except OSError:
        font = ImageFont.load_default()
    W, H = im.size
    for mk in marks:
        x, y, w, h = mk["box"]
        y -= offset_y
        c = dpr * scale  # page px -> screenshot px (scale < 1 when the browser zoomed the page out)
        x0, y0 = max(0, x * c), max(0, y * c)
        x1, y1 = min(W - 1, (x + w) * c), min(H - 1, (y + h) * c)
        if x1 <= x0 or y1 <= y0 or y0 >= H:
            continue
        col = COLORS[(mk["n"] - 1) % len(COLORS)]
        d.rectangle([x0, y0, x1, y1], outline=col, width=3 * dpr)
        r = 13 * dpr
        cx, cy = min(max(x0 + r, r), W - r), max(y0 - r // 2, r)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col, outline="white", width=2 * dpr)
        t = str(mk["n"])
        tw = d.textlength(t, font=font)
        d.text((cx - tw / 2, cy - 9 * dpr), t, fill="white", font=font)
    name = dest or shot.replace(".jpg", "-marked.jpg")
    im.save(out / name, "JPEG", quality=74, optimize=True)
    return name


# --------------------------------------------------------------------------- findings

def _kb(n: int) -> str:
    return f"{n / 1_000_000:.1f} MB" if n >= 1_000_000 else f"{round(n / 1000)} KB"


def findings(v: dict, out: Path, add) -> dict:
    """Turn measurements into findings. Each visual finding gets a numbered marker on a screenshot.
    Returns {"mobile": marked-shot, "desktop": marked-shot, "clips": [...], "legend": [...]} for the report."""
    if not v.get("ok"):
        return {}
    mob, desk = v["mobile"], v["desktop"]
    marks = {"mobile": [], "desktop": []}
    clip_marks = {c["file"]: [] for c in mob.get("clips", [])}
    legend = []
    n = 0

    def mark(device: str, box, text: str, fid: str):
        """Put a marker on the first-screen shot if the box is on it, otherwise on a close-up if we have one."""
        nonlocal n
        if not box:
            return None
        dv = mob if device == "mobile" else desk
        n += 1
        if box[1] < dv["vh"]:
            marks[device].append({"n": n, "box": box})
            where = "phone" if device == "mobile" else "desktop"
        else:
            where = None
            for c in mob.get("clips", []) if device == "mobile" else []:
                if c["offset_y"] <= box[1] <= c["offset_y"] + 900:
                    clip_marks[c["file"]].append({"n": n, "box": box})
                    where = "close-up"
                    break
            if not where:
                n -= 1
                return None
        legend.append({"n": n, "text": text, "id": fid, "where": where})
        return {"marker": n, "where": where}

    # ---- mobile layout
    if mob["doc_w"] > 394:
        w = mob["wide"][0] if mob["wide"] else None
        ev = mark("mobile", w and w["box"], "Content wider than the phone screen", "mobile_overflow")
        add("mobile", "mobile_overflow", "high", "Page doesn't fit on a phone screen",
            f"On a 390px-wide phone the page is {mob['doc_w']}px wide, so it either scrolls sideways or the browser "
            "shrinks the whole page to fit, making everything smaller.",
            "Rebuild layout with a mobile-first grid.", evidence=ev,
            impact="Sideways scrolling is one of the clearest signs of a broken mobile site; most visitors leave.")
    t = mob["text"]
    if t["chars"] > 400 and t["small_chars"] / t["chars"] > 0.15:
        pct = round(100 * t["small_chars"] / t["chars"])
        s = t["small_els"][0] if t["small_els"] else None
        ev = mark("mobile", s and s["box"], "Text smaller than 12px", "small_text_mobile")
        add("mobile", "small_text_mobile", "medium" if pct < 35 else "high", f"{pct}% of the text is too small to read on a phone",
            f"{pct}% of the visible text renders below 12px on a phone (Google recommends 16px for body text).",
            "Set a 16px base font with a fluid type scale.", evidence=ev,
            impact="Visitors have to pinch and zoom to read, and most won't.")
    if mob["tiny_count"] >= 3:
        tt = mob["tiny_targets"][0]
        ev = mark("mobile", tt["box"], f"Tap target {tt['w']}x{tt['h']}px", "tap_targets_small")
        add("mobile", "tap_targets_small", "medium" if mob["tiny_count"] < 10 else "high",
            f"{mob['tiny_count']} buttons or links are too small to tap",
            f"{mob['tiny_count']} tappable elements are smaller than 24x24px, the minimum in the accessibility standard (WCAG 2.2).",
            "Make every tap target at least 44x44px.", evidence=ev,
            impact="People tap the wrong thing or give up, especially on menus and phone links.")
    if mob["crowded_count"] >= 4:
        ct = mob["crowded_targets"][0]
        ev = mark("mobile", ct["box"], "Links packed too close together", "tap_targets_crowded")
        add("mobile", "tap_targets_crowded", "low", f"{mob['crowded_count']} links are packed too close together",
            "These links sit less than 4px from the next one, so a thumb easily hits the wrong one.",
            "Space tap targets at least 8px apart.", evidence=ev)
    if mob["overlays"]:
        o = mob["overlays"][0]
        ev = mark("mobile", o["box"], f"Pop-up or bar covering {o['share']}% of the screen", "mobile_overlay")
        add("mobile", "mobile_overlay", "high" if o["share"] >= 50 else "medium",
            f"A pop-up or bar covers {o['share']}% of the phone screen",
            f"Shortly after the page loads, a fixed element covers {o['share']}% of the first screen"
            + (f" (\"{o['text'][:40]}\")" if o["text"] else "") + ".",
            "Replace with an inline or small, dismissible element.", evidence=ev,
            impact="Google demotes pages with intrusive pop-ups on mobile, and visitors close the tab.")
    if not mob["cta_first_screen"]:
        ev = None
        add("conversion", "no_cta_first_screen_mobile", "high", "No call or booking button on the first phone screen",
            "When the page opens on a phone, there's no tap-to-call, 'book' or 'get a quote' button in view"
            + (f"; the first one is {round(mob['cta_any']['box'][1] / mob['vh'], 1)} screens down." if mob["cta_any"] else "."),
            "Put a sticky call/book button in the mobile header.", evidence=ev,
            impact="Most local searches happen on phones; if the next step isn't visible, visitors bounce.")
    if mob["h1"] and mob["h1"]["box"][1] > mob["vh"]:
        add("mobile", "headline_below_fold_mobile", "medium", "The main headline is below the first phone screen",
            f"The H1 headline starts {mob['h1']['box'][1]}px down, past the {mob['vh']}px screen.",
            "Lead with the headline and value proposition.",
            impact="Visitors decide in a few seconds; if they can't see what you do, they leave.")
    if not desk["cta_first_screen"]:
        add("conversion", "no_cta_first_screen_desktop", "medium", "No call or booking button on the first desktop screen",
            "Nothing like 'call', 'book' or 'get a quote' is visible before scrolling on a laptop screen.",
            "Add a primary call-to-action button in the hero.")
    if desk["doc_w"] > desk["vw"] + 4:
        add("design", "desktop_overflow", "medium", "Page scrolls sideways on a laptop",
            f"At 1366px wide the page is {desk['doc_w']}px wide.", "Fix the layout container.")
    errs = (mob["errors"] or []) + (desk["errors"] or [])
    if errs:
        add("technical", "js_errors", "medium" if len(errs) >= 3 else "low", f"{len(errs)} JavaScript error{'s' if len(errs) != 1 else ''} on load",
            "The browser reported script errors while loading the homepage: " + "; ".join(e[:80] for e in errs[:2]),
            "Fix or remove broken scripts.",
            impact="Broken scripts can silently break forms, menus and tracking.")

    # ---- images (desktop measurements show the largest renders; mobile shows lazy-loading)
    ip = image_problems(desk, dpr=1)
    ipm = image_problems(mob, dpr=2)
    if ip["broken"] or ipm["broken"]:
        b = list({i["src"]: i for i in ip["broken"] + ipm["broken"]}.values())
        add("design", "broken_images", "high", f"{len(b)} broken image{'s' if len(b) != 1 else ''}",
            "These images fail to load and show as empty boxes or broken icons.", "Replace or remove them.",
            [i["src"] for i in b], impact="Broken images make a business look closed or careless.")
    if ip["stretched"]:
        i = ip["stretched"][0]
        ev = mark("desktop", i["box"], "Stretched image", "stretched_images")
        add("design", "stretched_images", "medium", f"{len(ip['stretched'])} stretched or squashed image{'s' if len(ip['stretched']) != 1 else ''}",
            f"Shown at a different shape than the photo (e.g. {i['nw']}x{i['nh']} file shown at {i['w']}x{i['h']}).",
            "Use object-fit or crop images properly.", [x["src"] for x in ip["stretched"]], evidence=ev,
            impact="Distorted photos look amateur and undermine trust in the work you do.")
    if ip["blurry"]:
        i = ip["blurry"][0]
        ev = mark("desktop", i["box"], "Low-resolution image shown too large", "blurry_images")
        add("design", "blurry_images", "medium", f"{len(ip['blurry'])} image{'s' if len(ip['blurry']) != 1 else ''} will look blurry",
            f"The file is smaller than the space it fills (e.g. {i['nw']}px wide shown at {i['w']}px), so it's stretched and soft, worse on high-resolution screens.",
            "Use high-resolution responsive images.", [x["src"] for x in ip["blurry"]], evidence=ev)
    big = {i["src"]: i for i in ip["heavy"] + ipm["heavy"]}
    if big:
        tot = sum(i["bytes"] for i in big.values())
        add("performance", "heavy_images", "high" if tot > 1_500_000 else "medium",
            f"{len(big)} oversized image file{'s' if len(big) != 1 else ''} ({_kb(tot)})",
            f"{len(big)} images are over 300 KB each, {_kb(tot)} in total, on the homepage alone.",
            "Compress and serve responsive WebP/AVIF.", list(big),
            impact="Big images are the most common reason a page loads slowly on a phone.")
    elif ip["oversized"]:
        add("performance", "oversized_images", "low", f"{len(ip['oversized'])} image{'s are' if len(ip['oversized']) != 1 else ' is'} far larger than displayed",
            "Images are downloaded at more than twice the size they're shown.", "Serve resized images.",
            [x["src"] for x in ip["oversized"]])
    old = {i["src"]: i for i in ip["old_format"] + ipm["old_format"]}
    if len(old) >= 3:
        add("performance", "old_image_formats", "low", f"{len(old)} images use old JPEG/PNG formats",
            "Modern WebP/AVIF files are typically 25-50% smaller for the same quality.", "Convert images to WebP/AVIF.",
            list(old))
    if ipm["no_lazy"] and len(ipm["no_lazy"]) >= 4:
        add("performance", "no_lazy_loading", "low", f"{len(ipm['no_lazy'])} images below the fold load immediately",
            "Images far down the page are downloaded before the visitor scrolls to them.", "Add loading=lazy.",
            [x["src"] for x in ipm["no_lazy"]])
    st = {i["src"]: i for i in ip["stock"] + ipm["stock"]}
    if st:
        i = next(iter(st.values()))
        ev = mark("desktop", i["box"], "Stock photo", "stock_photos") if i in ip["stock"] else None
        add("design", "stock_photos", "medium" if len(st) >= 2 else "low", f"{len(st)} stock photo{'s' if len(st) != 1 else ''}",
            "These images come from stock photo libraries (their file names or hosts say so), so the same photos appear on other businesses' sites.",
            "Use real photos of the team, work and location.", list(st), evidence=ev,
            impact="Visitors recognise stock photos; real photos of your team and work build trust and get more calls.")

    # ---- measured speed (phone, slow 4G)
    pf = mob["perf"] or {}
    lcp = pf.get("lcp")
    if mob["timed_out"]:
        add("performance", "page_load_timeout", "critical", "The homepage didn't finish loading in 45 seconds on a phone",
            "On a mid-range phone with a slow 4G connection, the page was still loading after 45 seconds.",
            "Rebuild on a lean, fast stack.", impact="Over half of mobile visitors leave a page that takes more than 3 seconds.")
    elif lcp:
        s = lcp / 1000
        if s > 4:
            add("performance", "lcp_measured", "high", f"Main content takes {s:.1f}s to appear on a phone",
                f"Largest Contentful Paint measured at {s:.1f}s on a mid-range phone with slow 4G (Google's 'good' is under 2.5s).",
                "Rebuild with optimized images, fonts and fewer scripts.",
                impact="Over half of mobile visitors leave a page that takes more than 3 seconds to show anything useful.")
        elif s > 2.5:
            add("performance", "lcp_measured", "medium", f"Main content takes {s:.1f}s to appear on a phone",
                f"Largest Contentful Paint measured at {s:.1f}s on a mid-range phone with slow 4G (Google's 'good' is under 2.5s).",
                "Optimize the hero image and render-blocking resources.",
                impact="Each extra second of load time costs a share of the visitors who would have called.")
    cls = pf.get("cls") or 0
    if cls > 0.1:
        add("performance", "cls_measured", "high" if cls > 0.25 else "medium", "The page jumps around while it loads",
            f"Layout shift measured at {cls:.2f} on a phone (Google's 'good' is under 0.1).", "Reserve space for images, fonts and embeds.",
            impact="Visitors tap the wrong thing when content moves under their finger.")
    if mob["bytes"] > 2_500_000:
        add("performance", "page_weight", "high" if mob["bytes"] > 5_000_000 else "medium", f"The homepage downloads {_kb(mob['bytes'])} on a phone",
            f"{mob['requests']} files, {_kb(mob['bytes'])} in total ({_kb(mob['image_bytes'])} of images). A fast page is usually under 1.5 MB.",
            "Cut page weight: compress images, drop unused scripts and plugins.",
            impact="Heavy pages are slow on mobile data and cost visitors money on limited plans.")
    elif mob["requests"] > 120:
        add("performance", "too_many_requests", "medium", f"The homepage makes {mob['requests']} separate requests",
            "Every file is a separate trip to the server, which slows mobile loading.", "Bundle and remove unused assets.")

    # ---- annotate
    res = {"legend": legend, "clips": []}
    res["mobile"] = annotate(out, mob["shot"], marks["mobile"], 2, scale=mob["k"]) or mob["shot"]
    res["desktop"] = annotate(out, desk["shot"], marks["desktop"], 1) or desk["shot"]
    for c in mob.get("clips", []):
        if clip_marks.get(c["file"]):
            res["clips"].append({"file": annotate(out, c["file"], clip_marks[c["file"]], 2, c["offset_y"]) or c["file"],
                                 "marks": [m["n"] for m in clip_marks[c["file"]]]})
    res["measured"] = {"lcp_s": round(lcp / 1000, 1) if lcp else None, "cls": round(cls, 2),
                       "bytes": mob["bytes"], "requests": mob["requests"], "timed_out": mob["timed_out"]}
    return res
