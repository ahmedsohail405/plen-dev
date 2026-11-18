'use client'
import React, { useState } from 'react'

import type { Package } from '@/payload-types'

const GROUPS: Record<string, string> = {
  websites: 'Websites',
  ecommerce: 'Ecommerce',
  'cms-apps': 'Custom CMS & Web Apps',
  care: 'Care Plans',
  addons: 'Add-ons',
}
const per: Record<string, string> = { monthly: '/mo', 'per-page': '/page', each: '', 'one-time': '' }
const fmt = (n: number) => '$' + n.toLocaleString('en-US')

export const PriceTag: React.FC<{ p: Package }> = ({ p }) =>
  p.price != null ? (
    <>
      {p.pricePrefix && <small>{p.pricePrefix}</small>}
      <strong>{p.price === 0 ? 'Free' : fmt(p.price)}</strong>
      {p.billing && per[p.billing] && <small>{per[p.billing]}</small>}
    </>
  ) : (
    <strong>{p.priceNote || 'Custom'}</strong>
  )

const Card: React.FC<{ p: Package }> = ({ p }) => (
  <article className={`pkg ${p.highlighted ? 'is-hot' : ''}`}>
    {p.highlighted && <span className="badge">Most popular</span>}
    <div className="name">{p.name}</div>
    {p.tagline && <p className="tagline">{p.tagline}</p>}
    <div className="price">
      <PriceTag p={p} />
    </div>
    {(p.scope || p.timeline) && (
      <div className="facts">
        {p.scope && <span>{p.scope}</span>}
        {p.timeline && <span>{p.timeline}</span>}
      </div>
    )}
    {p.features && p.features.length > 0 && (
      <ul>
        {p.features.map((f, i) => (
          <li key={i}>{f.feature}</li>
        ))}
      </ul>
    )}
    <a className="btn" href={`/contact?package=${encodeURIComponent(p.name)}#contact`}>
      {p.ctaLabel || 'Get started'}
    </a>
  </article>
)

/**
 * All groups are rendered in the HTML (so Google and AI tools can read every
 * price); the tabs only filter what is visible.
 */
export const PackagesTabs: React.FC<{ packages: Package[] }> = ({ packages }) => {
  const groups = Array.from(new Set(packages.map((p) => p.group))).sort(
    (a, b) => Object.keys(GROUPS).indexOf(a) - Object.keys(GROUPS).indexOf(b),
  )
  const [active, setActive] = useState<string>('all')
  if (!packages.length) return null
  return (
    <>
      {groups.length > 1 && (
        <div className="pkg-tabs" role="tablist" aria-label="Package categories">
          {['all', ...groups].map((g) => (
            <button key={g} role="tab" aria-selected={active === g} onClick={() => setActive(g)}>
              {g === 'all' ? 'All packages' : GROUPS[g] || g}
            </button>
          ))}
        </div>
      )}
      {groups.map((g) => {
        const list = packages.filter((p) => p.group === g)
        return (
          <div key={g} className="pkg-group" hidden={active !== 'all' && active !== g}>
            {groups.length > 1 && <h3 className="h3">{GROUPS[g] || g}</h3>}
            {g === 'addons' ? (
              <div className="pkg-addons">
                {list.map((p) => (
                  <div key={p.id}>
                    <span>
                      {p.name}
                      {p.tagline ? <small style={{ display: 'block', color: 'var(--muted)' }}>{p.tagline}</small> : null}
                    </span>
                    <strong>{p.price != null ? `${p.pricePrefix ? p.pricePrefix + ' ' : ''}${p.price === 0 ? 'Free' : fmt(p.price)}${per[p.billing || ''] || ''}` : p.priceNote}</strong>
                  </div>
                ))}
              </div>
            ) : (
              <div className="pkg-grid">
                {list.map((p) => (
                  <Card key={p.id} p={p} />
                ))}
              </div>
            )}
          </div>
        )
      })}
    </>
  )
}
