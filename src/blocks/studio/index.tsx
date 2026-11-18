import Link from 'next/link'
import React from 'react'

import type { Package, Project } from '@/payload-types'
import { CMSLink } from '@/components/Link'
import { Hl } from '@/components/studio/Hl'
import { Arrow, Icon } from '@/components/studio/Icon'
import { SectionHead } from '@/components/studio/SectionHead'
import { getPackages, getProjects, mediaUrl } from '@/lib/data'
import { faqSchema, JsonLd } from '@/lib/schema'
import { PackagesTabs } from './PackagesTabs'
import { LeadFormClient } from './LeadForm'

/* Blocks receive `dark` when the page alternates section colour. */
type B<T> = T & { dark?: boolean }
const cls = (dark?: boolean, extra = '') => `section ${dark ? 'section--dark' : ''} ${extra}`.trim()

/* ------------------------------------------------------------------ */
export const MarqueeBlock: React.FC<B<{ items?: { text: string }[] | null; style?: string | null }>> = ({ items, style, dark }) => {
  const list = (items || []).map((i) => i.text)
  if (!list.length) return null
  const loop = [...list, ...list]
  return (
    <div className={`${dark ? 'section--dark' : ''}`} aria-label={list.join(', ')}>
      <div className={`marquee marquee--${style || 'outline'}`} aria-hidden>
        <div className="marquee-track">
          {loop.map((t, i) => (
            <span key={i}>{t}</span>
          ))}
        </div>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
type ServicesProps = { eyebrow?: string | null; heading?: string | null; intro?: string | null; columns?: string | null; items?: { icon?: string | null; title: string; text?: string | null; href?: string | null }[] | null }
export const ServicesBlock: React.FC<B<ServicesProps>> = ({ eyebrow, heading, intro, items, columns, dark }) => (
  <section className={cls(dark)}>
    <div className="wrap">
      <SectionHead eyebrow={eyebrow} heading={heading} intro={intro} />
      <div className="svc-grid" style={{ ['--cols' as string]: columns || '3' }}>
        {(items || []).map((it, i) => {
          const inner = (
            <>
              <span className="num">{String(i + 1).padStart(2, '0')}</span>
              <span className="icon">
                <Icon name={it.icon} />
              </span>
              <h3 className="h3">{it.title}</h3>
              {it.text && <p>{it.text}</p>}
              {it.href && (
                <span className="go">
                  Explore <Arrow />
                </span>
              )}
            </>
          )
          return it.href ? (
            <Link key={i} href={it.href} className="svc" data-reveal style={{ ['--d' as string]: `${(i % 3) * 80}ms` }}>
              {inner}
            </Link>
          ) : (
            <div key={i} className="svc" data-reveal>
              {inner}
            </div>
          )
        })}
      </div>
    </div>
  </section>
)

/* ------------------------------------------------------------------ */
export const ProjectScreen: React.FC<{ project: Project; eager?: boolean }> = ({ project, eager }) => {
  const video = mediaUrl(project.video)
  const img = mediaUrl(project.cover)
  if (video)
    return <video src={video} poster={img || undefined} autoPlay muted loop playsInline preload={eager ? 'auto' : 'metadata'} aria-label={`${project.title} website walkthrough video`} />
  // eslint-disable-next-line @next/next/no-img-element
  if (img) return <img src={img} alt={`${project.title} website homepage`} loading={eager ? 'eager' : 'lazy'} />
  return null
}

type WorkProps = { eyebrow?: string | null; heading?: string | null; intro?: string | null; source?: string | null; style?: string | null; projects?: (number | string | Project)[] | null }
export const WorkBlock: React.FC<B<WorkProps>> = async ({ eyebrow, heading, intro, source, style, projects, dark }) => {
  const all = await getProjects()
  let list: Project[]
  if (source === 'pick') {
    const ids = (projects || []).map((p) => (typeof p === 'object' ? p.id : p))
    list = ids.map((id) => all.find((p) => p.id === id)).filter(Boolean) as Project[]
  } else if (source === 'featured') {
    list = all.filter((p) => p.featured)
    if (!list.length) list = all
  } else list = all
  if (!list.length) return null

  return (
    <section className={cls(dark)} id="work">
      <div className="wrap">
        <SectionHead eyebrow={eyebrow} heading={heading} intro={intro}>
          <div className="btn-row" style={{ marginTop: 20 }}>
            <Link href="/work" className="btn btn--ghost">
              All projects <Arrow />
            </Link>
          </div>
        </SectionHead>
        {style === 'grid' ? (
          <div className="work-grid">
            {list.map((p, i) => (
              <Link key={p.id} href={`/work/${p.slug}`} className="work-tile" data-reveal style={{ ['--accent' as string]: p.accent || undefined, ['--d' as string]: `${(i % 2) * 100}ms` }}>
                <div className="thumb">
                  <ProjectScreen project={p} />
                </div>
                <div className="row">
                  <h3>{p.title}</h3>
                  <span>{p.industry}</span>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="work-stack">
            {list.map((p, i) => (
              <Link key={p.id} href={`/work/${p.slug}`} className="work-card" style={{ ['--i' as string]: i, ['--accent' as string]: p.accent || undefined }}>
                <div className="info">
                  <div className="meta">
                    <span>{p.industry}</span>
                    {p.location && <span>{p.location}</span>}
                    {p.year && <span>{p.year}</span>}
                  </div>
                  <h3>{p.title}</h3>
                  <p>{p.summary}</p>
                  <span className="view">
                    View case study <Arrow />
                  </span>
                  {p.results && p.results.length > 0 && (
                    <div className="results">
                      {p.results.slice(0, 2).map((r, j) => (
                        <div key={j}>
                          <strong>{r.value}</strong>
                          <span>{r.label}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <div className="screen">
                  <div className="frame">
                    <ProjectScreen project={p} />
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}

/* ------------------------------------------------------------------ */
type PkgProps = { eyebrow?: string | null; heading?: string | null; intro?: string | null; groups?: string[] | null; note?: string | null }
export const PackagesBlock: React.FC<B<PkgProps>> = async ({ eyebrow, heading, intro, groups, note, dark }) => {
  const pkgs: Package[] = await getPackages()
  const filtered = groups && groups.length ? pkgs.filter((p) => groups.includes(p.group)) : pkgs
  return (
    <section className={cls(dark)} id="packages">
      <div className="wrap">
        <SectionHead eyebrow={eyebrow} heading={heading} intro={intro} />
        <PackagesTabs packages={filtered} />
        {note && <p className="pkg-note">{note}</p>}
      </div>
    </section>
  )
}

/* ------------------------------------------------------------------ */
type ProcessProps = { eyebrow?: string | null; heading?: string | null; intro?: string | null; steps?: { title: string; text?: string | null; duration?: string | null }[] | null }
export const ProcessBlock: React.FC<B<ProcessProps>> = ({ eyebrow, heading, intro, steps, dark }) => (
  <section className={cls(dark)}>
    <div className="wrap">
      <SectionHead eyebrow={eyebrow} heading={heading} intro={intro} />
      <ol className="process" style={{ padding: 0, margin: 0 }}>
        {(steps || []).map((s, i) => (
          <li key={i} data-reveal style={{ ['--d' as string]: `${i * 90}ms` }}>
            <h3 className="h3">{s.title}</h3>
            {s.text && <p>{s.text}</p>}
            {s.duration && <span className="dur">{s.duration}</span>}
          </li>
        ))}
      </ol>
    </div>
  </section>
)

/* ------------------------------------------------------------------ */
type StatsProps = { eyebrow?: string | null; heading?: string | null; intro?: string | null; items?: { value: string; label: string }[] | null }
export const StatsBlock: React.FC<B<StatsProps>> = ({ eyebrow, heading, intro, items, dark }) => (
  <section className={cls(dark, 'section--tight')}>
    <div className="wrap">
      <SectionHead eyebrow={eyebrow} heading={heading} intro={intro} />
      <div className="stats">
        {(items || []).map((s, i) => (
          <div key={i} data-reveal style={{ ['--d' as string]: `${i * 80}ms` }}>
            <strong>{s.value}</strong>
            <span>{s.label}</span>
          </div>
        ))}
      </div>
    </div>
  </section>
)

/* ------------------------------------------------------------------ */
type TProps = { eyebrow?: string | null; heading?: string | null; intro?: string | null; items?: { quote: string; name: string; role?: string | null; company?: string | null; rating?: number | null }[] | null }
export const TestimonialsBlock: React.FC<B<TProps>> = ({ eyebrow, heading, intro, items, dark }) => (
  <section className={cls(dark)}>
    <div className="wrap">
      <SectionHead eyebrow={eyebrow} heading={heading} intro={intro} />
      <div className="quotes">
        {(items || []).map((q, i) => (
          <figure key={i} className="quote" data-reveal style={{ ['--d' as string]: `${(i % 3) * 90}ms` }}>
            <div className="stars" aria-label={`${q.rating || 5} out of 5`}>
              {'★'.repeat(q.rating || 5)}
            </div>
            <blockquote>“{q.quote}”</blockquote>
            <figcaption>
              <span className="av" aria-hidden>
                {q.name.slice(0, 1)}
              </span>
              <div>
                <strong>{q.name}</strong>
                <span>{[q.role, q.company].filter(Boolean).join(', ')}</span>
              </div>
            </figcaption>
          </figure>
        ))}
      </div>
    </div>
  </section>
)

/* ------------------------------------------------------------------ */
type FaqProps = { eyebrow?: string | null; heading?: string | null; intro?: string | null; items?: { question: string; answer: string }[] | null }
export const FaqBlock: React.FC<B<FaqProps>> = ({ eyebrow, heading, intro, items, dark }) => {
  const list = items || []
  return (
    <section className={cls(dark)}>
      {list.length > 0 && <JsonLd data={faqSchema(list)} />}
      <div className="wrap faq">
        <div data-reveal>
          {eyebrow && <span className="eyebrow">{eyebrow}</span>}
          <h2 className="h2" style={{ marginTop: 18 }}>
            <Hl text={heading || 'Questions, *answered*'} />
          </h2>
          {intro && <p className="lead" style={{ marginTop: 20 }}>{intro}</p>}
        </div>
        <div data-reveal style={{ ['--d' as string]: '120ms' }}>
          {list.map((f, i) => (
            <details key={i} open={i === 0}>
              <summary>{f.question}</summary>
              <p>{f.answer}</p>
            </details>
          ))}
        </div>
      </div>
    </section>
  )
}

/* ------------------------------------------------------------------ */
type LeadProps = {
  formType: 'website_audit' | 'contact' | 'quote'
  eyebrow?: string | null
  heading?: string | null
  intro?: string | null
  bullets?: { text: string }[] | null
  submitLabel?: string | null
  successMessage?: string | null
  anchor?: string | null
}
export const LeadFormBlock: React.FC<B<LeadProps>> = async (p) => {
  const pkgs = p.formType === 'quote' ? (await getPackages()).filter((x) => x.group !== 'addons').map((x) => x.name) : []
  return (
    <section className={cls(p.dark)} id={p.anchor || (p.formType === 'website_audit' ? 'audit' : 'contact')}>
      <div className="wrap lead-wrap">
        <div data-reveal>
          {p.eyebrow && <span className="eyebrow">{p.eyebrow}</span>}
          <h2 className="h2" style={{ marginTop: 18 }}>
            <Hl text={p.heading} />
          </h2>
          {p.intro && <p className="lead" style={{ marginTop: 22 }}>{p.intro}</p>}
          {p.bullets && p.bullets.length > 0 && (
            <ul className="lead-bullets">
              {p.bullets.map((b, i) => (
                <li key={i}>{b.text}</li>
              ))}
            </ul>
          )}
        </div>
        <div data-reveal style={{ ['--d' as string]: '140ms' }}>
          <LeadFormClient formType={p.formType} submitLabel={p.submitLabel || 'Send'} successMessage={p.successMessage || ''} packages={pkgs} />
        </div>
      </div>
    </section>
  )
}

/* ------------------------------------------------------------------ */
type AreasProps = { eyebrow?: string | null; heading?: string | null; intro?: string | null; areas?: { name: string; href?: string | null; neighborhoods?: string | null }[] | null }
export const AreasBlock: React.FC<B<AreasProps>> = ({ eyebrow, heading, intro, areas, dark }) => (
  <section className={cls(dark)}>
    <div className="wrap">
      <SectionHead eyebrow={eyebrow} heading={heading} intro={intro} />
      <div className="areas">
        {(areas || []).map((a, i) => {
          const inner = (
            <>
              <svg className="pin" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden>
                <path d="M12 22s7-6.2 7-12a7 7 0 10-14 0c0 5.8 7 12 7 12z" />
                <circle cx="12" cy="10" r="2.5" />
              </svg>
              <h3>{a.name}</h3>
              {a.neighborhoods && <p>{a.neighborhoods}</p>}
            </>
          )
          return a.href ? (
            <Link href={a.href} className="area" key={i} data-reveal style={{ ['--d' as string]: `${i * 70}ms` }}>
              {inner}
            </Link>
          ) : (
            <div className="area" key={i} data-reveal>
              {inner}
            </div>
          )
        })}
      </div>
    </div>
  </section>
)

/* ------------------------------------------------------------------ */
type StatementProps = { text: string; links?: { link: React.ComponentProps<typeof CMSLink> }[] | null }
export const StatementBlock: React.FC<B<StatementProps>> = ({ text, links, dark }) => (
  <section className={cls(dark)}>
    <div className="wrap">
      <p className="statement" data-reveal>
        <Hl text={text} />
      </p>
      {links && links.length > 0 && (
        <div className="btn-row" data-reveal>
          {links.map(({ link }, i) => (
            <CMSLink key={i} {...link} appearance="inline" className={i === 0 ? (dark ? 'btn btn--lime' : 'btn') : 'btn btn--ghost'}>
              <Arrow />
            </CMSLink>
          ))}
        </div>
      )}
    </div>
  </section>
)
