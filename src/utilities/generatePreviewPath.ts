import { PreviewSearchParams } from '@/app/(frontend)/next/preview/route'
import { PayloadRequest, CollectionSlug } from 'payload'

const collectionPrefixMap: Partial<Record<CollectionSlug, string>> = {
  posts: '/blog',
  projects: '/work',
  pages: '',
}

type Props = {
  collection: keyof typeof collectionPrefixMap
  slug: string
  /** Full public path for nested pages, e.g. /locations/brooklyn */
  path?: string | null
  req: PayloadRequest
}

export const generatePreviewPath = ({ collection, slug, path }: Props) => {
  if (slug === undefined || slug === null) {
    return null
  }

  const target =
    collection === 'pages' && path
      ? path
      : collection === 'pages' && slug === 'home'
        ? '/'
        : `${collectionPrefixMap[collection]}/${encodeURIComponent(slug)}`

  const encodedParams = new URLSearchParams({
    path: target,
    previewSecret: process.env.PREVIEW_SECRET || '',
  } satisfies PreviewSearchParams)

  return `/next/preview?${encodedParams.toString()}`
}
