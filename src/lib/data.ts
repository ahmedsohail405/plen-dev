import configPromise from '@payload-config'
import { getPayload } from 'payload'
import { unstable_cache } from 'next/cache'
import { draftMode } from 'next/headers'
import { cache } from 'react'

import type { Package, Project, SiteSetting } from '@/payload-types'
import { getCachedGlobal } from '@/utilities/getGlobals'

export const getSettings = (): Promise<SiteSetting> => getCachedGlobal('site-settings', 1)()

export const getPackages = unstable_cache(
  async (): Promise<Package[]> => {
    const payload = await getPayload({ config: configPromise })
    const res = await payload.find({ collection: 'packages', limit: 200, sort: 'order', depth: 0 })
    return res.docs
  },
  ['packages'],
  { tags: ['packages'] },
)

export const publishedProjects = unstable_cache(
  async (): Promise<Project[]> => {
    const payload = await getPayload({ config: configPromise })
    const res = await payload.find({ collection: 'projects', limit: 100, sort: 'order', depth: 1, draft: false, where: { _status: { equals: 'published' } } })
    return res.docs
  },
  ['projects'],
  { tags: ['projects'] },
)

export const getProjects = cache(async (): Promise<Project[]> => {
  const { isEnabled } = await draftMode()
  if (!isEnabled) return publishedProjects()
  const payload = await getPayload({ config: configPromise })
  const res = await payload.find({ collection: 'projects', limit: 100, sort: 'order', depth: 1, draft: true, overrideAccess: true })
  return res.docs
})

export const mediaUrl = (m: unknown): string | null => {
  if (m && typeof m === 'object' && 'url' in m && typeof (m as { url?: string }).url === 'string') return (m as { url: string }).url
  return null
}
