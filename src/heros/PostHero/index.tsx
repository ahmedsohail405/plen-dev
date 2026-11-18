import React from 'react'

import type { Post } from '@/payload-types'

import { Breadcrumbs } from '@/heros/RenderHero'
import { formatAuthors } from '@/utilities/formatAuthors'
import { mediaUrl } from '@/lib/data'

/** Studio-styled blog post hero: breadcrumbs, category, title, date and optional cover image. */
export const PostHero: React.FC<{ post: Post }> = ({ post }) => {
  const { categories, heroImage, populatedAuthors, publishedAt, title } = post
  const cats = (categories || []).filter((c) => typeof c === 'object' && c !== null) as { title?: string }[]
  const authors = populatedAuthors && populatedAuthors.length ? formatAuthors(populatedAuthors) : ''
  const img = mediaUrl(heroImage)
  const date = publishedAt
    ? new Date(publishedAt).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
    : ''
  return (
    <section className="hero-page hero-post">
      <div className="wrap">
        <Breadcrumbs
          crumbs={[
            { name: 'Home', path: '/' },
            { name: 'Blog', path: '/blog' },
            { name: title, path: `/blog/${post.slug}` },
          ]}
        />
        <span className="eyebrow" data-reveal>
          {cats.map((c) => c.title).filter(Boolean).join(', ') || 'Guide'}
        </span>
        <h1 className="display" data-reveal style={{ ['--d' as string]: '80ms' }}>
          {title}
        </h1>
        <p className="post-meta" data-reveal style={{ ['--d' as string]: '160ms' }}>
          {[authors && `By ${authors}`, date && <time key="d" dateTime={publishedAt || undefined}>{date}</time>]
            .filter(Boolean)
            .map((x, i) => (
              <React.Fragment key={i}>
                {i > 0 && ' · '}
                {x}
              </React.Fragment>
            ))}
        </p>
        {img && (
          <div className="media" data-reveal style={{ ['--d' as string]: '220ms', marginTop: 30 }}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={img} alt={(heroImage as { alt?: string })?.alt || ''} />
          </div>
        )}
      </div>
    </section>
  )
}
