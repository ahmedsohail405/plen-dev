import type { MetadataRoute } from 'next'
import configPromise from '@payload-config'
import { getPayload } from 'payload'

import { SITE } from '@/lib/schema'

export const revalidate = 3600

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const payload = await getPayload({ config: configPromise })
  const base = SITE()
  const where = { _status: { equals: 'published' } } as const
  const [pages, posts, projects] = await Promise.all([
    payload.find({ collection: 'pages', where, limit: 1000, pagination: false, depth: 0, select: { path: true, slug: true, updatedAt: true, meta: true } }),
    payload.find({ collection: 'posts', where, limit: 1000, pagination: false, depth: 0, select: { slug: true, updatedAt: true, meta: true } }),
    payload.find({ collection: 'projects', where, limit: 1000, pagination: false, depth: 0, select: { slug: true, updatedAt: true } }),
  ])
  const noindex = (d: { meta?: unknown }) => Boolean((d.meta as { noindex?: boolean } | undefined)?.noindex)

  const priority = (path: string) =>
    path === '/' ? 1 : /^\/(packages|website-audit|services|locations)/.test(path) ? 0.9 : /^\/industries/.test(path) ? 0.8 : 0.6

  return [
    ...pages.docs
      .filter((p) => !noindex(p))
      .map((p) => {
        const path = p.slug === 'home' ? '/' : p.path || `/${p.slug}`
        return { url: base + (path === '/' ? '' : path), lastModified: p.updatedAt, changeFrequency: 'weekly' as const, priority: priority(path) }
      }),
    { url: `${base}/blog`, changeFrequency: 'weekly', priority: 0.6 },
    ...posts.docs.filter((p) => !noindex(p)).map((p) => ({ url: `${base}/blog/${p.slug}`, lastModified: p.updatedAt, priority: 0.6 })),
    ...projects.docs.map((p) => ({ url: `${base}/work/${p.slug}`, lastModified: p.updatedAt, priority: 0.7 })),
  ]
}
