import Link from 'next/link'
import React from 'react'

import type { Media, Page, Project } from '@/payload-types'
import { CMSLink } from '@/components/Link'
import { Arrow } from '@/components/studio/Icon'
import { Hl } from '@/components/studio/Hl'
import { mediaUrl, projectCover, projectVideo } from '@/lib/data'

type Props = Page['hero'] & { pageTitle?: string; crumbs?: { name: string; path: string }[] }

const HeroLinks: React.FC<{ links: Page['hero']['links'] }> = ({ links }) =>
  links && links.length ? (
    <div className="btn-row">
      {links.map(({ link }, i) => (
        <CMSLink key={i} {...link} appearance="inline" className={i === 0 ? 'btn' : 'btn btn--ghost'}>
          <Arrow />
        </CMSLink>
      ))}
    </div>
  ) : null

const positions = [
  { left: '0%', top: '8%', r: '-6deg', delay: '0s' },
  { left: '22%', top: '30%', r: '3deg', delay: '-2s' },
  { left: '46%', top: '2%', r: '-2deg', delay: '-4s' },
  { left: '66%', top: '28%', r: '5deg', delay: '-1s' },
  { left: '34%', top: '52%', r: '-4deg', delay: '-3s' },
]

const StudioHero: React.FC<Props> = (p) => {
  const showcase = (p.showcase || []).filter((x): x is Project => typeof x === 'object')
  return (
    <section className="hero-studio">
      <div className="blob" aria-hidden />
      <div className="wrap">
        {p.eyebrow && (
          <span className="eyebrow" data-reveal>
            {p.eyebrow}
          </span>
        )}
        <h1 className="display" data-reveal style={{ ['--d' as string]: '80ms' }}>
          <Hl text={p.title || p.pageTitle} />
        </h1>
        <div className="hero-grid">
          <div data-reveal style={{ ['--d' as string]: '200ms' }}>
            {p.subtitle && <p className="hero-sub">{p.subtitle}</p>}
            {p.answer && <p className="hero-answer">{p.answer}</p>}
            <HeroLinks links={p.links} />
          </div>
          {p.badges && p.badges.length > 0 && (
            <div className="hero-badges" data-reveal style={{ ['--d' as string]: '320ms' }}>
              {p.badges.map((b, i) => (
                <div key={i}>
                  <strong>{b.value}</strong>
                  <span>{b.label}</span>
                </div>
              ))}
            </div>
          )}
        </div>
        {showcase.length > 0 && (
          <div className="hero-reel" aria-label="Recent work">
            {showcase.slice(0, 5).map((proj, i) => {
              const pos = positions[i % positions.length]!
              const video = projectVideo(proj)
              const img = projectCover(proj)
              return (
                <Link
                  key={proj.id}
                  href={`/work/${proj.slug}`}
                  className="float-card"
                  style={{ left: pos.left, top: pos.top, ['--r' as string]: pos.r, ['--delay' as string]: pos.delay, zIndex: i % 2 ? 2 : 1 }}
                >
                  <div className="chrome">
                    <i />
                    <i />
                    <i />
                    <span>{proj.domain || proj.title}</span>
                  </div>
                  {video ? (
                    <video src={video} poster={img || undefined} autoPlay muted loop playsInline preload="none" aria-label={`${proj.title} website walkthrough`} />
                  ) : img ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={img} alt={`${proj.title} website`} loading="lazy" />
                  ) : null}
                  <span className="tag">{proj.industry}</span>
                </Link>
              )
            })}
          </div>
        )}
      </div>
    </section>
  )
}

export const Breadcrumbs: React.FC<{ crumbs?: { name: string; path: string }[] }> = ({ crumbs }) =>
  crumbs && crumbs.length > 1 ? (
    <nav aria-label="Breadcrumb">
      <ol className="crumbs">
        {crumbs.map((c, i) => (
          <li key={c.path}>{i < crumbs.length - 1 ? <Link href={c.path}>{c.name}</Link> : <span aria-current="page">{c.name}</span>}</li>
        ))}
      </ol>
    </nav>
  ) : null

const PageHero: React.FC<Props> = (p) => {
  const img = mediaUrl(p.media)
  return (
    <section className="hero-page">
      <div className="wrap">
        <Breadcrumbs crumbs={p.crumbs} />
        <div className="cols">
          <div>
            {p.eyebrow && (
              <span className="eyebrow" data-reveal>
                {p.eyebrow}
              </span>
            )}
            <h1 className="display" data-reveal style={{ ['--d' as string]: '80ms' }}>
              <Hl text={p.title || p.pageTitle} />
            </h1>
          </div>
          <div data-reveal style={{ ['--d' as string]: '180ms' }}>
            {img ? (
              <div className="media">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={img} alt={(p.media as Media)?.alt || ''} />
              </div>
            ) : null}
          </div>
        </div>
        <div data-reveal style={{ ['--d' as string]: '240ms', maxWidth: 760 }}>
          {p.subtitle && <p className="hero-sub">{p.subtitle}</p>}
          {p.answer && <p className="hero-answer">{p.answer}</p>}
          <HeroLinks links={p.links} />
        </div>
      </div>
    </section>
  )
}

export const RenderHero: React.FC<Props> = (props) => {
  if (!props?.type || props.type === 'none') return null
  if (props.type === 'studio') return <StudioHero {...props} />
  return <PageHero {...props} />
}
