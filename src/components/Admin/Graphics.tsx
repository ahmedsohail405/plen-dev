import React from 'react'

export const AdminLogo = () => (
  <div style={{ display: 'flex', alignItems: 'baseline', gap: 2, fontWeight: 700, fontSize: 30, letterSpacing: '-0.05em' }}>
    Plen&nbsp;<em style={{ fontFamily: 'Georgia, serif', fontWeight: 400, color: '#8b74ff' }}>Dev</em>
    <span style={{ fontSize: 13, fontWeight: 500, letterSpacing: 0, marginLeft: 10, opacity: 0.6 }}>CMS</span>
  </div>
)

export const AdminIcon = () => (
  // eslint-disable-next-line @next/next/no-img-element
  <img src="/brand/plendev-avatar-ink.svg" alt="Plen Dev" width={26} height={26} style={{ borderRadius: 8, display: 'block' }} />
)
