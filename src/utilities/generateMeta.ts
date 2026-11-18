import type { Metadata } from 'next'

import type { Media, Page, Post, Config } from '../payload-types'

import { getSettings } from '@/lib/data'
import { mergeOpenGraph } from './mergeOpenGraph'
import { getServerSideURL } from './getURL'

const getImageURL = (image?: Media | Config['db']['defaultIDType'] | null, fallback?: unknown) => {
  const serverUrl = getServerSideURL()
  const img = image && typeof image === 'object' ? image : fallback && typeof fallback === 'object' ? (fallback as Media) : null
  if (img && 'url' in img && img.url) return serverUrl + (img.sizes?.og?.url || img.url)
  return serverUrl + '/og.png'
}

type Doc = (Partial<Page> | Partial<Post>) & { meta?: (Page['meta'] & { canonical?: string | null; noindex?: boolean | null; keywords?: string | null }) | null }

export const generateMeta = async (args: { doc: Doc | null; path?: string }): Promise<Metadata> => {
  const { doc, path } = args
  const s = await getSettings()
  const suffix = s.titleSuffix ?? ' | Plen Dev'
  const base = doc?.meta?.title || doc?.title || s.businessName
  // Don't double-append the brand if the editor already typed it.
  const title = base.includes(s.businessName) ? base : base + suffix
  const description = doc?.meta?.description || s.defaultDescription || undefined
  const url = path ?? ((doc as Page | null)?.path || '/')
  const canonical = doc?.meta?.canonical || url

  return {
    title: { absolute: title },
    description,
    alternates: { canonical },
    robots: doc?.meta?.noindex ? { index: false, follow: true } : undefined,
    openGraph: mergeOpenGraph({
      description: description || '',
      images: [{ url: getImageURL(doc?.meta?.image, s.defaultOgImage) }],
      title,
      url: canonical,
    }),
  }
}
