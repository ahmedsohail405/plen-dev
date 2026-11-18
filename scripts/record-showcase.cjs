// Records a ~25s scrolling walkthrough of each demo site and a homepage cover image.
// Usage: node scripts/record-showcase.cjs [baseUrl]   (dev server must be running)
// Output: public/showcase-media/<slug>.mp4 + <slug>.jpg  (requires ffmpeg)
const { chromium } = require('playwright')
const { execFileSync } = require('child_process')
const fs = require('fs')
const path = require('path')

const base = process.argv[2] || 'http://localhost:3000'
const out = path.resolve(__dirname, '../public/showcase-media')
const tmp = path.join(out, '.tmp')
fs.mkdirSync(tmp, { recursive: true })

const SITES = {
  'lumen-pine-dental': async (p, s) => { await s(0.22, 3500); await p.click('.slots span:nth-child(4)').catch(() => {}); await p.waitForTimeout(500); await s(1, 14000) },
  'kestrel-row-realty': async (p, s) => { await s(0.18, 3000); await p.hover('.lst:nth-child(2)').catch(() => {}); await p.waitForTimeout(900); await s(1, 15000) },
  relaywave: async (p, s) => { await p.waitForTimeout(800); await s(0.12, 2500); await p.waitForTimeout(1200); await s(1, 16000) },
  'hearthside-home-care': async (p, s) => { await s(1, 18000) },
  'saltgrain-ceramics': async (p, s) => {
    await s(0.17, 3000)
    await p.hover('.prod:nth-child(3)').catch(() => {}); await p.waitForTimeout(700)
    await p.click('.prod:nth-child(3) .add').catch(() => {}); await p.waitForTimeout(2200)
    await p.click('#scrim').catch(() => {}); await p.waitForTimeout(700)
    await s(1, 12000)
  },
}

;(async () => {
  const browser = await chromium.launch()
  for (const [slug, script] of Object.entries(SITES)) {
    const url = `${base}/showcase/${slug}/index.html`
    // cover image
    const shotCtx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1.5 })
    const sp = await shotCtx.newPage()
    await sp.goto(url, { waitUntil: 'networkidle' })
    await sp.evaluate(() => document.querySelectorAll('[data-r]').forEach((e) => e.classList.add('in')))
    await sp.waitForTimeout(1500)
    await sp.screenshot({ path: path.join(tmp, `${slug}.png`) })
    await shotCtx.close()

    // video
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, recordVideo: { dir: tmp, size: { width: 1440, height: 900 } } })
    const page = await ctx.newPage()
    await page.goto(url, { waitUntil: 'networkidle' })
    await page.waitForTimeout(1600)
    // smooth scroll to a fraction of the page over ms
    const scrollTo = (frac, ms) =>
      page.evaluate(
        ({ frac, ms }) =>
          new Promise((res) => {
            const start = scrollY, end = (document.documentElement.scrollHeight - innerHeight) * frac, t0 = performance.now()
            const ease = (t) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2)
            const step = (now) => { const t = Math.min(1, (now - t0) / ms); scrollTo(0, start + (end - start) * ease(t)); t < 1 ? requestAnimationFrame(step) : res() }
            requestAnimationFrame(step)
          }),
        { frac, ms },
      )
    await script(page, scrollTo)
    await page.waitForTimeout(1200)
    await scrollTo(0, 2500)
    await page.waitForTimeout(1500)
    const video = page.video()
    await ctx.close()
    const webm = await video.path()
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', webm, '-ss', '0.8', '-vf', 'scale=1280:-2,fps=30', '-c:v', 'libx264', '-preset', 'slow', '-crf', '27', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an', path.join(out, `${slug}.mp4`)])
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', path.join(tmp, `${slug}.png`), '-vf', 'scale=1600:-2', '-q:v', '4', path.join(out, `${slug}.jpg`)])
    console.log('recorded', slug, (fs.statSync(path.join(out, `${slug}.mp4`)).size / 1e6).toFixed(1) + 'MB')
  }
  await browser.close()
  fs.rmSync(tmp, { recursive: true, force: true })
})()
