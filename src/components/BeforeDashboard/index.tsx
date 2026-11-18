import configPromise from '@payload-config'
import { getPayload } from 'payload'
import React from 'react'

import { LoadContentButton } from './LoadContentButton'
import './index.scss'

const baseClass = 'before-dashboard'

/** Plen CMS welcome panel: new leads at a glance and quick links. */
const BeforeDashboard = async () => {
  const payload = await getPayload({ config: configPromise })
  const [newLeads, audits, pages] = await Promise.all([
    payload.count({ collection: 'leads', where: { status: { equals: 'new' } }, overrideAccess: true }),
    payload.count({ collection: 'leads', where: { audit_status: { equals: 'awaiting_approval' } }, overrideAccess: true }),
    payload.count({ collection: 'pages', overrideAccess: true }),
  ])
  const card = { padding: '18px 20px', borderRadius: 12, border: '1px solid var(--theme-elevation-150)', textDecoration: 'none', color: 'inherit', display: 'block' }
  return (
    <div className={baseClass}>
      <h2 style={{ marginBottom: 6 }}>Welcome to the Plen CMS</h2>
      <p style={{ opacity: 0.7, marginTop: 0 }}>Edit any page with live preview, follow up on leads and manage SEO and tracking code from here.</p>
      {pages.totalDocs === 0 && <LoadContentButton />}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12, marginTop: 16 }}>
        <a href="/admin/collections/leads?where[status][equals]=new" style={card}>
          <strong style={{ fontSize: 28 }}>{newLeads.totalDocs}</strong>
          <div>new leads</div>
        </a>
        <a href="/admin/collections/leads?where[audit_status][equals]=awaiting_approval" style={card}>
          <strong style={{ fontSize: 28 }}>{audits.totalDocs}</strong>
          <div>audits awaiting your approval</div>
        </a>
        <a href="/admin/collections/pages" style={card}>
          <strong style={{ fontSize: 18 }}>Edit pages →</strong>
          <div>Open a page, then click the eye icon for live preview</div>
        </a>
        <a href="/admin/globals/site-settings" style={card}>
          <strong style={{ fontSize: 18 }}>Site settings →</strong>
          <div>Business info, header code, analytics, AI crawlers</div>
        </a>
      </div>
    </div>
  )
}

export default BeforeDashboard
