import fs from 'fs'
import path from 'path'
import type { CollectionSlug, Payload, PayloadRequest } from 'payload'

import { PACKAGES, PAGES, POSTS, PROJECTS, type PageSeed } from './content'
import { mdToLexical } from './mdToLexical'

const ctx = { disableRevalidate: true }

/**
 * Seeds Plen Dev content. Safe to re-run: it clears pages, posts, projects and
 * packages (never leads or users) and recreates them.
 * Portfolio media is read from /public/showcase-media/<slug>.{jpg,mp4} if present.
 */
export const seed = async ({ payload, req }: { payload: Payload; req: PayloadRequest }): Promise<{ mediaErrors: string[] }> => {
  payload.logger.info('Seeding Plen Dev…')

  const clear: CollectionSlug[] = ['pages', 'posts', 'projects', 'packages', 'categories', 'search', 'redirects']
  for (const c of clear) {
    await payload.db.deleteMany({ collection: c, req, where: {} })
    if (payload.collections[c]?.config.versions) await payload.db.deleteVersions({ collection: c, req, where: {} })
  }
  // media: only remove portfolio media we created before
  await payload.delete({ collection: 'media', where: { alt: { like: '[showcase]' } }, req, context: ctx, overrideAccess: true })

  /* ---------- settings & navigation ---------- */
  await payload.updateGlobal({
    slug: 'site-settings',
    req,
    context: ctx,
    data: {
      businessName: 'Plen Dev',
      tagline: 'Web design & development studio in New York',
      description:
        'Plen Dev is a New York web design and development company. We design and build custom websites, ecommerce stores, custom CMS platforms and web apps for businesses in Brooklyn, Queens, New York City and Long Island. Every site includes the Plen CMS with live-preview editing, a lead inbox and SEO controls.',
      email: 'info@plendev.com',
      phone: '',
      address: { city: 'Brooklyn', region: 'NY', hideStreet: true },
      areasServed: ['Brooklyn', 'Queens', 'Manhattan', 'New York City', 'Long Island', 'Nassau County', 'Suffolk County'].map((area) => ({ area })),
      hours: 'Mo-Fr 09:00-18:00',
      titleSuffix: ' | Plen Dev',
      defaultDescription:
        'Plen Dev builds fast, creative websites with an easy custom CMS for businesses in Brooklyn, Queens, NYC and Long Island. Websites from $1,499.',
      allowAiCrawlers: true,
      llmsIntro:
        'Plen Dev is a web design and development studio in New York (Brooklyn, Queens, NYC and Long Island). It builds custom Next.js websites, online stores, custom CMS platforms and web apps, with fixed published prices starting at $1,499.',
      llmsFacts: [
        'Services: custom web development, website design, custom CMS development, ecommerce development, web apps and client portals, website maintenance (care plans).',
        'Plen Dev does not sell SEO or marketing retainers; every website includes on-page SEO, schema markup and AI-readable structure.',
        'Every website includes the Plen CMS: live-preview editing of text and images, a lead inbox, per-page SEO fields and site-wide or per-page header code snippets.',
        'Typical launch time: 2 weeks (5 pages) to 4–8 weeks (custom sites).',
        'Free website audits are available at /website-audit.',
      ].map((fact) => ({ fact })),
      integrations: { leadWebhookEnabled: true },
    },
  })

  /* ---------- packages ---------- */
  for (const p of PACKAGES) {
    await payload.create({
      collection: 'packages',
      req,
      context: ctx,
      data: { ...p, features: ((p as { features?: string[] }).features || []).map((feature) => ({ feature })) } as never,
    })
  }

  /* ---------- portfolio ---------- */
  const mediaDir = path.resolve(process.cwd(), 'public/showcase-media')
  const projectIds: Record<string, number | string> = {}
  const mediaErrors: string[] = []
  for (const pr of PROJECTS) {
    const upload = async (file: string, alt: string) => {
      try {
        // On disk locally; on Vercel public/ isn't in the function bundle, so fetch it from the site itself
        const full = path.join(mediaDir, file)
        let data: Buffer | undefined
        if (fs.existsSync(full)) data = fs.readFileSync(full)
        else {
          const base = process.env.NEXT_PUBLIC_SERVER_URL || (process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : '')
          if (!base) return undefined
          const res = await fetch(`${base}/showcase-media/${file}`)
          if (!res.ok) throw new Error(`fetch ${file}: ${res.status}`)
          data = Buffer.from(await res.arrayBuffer())
        }
        const mimetype = file.endsWith('.mp4') ? 'video/mp4' : 'image/jpeg'
        const doc = await payload.create({
          collection: 'media',
          req,
          context: ctx,
          data: { alt: `[showcase] ${alt}` },
          file: { data, mimetype, name: file, size: data.length },
        })
        return doc.id
      } catch (err) {
        // Don't let one media upload stop the whole content load
        payload.logger.error({ err, message: `Seed: could not upload ${file}` })
        mediaErrors.push(`${file}: ${err instanceof Error ? err.message : String(err)}`)
        return undefined
      }
    }
    const cover = await upload(`${pr.slug}.jpg`, `${pr.title} website homepage`)
    const video = await upload(`${pr.slug}.mp4`, `${pr.title} website walkthrough video`)
    const doc = await payload.create({
      collection: 'projects',
      req,
      context: ctx,
      data: {
        ...pr,
        featured: true,
        cover,
        video,
        liveUrl: `/showcase/${pr.slug}/`,
        services: pr.services.map((service) => ({ service })),
        meta: { title: `${pr.title}: ${pr.industry} Website Design`, description: pr.summary },
        _status: 'published',
      } as never,
    })
    projectIds[pr.slug] = doc.id
  }

  /* ---------- pages (parents first) ---------- */
  const ids: Record<string, number | string> = {}
  const pending = [...PAGES]
  let guard = 0
  while (pending.length && guard++ < 200) {
    const page = pending.shift() as PageSeed
    if (page.parent && !ids[page.parent]) {
      pending.push(page)
      continue
    }
    const hero = { ...page.hero }
    if (hero.type === 'studio') hero.showcase = Object.values(projectIds).slice(0, 5)
    const layout = page.layout.map((b) => {
      if (b.blockType === 'work' && Array.isArray(b.projects)) return { ...b, projects: (b.projects as string[]).map((s) => projectIds[s]).filter(Boolean) }
      return b
    })
    const doc = await payload.create({
      collection: 'pages',
      req,
      context: ctx,
      data: {
        title: page.title,
        slug: page.slug,
        parent: page.parent ? ids[page.parent] : undefined,
        hero,
        layout,
        meta: page.meta,
        _status: 'published',
      } as never,
    })
    ids[page.slug] = doc.id
  }

  /* ---------- blog ---------- */
  const cat = await payload.create({ collection: 'categories', req, context: ctx, data: { title: 'Web development', slug: 'web-development' } as never })
  for (const p of POSTS) {
    await payload.create({
      collection: 'posts',
      req,
      context: ctx,
      data: {
        title: p.title,
        slug: p.slug,
        content: mdToLexical(p.body),
        categories: [cat.id],
        meta: { title: p.title, description: p.description },
        publishedAt: new Date().toISOString(),
        _status: 'published',
      } as never,
    })
  }

  /* ---------- header & footer ---------- */
  const ref = (slug: string, label: string) => ({ link: { type: 'reference', label, reference: { relationTo: 'pages', value: ids[slug] } } })
  await payload.updateGlobal({
    slug: 'header',
    req,
    context: ctx,
    data: {
      navItems: [ref('services', 'Services'), ref('work', 'Work'), ref('packages', 'Packages'), ref('industries', 'Industries'), ref('about', 'About'), ref('contact', 'Contact')],
      cta: { label: 'Free website audit', href: '/website-audit' },
    } as never,
  })
  await payload.updateGlobal({
    slug: 'footer',
    req,
    context: ctx,
    data: {
      bigLine: "Let's build *something.*",
      columns: [
        {
          title: 'Services',
          links: [
            ['Web development', '/services/web-development'],
            ['Website design', '/services/web-design'],
            ['Custom CMS', '/services/custom-cms'],
            ['Ecommerce', '/services/ecommerce'],
            ['Web apps', '/services/web-apps'],
            ['Care plans', '/services/website-maintenance'],
          ].map(([label, href]) => ({ label, href })),
        },
        {
          title: 'Locations',
          links: [
            ['Brooklyn', '/locations/brooklyn'],
            ['Queens', '/locations/queens'],
            ['New York City', '/locations/new-york-city'],
            ['Long Island', '/locations/long-island'],
            ['Nassau County', '/locations/long-island/nassau-county'],
            ['Suffolk County', '/locations/long-island/suffolk-county'],
          ].map(([label, href]) => ({ label, href })),
        },
        {
          title: 'Studio',
          links: [
            ['Work', '/work'],
            ['Packages', '/packages'],
            ['Free website audit', '/website-audit'],
            ['Industries', '/industries'],
            ['Blog', '/blog'],
            ['About', '/about'],
            ['Contact', '/contact'],
          ].map(([label, href]) => ({ label, href })),
        },
      ],
    } as never,
  })

  payload.logger.info(`Seeded ${PAGES.length} pages, ${PACKAGES.length} packages, ${PROJECTS.length} projects, ${POSTS.length} posts.`)
  return { mediaErrors }
}
