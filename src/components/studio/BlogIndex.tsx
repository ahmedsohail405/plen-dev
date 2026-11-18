import Link from 'next/link'
import React from 'react'

import type { Category, Post } from '@/payload-types'
import { Breadcrumbs } from '@/heros/RenderHero'
import { Arrow } from '@/components/studio/Icon'
import { Hl } from '@/components/studio/Hl'

const fmt = (d?: string | null) =>
  d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : ''

/** Studio-styled blog listing used by /blog and /blog/page/N. */
export const BlogIndex: React.FC<{ posts: Post[]; page?: number; totalPages?: number }> = ({ posts, page = 1, totalPages = 1 }) => (
  <>
    <section className="hero-page">
      <div className="wrap">
        <Breadcrumbs crumbs={[{ name: 'Home', path: '/' }, { name: 'Blog', path: '/blog' }]} />
        <span className="eyebrow" data-reveal>Plen Dev blog</span>
        <h1 className="display" data-reveal style={{ ['--d' as string]: '80ms' }}>
          <Hl text="Notes on *better* websites" />
        </h1>
        <p className="hero-sub" data-reveal style={{ ['--d' as string]: '180ms', maxWidth: 720 }}>
          Plain-English guides on website costs, CMS choices and audits for New York businesses.
        </p>
      </div>
    </section>
    <section className="section section--tight" style={{ paddingTop: 0 }}>
      <div className="wrap">
        <div className="post-grid">
          {posts.map((p, i) => {
            const cats = (p.categories || []).filter((c): c is Category => typeof c === 'object' && c !== null)
            return (
              <Link key={p.id} href={`/blog/${p.slug}`} className="post-card" data-reveal style={{ ['--d' as string]: `${i * 70}ms` }}>
                <span className="post-meta">
                  {cats[0]?.title || 'Guide'}
                  {p.publishedAt ? ` · ${fmt(p.publishedAt)}` : ''}
                </span>
                <h2 className="h3">{p.title}</h2>
                {p.meta?.description && <p>{p.meta.description}</p>}
                <span className="post-more">
                  Read article <Arrow />
                </span>
              </Link>
            )
          })}
        </div>
        {totalPages > 1 && (
          <nav className="btn-row" style={{ marginTop: 40 }} aria-label="Blog pages">
            {page > 1 && <Link className="btn btn--ghost" href={page === 2 ? '/blog' : `/blog/page/${page - 1}`}>Newer posts</Link>}
            {page < totalPages && <Link className="btn btn--ghost" href={`/blog/page/${page + 1}`}>Older posts</Link>}
          </nav>
        )}
      </div>
    </section>
  </>
)
