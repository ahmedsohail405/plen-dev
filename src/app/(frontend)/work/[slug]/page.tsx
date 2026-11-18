import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { draftMode } from 'next/headers'
import React from 'react'

import { LivePreviewListener } from '@/components/LivePreviewListener'
import { Arrow } from '@/components/studio/Icon'
import { Breadcrumbs } from '@/heros/RenderHero'
import { ProjectScreen } from '@/blocks/studio'
import { getProjects, mediaUrl, publishedProjects } from '@/lib/data'
import { breadcrumbSchema, JsonLd, orgId, SITE } from '@/lib/schema'
import { generateMeta } from '@/utilities/generateMeta'

type Args = { params: Promise<{ slug: string }> }

export async function generateStaticParams() {
  const list = await publishedProjects()
  return list.map((p) => ({ slug: p.slug as string }))
}

export default async function ProjectPage({ params }: Args) {
  const { slug } = await params
  const { isEnabled: draft } = await draftMode()
  const all = await getProjects()
  const idx = all.findIndex((p) => p.slug === slug)
  const p = all[idx]
  if (!p) notFound()
  const next = all[(idx + 1) % all.length]
  const crumbs = [
    { name: 'Home', path: '/' },
    { name: 'Work', path: '/work' },
    { name: p.title, path: `/work/${p.slug}` },
  ]
  const host = p.domain || ''
  const video = mediaUrl(p.video)

  return (
    <article style={{ ['--accent' as string]: p.accent || undefined }}>
      {draft && <LivePreviewListener />}
      <JsonLd
        data={{
          '@context': 'https://schema.org',
          '@type': 'CreativeWork',
          name: `${p.title} website`,
          about: p.industry,
          description: p.summary,
          url: `${SITE()}/work/${p.slug}`,
          creator: { '@id': orgId() },
          image: mediaUrl(p.cover) ? SITE() + mediaUrl(p.cover) : undefined,
          ...(video ? { video: { '@type': 'VideoObject', name: `${p.title} website walkthrough`, description: p.summary, contentUrl: SITE() + video, thumbnailUrl: mediaUrl(p.cover) ? SITE() + mediaUrl(p.cover) : undefined, uploadDate: p.createdAt } } : {}),
        }}
      />
      <JsonLd data={breadcrumbSchema(crumbs)} />
      <section className="case-hero">
        <div className="wrap">
          <Breadcrumbs crumbs={crumbs} />
          <span className="eyebrow" style={{ marginTop: 20 }}>
            {p.industry}
          </span>
          <h1 className="display">{p.title}</h1>
          <p className="hero-sub">{p.summary}</p>
          <div className="case-meta">
            <div>
              <span>Industry</span>
              {p.industry}
            </div>
            <div>
              <span>Location</span>
              {p.location || 'New York'}
            </div>
            <div>
              <span>Year</span>
              {p.year || new Date().getFullYear()}
            </div>
            <div>
              <span>Built with</span>
              Next.js + Plen CMS
            </div>
          </div>
        </div>
      </section>
      <section className="wrap">
        <div className="case-video" data-reveal>
          <div className="chrome">
            <i />
            <i />
            <i />
            <span>{host || p.title}</span>
          </div>
          <ProjectScreen project={p} eager />
        </div>
        {p.liveUrl && (
          <div className="btn-row" style={{ marginTop: 24 }}>
            <a className="btn" href={p.liveUrl} target="_blank" rel="noopener">
              Open the live site <Arrow />
            </a>
          </div>
        )}
      </section>
      {p.results && p.results.length > 0 && (
        <section className="section section--tight">
          <div className="wrap stats">
            {p.results.map((r, i) => (
              <div key={i} data-reveal style={{ ['--d' as string]: `${i * 80}ms` }}>
                <strong style={{ color: 'var(--accent)' }}>{r.value}</strong>
                <span>{r.label}</span>
              </div>
            ))}
          </div>
        </section>
      )}
      <section className="section">
        <div className="wrap case-cols">
          <div data-reveal>
            <span className="eyebrow">The brief</span>
            <p className="lead" style={{ marginTop: 18, color: 'var(--ink-3)' }}>
              {p.challenge}
            </p>
          </div>
          <div data-reveal style={{ ['--d' as string]: '120ms' }}>
            <span className="eyebrow">What we built</span>
            <p className="lead" style={{ marginTop: 18, color: 'var(--ink-3)' }}>
              {p.solution}
            </p>
            {p.services && p.services.length > 0 && (
              <div className="chips" style={{ marginTop: 24 }}>
                {p.services.map((s, i) => (
                  <span key={i}>{s.service}</span>
                ))}
              </div>
            )}
          </div>
        </div>
      </section>
      {next && next.id !== p.id && (
        <section className="section section--dark">
          <div className="wrap">
            <span className="eyebrow">Next project</span>
            <Link href={`/work/${next.slug}`} style={{ textDecoration: 'none' }}>
              <p className="display" style={{ fontSize: 'clamp(3rem, 10vw, 9rem)', margin: '20px 0 0' }}>
                {next.title} <span className="hl">→</span>
              </p>
            </Link>
          </div>
        </section>
      )}
    </article>
  )
}

export async function generateMetadata({ params }: Args): Promise<Metadata> {
  const { slug } = await params
  const p = (await getProjects()).find((x) => x.slug === slug)
  if (!p) return {}
  return generateMeta({
    doc: { title: `${p.title} — ${p.industry} website`, meta: { title: p.meta?.title || `${p.title}: ${p.industry} Website Design`, description: p.meta?.description || p.summary, image: p.cover as never } },
    path: `/work/${p.slug}`,
  })
}
