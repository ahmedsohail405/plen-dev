import configPromise from '@payload-config'
import { getPayload } from 'payload'

import type { Page } from '@/payload-types'
import { getPackages, getProjects, getSettings } from '@/lib/data'
import { SITE } from '@/lib/schema'

const plain = (t?: string | null) => (t || '').replace(/\*/g, '').trim()
const money = (n: number) => '$' + n.toLocaleString('en-US')
const GROUPS: Record<string, string> = { websites: 'Website packages', ecommerce: 'Ecommerce packages', 'cms-apps': 'Custom CMS & web app packages', care: 'Care plans (monthly)', addons: 'Add-ons' }

/** Pull readable text out of a page's blocks for llms-full.txt. */
const blockText = (page: Page) => {
  const out: string[] = []
  for (const b of page.layout || []) {
    const x = b as Record<string, unknown>
    if (x.heading) out.push(`### ${plain(x.heading as string)}`)
    if (x.intro) out.push(plain(x.intro as string))
    if (x.text && typeof x.text === 'string') out.push(plain(x.text))
    for (const it of (x.items as Record<string, string>[] | undefined) || []) {
      if (it.question) out.push(`Q: ${it.question}\nA: ${it.answer}`)
      else if (it.title) out.push(`- ${it.title}${it.text ? `: ${it.text}` : ''}`)
      else if (it.value && it.label) out.push(`- ${it.value} ${it.label}`)
    }
    for (const s of (x.steps as Record<string, string>[] | undefined) || []) out.push(`- ${s.title}: ${s.text || ''}`)
    for (const a of (x.areas as Record<string, string>[] | undefined) || []) out.push(`- ${a.name}${a.neighborhoods ? ` (${a.neighborhoods})` : ''}`)
  }
  return out.filter(Boolean).join('\n')
}

export async function buildLlms(full: boolean) {
  const base = SITE()
  const [s, pkgs, projects, payload] = await Promise.all([getSettings(), getPackages(), getProjects(), getPayload({ config: configPromise })])
  const pages = (
    await payload.find({ collection: 'pages', where: { _status: { equals: 'published' } }, limit: 500, pagination: false, depth: 0, sort: 'path' })
  ).docs.filter((p) => !(p.meta as { noindex?: boolean })?.noindex)
  const posts = (await payload.find({ collection: 'posts', where: { _status: { equals: 'published' } }, limit: 200, pagination: false, depth: 0 })).docs

  const url = (p: Page) => base + (p.slug === 'home' ? '/' : p.path || `/${p.slug}`)
  const desc = (p: Page) => plain(p.hero?.answer) || p.meta?.description || plain(p.hero?.subtitle) || ''
  const section = (title: string, list: Page[]) =>
    list.length ? `\n## ${title}\n\n${list.map((p) => `- [${p.title}](${url(p)})${desc(p) ? `: ${desc(p)}` : ''}`).join('\n')}\n` : ''

  const by = (prefix: string) => pages.filter((p) => (p.path || '').startsWith(prefix) && p.path !== prefix)
  const used = new Set([...by('/services/'), ...by('/locations/'), ...by('/industries/')].map((p) => p.id))
  const core = pages.filter((p) => !used.has(p.id))

  const lines: string[] = []
  lines.push(`# ${s.businessName}`)
  lines.push('')
  lines.push(`> ${plain(s.llmsIntro) || s.description || s.tagline || ''}`)
  lines.push('')
  const facts = [
    ...(s.llmsFacts || []).map((f) => f.fact),
    s.areasServed?.length ? `Areas served: ${s.areasServed.map((a) => a.area).join(', ')}` : '',
    s.email ? `Email: ${s.email}` : '',
    s.phone ? `Phone: ${s.phone}` : '',
    `Free website audit: ${base}/website-audit`,
  ].filter(Boolean)
  lines.push(...facts.map((f) => `- ${f}`))
  lines.push(section('Main pages', core))
  lines.push(section('Services', by('/services/')))
  lines.push(section('Locations', by('/locations/')))
  lines.push(section('Industries', by('/industries/')))

  if (pkgs.length) {
    lines.push(`\n## Packages and pricing (USD)\n\nFull details: ${base}/packages\n`)
    for (const g of Object.keys(GROUPS)) {
      const list = pkgs.filter((p) => p.group === g)
      if (!list.length) continue
      lines.push(`### ${GROUPS[g]}\n`)
      for (const p of list) {
        const price = p.price != null ? `${p.pricePrefix ? p.pricePrefix + ' ' : ''}${p.price === 0 ? 'Free' : money(p.price)}${p.billing === 'monthly' ? '/month' : p.billing === 'per-page' ? '/page' : ''}` : p.priceNote || 'Custom quote'
        const extra = full ? (p.features || []).map((f) => f.feature).join('; ') : [p.scope, p.tagline].filter(Boolean).join(', ')
        lines.push(`- ${p.name}: ${price}${extra ? ` (${extra})` : ''}`)
      }
      lines.push('')
    }
  }

  if (projects.length) {
    lines.push(`## Portfolio\n`)
    for (const p of projects) lines.push(`- [${p.title}](${base}/work/${p.slug}) (${p.industry}): ${p.summary}`)
  }
  if (posts.length) {
    lines.push(`\n## Articles\n`)
    for (const p of posts) lines.push(`- [${p.title}](${base}/blog/${p.slug})${p.meta?.description ? `: ${p.meta.description}` : ''}`)
  }

  if (full) {
    lines.push(`\n---\n\n# Page content\n`)
    for (const p of pages) {
      lines.push(`\n## ${plain(p.hero?.title) || p.title}\n\nURL: ${url(p)}\n`)
      if (p.hero?.subtitle) lines.push(plain(p.hero.subtitle))
      if (p.hero?.answer) lines.push(plain(p.hero.answer))
      const t = blockText(p)
      if (t) lines.push(t)
    }
  } else {
    lines.push(`\n## Optional\n\n- [Full text version for AI tools](${base}/llms-full.txt)\n- [Sitemap](${base}/sitemap.xml)`)
  }
  return lines.join('\n').replace(/\n{3,}/g, '\n\n') + '\n'
}
