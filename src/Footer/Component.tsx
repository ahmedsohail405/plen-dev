import Link from 'next/link'
import React from 'react'

import { getCachedGlobal } from '@/utilities/getGlobals'
import { getSettings } from '@/lib/data'
import { Hl } from '@/components/studio/Hl'

export async function Footer() {
  const [footer, s] = await Promise.all([getCachedGlobal('footer', 1)(), getSettings()])
  const year = new Date().getFullYear()
  const addr = s.address
  return (
    <footer className="site-footer">
      <div className="wrap">
        <p className="big">
          <Link href="/contact">
            <Hl text={footer.bigLine || "Let's build *something.*"} />
          </Link>
        </p>
        <div className="btn-row">
          <Link href="/website-audit" className="btn btn--lime">
            Get a free website audit
          </Link>
          {s.email && (
            <a href={`mailto:${s.email}`} className="btn btn--ghost" style={{ ['--fg' as string]: 'var(--paper)', borderColor: 'var(--line-dark)' }}>
              {s.email}
            </a>
          )}
        </div>
        <div className="foot-cols">
          <div>
            <h4>{s.businessName}</h4>
            <p>{s.tagline}</p>
            {addr && (addr.city || addr.region) && (
              <p>
                {!addr.hideStreet && addr.street ? `${addr.street}, ` : ''}
                {[addr.city, addr.region].filter(Boolean).join(', ')} {addr.postalCode || ''}
              </p>
            )}
            {s.phone && (
              <p>
                <a href={`tel:${s.phone.replace(/[^\d+]/g, '')}`}>{s.phone}</a>
              </p>
            )}
            {s.email && (
              <p>
                <a href={`mailto:${s.email}`}>{s.email}</a>
              </p>
            )}
          </div>
          {(footer.columns || []).map((c, i) => (
            <div key={i}>
              <h4>{c.title}</h4>
              <ul>
                {(c.links || []).map((l, j) => (
                  <li key={j}>
                    <Link href={l.href}>{l.label}</Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="foot-bottom">
          <span>
            © {year} {s.legalName || s.businessName}. Websites designed and built in New York.
          </span>
          <span>
            {(s.social || []).map((x, i) => (
              <a key={i} href={x.url} rel="noopener" target="_blank" style={{ marginLeft: 16 }}>
                {x.platform}
              </a>
            ))}
            <a href="/llms.txt" style={{ marginLeft: 16 }}>
              llms.txt
            </a>
            <a href="/sitemap.xml" style={{ marginLeft: 16 }}>
              Sitemap
            </a>
          </span>
        </div>
      </div>
    </footer>
  )
}
