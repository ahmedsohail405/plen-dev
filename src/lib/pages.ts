import configPromise from '@payload-config'
import { draftMode } from 'next/headers'
import { getPayload } from 'payload'
import { cache } from 'react'

import type { Page } from '@/payload-types'

export const queryPageByPath = cache(async (path: string): Promise<Page | null> => {
  const { isEnabled: draft } = await draftMode()
  const payload = await getPayload({ config: configPromise })
  const res = await payload.find({
    collection: 'pages',
    draft,
    limit: 1,
    pagination: false,
    overrideAccess: draft,
    depth: 2,
    where: path === '/' ? { slug: { equals: 'home' } } : { path: { equals: path } },
  })
  return res.docs?.[0] || null
})

/** Breadcrumbs built from the parent chain. */
export const crumbsFor = async (page: Page): Promise<{ name: string; path: string }[]> => {
  const chain: { name: string; path: string }[] = []
  const payload = await getPayload({ config: configPromise })
  let cur: Page | null = page
  let guard = 0
  while (cur && guard++ < 6) {
    chain.unshift({ name: cur.title, path: cur.path || `/${cur.slug}` })
    const parent: Page['parent'] = cur.parent
    if (!parent) break
    cur = typeof parent === 'object' ? parent : await payload.findByID({ collection: 'pages', id: parent, depth: 0 }).catch(() => null)
  }
  return [{ name: 'Home', path: '/' }, ...chain.filter((c) => c.path !== '/')]
}
