import type { Metadata } from 'next/types'

import configPromise from '@payload-config'
import { getPayload } from 'payload'
import React from 'react'
import PageClient from './page.client'
import { BlogIndex } from '@/components/studio/BlogIndex'
import type { Post } from '@/payload-types'

export const dynamic = 'force-static'
export const revalidate = 600

export default async function Page() {
  const payload = await getPayload({ config: configPromise })
  const posts = await payload.find({ collection: 'posts', depth: 1, limit: 12, overrideAccess: false, sort: '-publishedAt' })
  return (
    <>
      <PageClient />
      <BlogIndex posts={posts.docs as Post[]} page={posts.page} totalPages={posts.totalPages} />
    </>
  )
}

export function generateMetadata(): Metadata {
  return {
    title: 'Web Design & Development Blog | Plen Dev',
    description: 'Guides on website costs, custom CMS vs WordPress and website audits for New York businesses.',
    alternates: { canonical: '/blog' },
  }
}
