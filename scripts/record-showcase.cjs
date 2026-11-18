// Records a smooth 60fps scrolling walkthrough of each demo site and a cover image.
// Frames are captured one by one at exact scroll positions (no screen recording), so the
// scroll never stutters, then encoded with ffmpeg.
// Usage: node scripts/record-showcase.cjs [baseUrl] [slug]   (site server must be running)
// Output: public/showcase-media/<slug>.mp4 + <slug>.jpg  (requires ffmpeg)
const { chromium } = require('playwright')
const { execFileSync } = require('child_process')
const fs = require('fs')
const path = require('path')

const base = process.argv[2] || 'http://localhost:3000'
const only = process.argv[3]
const out = path.resolve(__dirname, '../public/showcase-media')
const FPS = 60
const W = 1440
const H = 900

// Each site: list of [targetFraction, seconds] moves, with optional pauses ([null, seconds]).
const SITES = {
  'northbridge-medical': [[null, 1.2], [0.22, 3.5], [null, 1], [1, 15], [null, 1.2], [0, 2.6], [null, 0.8]],
  'kestrel-row-realty': [[null, 1.2], [0.2, 3.2], [null, 1], [1, 15], [null, 1.2], [0, 2.6], [null, 0.8]],
  relaywave: [[null, 1.6], [0.14, 2.8], [null, 1.4], [1, 15], [null, 1.2], [0, 2.6], [null, 0.8]],
  'hearthside-home-care': [[null, 1.2], [1, 18], [null, 1.2], [0, 2.6], [null, 0.8]],
  'saltgrain-ceramics': [[null, 1.2], [0.18, 3], [null, 1], [1, 14], [null, 1.2], [0, 2.6], [null, 0.8]],
}

const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2)

;(async () => {
  const browser = await chromium.launch()
  for (const [slug, moves] of Object.entries(SITES)) {
    if (only && slug !== only) continue
    const url = `${base}/showcase/${slug}/index.html`
    const tmp = path.join(out, `.tmp-${slug}`)
    fs.rmSync(tmp, { recursive: true, force: true })
    fs.mkdirSync(tmp, { recursive: true })

    const ctx = await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: 1 })
    const page = await ctx.newPage()
    await page.goto(url, { waitUntil: 'networkidle' })
    await page.addStyleTag({ content: 'html{scroll-behavior:auto!important}' })
    // Show every scroll-reveal element and load lazy images before recording.
    await page.evaluate(async () => {
      for (let y = 0; y < document.documentElement.scrollHeight; y += 500) { scrollTo(0, y); await new Promise((r) => setTimeout(r, 60)) }
      document.querySelectorAll('[data-r]').forEach((e) => e.classList.add('in'))
      scrollTo(0, 0)
    })
    await page.waitForTimeout(1500)

    // Cover image at 1.5x.
    const shotCtx = await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: 1.5 })
    const sp = await shotCtx.newPage()
    await sp.goto(url, { waitUntil: 'networkidle' })
    await sp.evaluate(() => document.querySelectorAll('[data-r]').forEach((e) => e.classList.add('in')))
    await sp.waitForTimeout(1500)
    await sp.screenshot({ path: path.join(tmp, 'cover.png') })
    await shotCtx.close()

    // Slow CSS animations to roughly match capture speed, so motion keeps its real pace in the video.
    const cdp = await ctx.newCDPSession(page)
    await cdp.send('Animation.enable')
    const maxY = await page.evaluate(() => document.documentElement.scrollHeight - innerHeight)
    let y = 0
    let n = 0
    const t0 = Date.now()
    await cdp.send('Animation.setPlaybackRate', { playbackRate: 0.21 })
    for (const [frac, secs] of moves) {
      const frames = Math.round(secs * FPS)
      const from = y
      const to = frac === null ? y : Math.round(maxY * frac)
      for (let i = 1; i <= frames; i++) {
        y = from + (to - from) * ease(i / frames)
        await page.evaluate((yy) => scrollTo(0, yy), y)
        await page.screenshot({ path: path.join(tmp, `f${String(n++).padStart(5, '0')}.jpg`), type: 'jpeg', quality: 92 })
      }
    }
    await ctx.close()
    const mp4 = path.join(out, `${slug}.mp4`)
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(FPS), '-i', path.join(tmp, 'f%05d.jpg'), '-vf', 'scale=1280:-2:flags=lanczos', '-c:v', 'libx264', '-preset', 'slow', '-crf', '24', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an', mp4])
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', path.join(tmp, 'cover.png'), '-vf', 'scale=1600:-2', '-q:v', '4', path.join(out, `${slug}.jpg`)])
    fs.rmSync(tmp, { recursive: true, force: true })
    console.log('recorded', slug, n, 'frames in', ((Date.now() - t0) / 1000).toFixed(0) + 's,', (fs.statSync(mp4).size / 1e6).toFixed(1) + 'MB')
  }
  await browser.close()
})()
