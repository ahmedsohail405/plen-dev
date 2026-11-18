import type { Metadata } from 'next'
import configPromise from '@payload-config'
import { draftMode } from 'next/headers'
import { getPayload } from 'payload'
import React from 'react'

import { RenderBlocks } from '@/blocks/RenderBlocks'
import { LivePreviewListener } from '@/components/LivePreviewListener'
import { PayloadRedirects } from '@/components/PayloadRedirects'
import { PageCode } from '@/components/studio/PageCode'
import { plain } from '@/components/studio/Hl'
import { RenderHero } from '@/heros/RenderHero'
import { crumbsFor, queryPageByPath } from '@/lib/pages'
import { breadcrumbSchema, JsonLd, orgId, SITE } from '@/lib/schema'
import { generateMeta } from '@/utilities/generateMeta'

export async function generateStaticParams() {
  const payload = await getPayload({ config: configPromise })
  const pages = await payload.find({ collection: 'pages', draft: false, limit: 1000, overrideAccess: false, pagination: false, select: { path: true, slug: true } })
  return pages.docs
    .filter((d) => d.slug !== 'home' && d.path && !['/work', '/blog', '/search'].includes(d.path as string))
    .map((d) => ({ slug: (d.path as string).split('/').filter(Boolean) }))
}

type Args = { params: Promise<{ slug?: string[] }> }

const toPath = (slug?: string[]) => (slug && slug.length ? '/' + slug.map(decodeURIComponent).join('/') : '/')

export default async function Page({ params }: Args) {
  const { isEnabled: draft } = await draftMode()
  const { slug } = await params
  const path = toPath(slug)
  const page = await queryPageByPath(path)

  if (!page) return <PayloadRedirects url={path} />

  const crumbs = await crumbsFor(page)
  const meta = page.meta as (typeof page.meta & { schemaType?: string | null; schemaJson?: string | null }) | undefined
  let custom: unknown = null
  try {
    custom = meta?.schemaJson ? JSON.parse(meta.schemaJson) : null
  } catch {
    custom = null
  }

  const webPage = {
    '@context': 'https://schema.org',
    '@type': meta?.schemaType || 'WebPage',
    '@id': `${SITE()}${path}#webpage`,
    url: `${SITE()}${path === '/' ? '' : path}`,
    name: meta?.title || page.title,
    headline: plain(page.hero?.title) || page.title,
    description: meta?.description || page.hero?.answer || undefined,
    isPartOf: { '@id': `${SITE()}/#website` },
    ...(meta?.schemaType === 'Service'
      ? { provider: { '@id': orgId() }, areaServed: ['Brooklyn', 'Queens', 'New York City', 'Long Island'], serviceType: page.title }
      : { about: { '@id': orgId() } }),
    dateModified: page.updatedAt,
  }

  return (
    <article>
      <PayloadRedirects disableNotFound url={path} />
      {draft && <LivePreviewListener />}
      <JsonLd data={webPage} />
      {crumbs.length > 1 && <JsonLd data={breadcrumbSchema(crumbs)} />}
      {custom ? <JsonLd data={custom} /> : null}
      <PageCode path={path} docId={page.id} own={page.codeSnippets as never} />
      <RenderHero {...page.hero} pageTitle={page.title} crumbs={crumbs} />
      <RenderBlocks blocks={page.layout} />
    </article>
  )
}

export async function generateMetadata({ params }: Args): Promise<Metadata> {
  const { slug } = await params
  const path = toPath(slug)
  const page = await queryPageByPath(path)
  return generateMeta({ doc: page, path })
}
