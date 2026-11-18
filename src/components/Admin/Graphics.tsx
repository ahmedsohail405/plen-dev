import React from 'react'

export const AdminLogo = () => (
  <div style={{ display: 'flex', alignItems: 'baseline', gap: 2, fontWeight: 700, fontSize: 30, letterSpacing: '-0.05em' }}>
    plen<span style={{ width: 10, height: 10, borderRadius: 99, background: '#5b3bff', display: 'inline-block', margin: '0 2px' }} />
    <em style={{ fontFamily: 'Georgia, serif', fontWeight: 400 }}>dev</em>
    <span style={{ fontSize: 13, fontWeight: 500, letterSpacing: 0, marginLeft: 10, opacity: 0.6 }}>CMS</span>
  </div>
)

export const AdminIcon = () => (
  <span style={{ display: 'grid', placeItems: 'center', width: 26, height: 26, borderRadius: 8, background: '#0d0d0f', color: '#c8f560', fontWeight: 700, fontSize: 15 }}>p</span>
)
