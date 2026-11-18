import type { Metadata } from 'next'
import React from 'react'

import { WorkBlock } from '@/blocks/studio'
import { RenderHero } from '@/heros/RenderHero'
import { RenderBlocks } from '@/blocks/RenderBlocks'
import { PageCode } from '@/components/studio/PageCode'
import { crumbsFor, queryPageByPath } from '@/lib/pages'
import { breadcrumbSchema, JsonLd } from '@/lib/schema'
import { generateMeta } from '@/utilities/generateMeta'

/**
 * /work is a CMS page (slug "work") with the portfolio grid always rendered
 * first, so editors control the header and anything below the grid.
 */
export default async function WorkIndex() {
  const page = await queryPageByPath('/work')
  const crumbs = page ? await crumbsFor(page) : [{ name: 'Home', path: '/' }, { name: 'Work', path: '/work' }]
  return (
    <article>
      <JsonLd data={breadcrumbSchema(crumbs)} />
      {page && <PageCode path="/work" docId={page.id} own={page.codeSnippets as never} />}
      <RenderHero {...(page?.hero || { type: 'page', title: 'Selected *work*' })} pageTitle={page?.title || 'Work'} crumbs={crumbs} />
      <WorkBlock source="all" style="grid" />
      {page && <RenderBlocks blocks={page.layout} />}
    </article>
  )
}

export async function generateMetadata(): Promise<Metadata> {
  const page = await queryPageByPath('/work')
  return generateMeta({ doc: page || { title: 'Web Design Portfolio' }, path: '/work' })
}
