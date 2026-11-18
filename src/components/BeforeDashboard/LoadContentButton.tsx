'use client'
import React, { useState } from 'react'

/** One-time button that loads the Plen Dev pages, packages and portfolio into an empty database. */
export const LoadContentButton: React.FC = () => {
  const [state, setState] = useState<'idle' | 'loading' | 'done' | 'error'>('idle')
  const [msg, setMsg] = useState('')
  const run = async () => {
    if (state === 'loading') return
    setState('loading')
    try {
      const res = await fetch('/next/seed', { method: 'POST', credentials: 'include' })
      if (!res.ok) throw new Error(await res.text())
      setState('done')
      setTimeout(() => window.location.reload(), 1200)
    } catch (e) {
      setState('error')
      setMsg(e instanceof Error ? e.message : 'Something went wrong')
    }
  }
  return (
    <div style={{ marginTop: 16, padding: '16px 20px', borderRadius: 12, border: '1px dashed var(--theme-elevation-250)' }}>
      <strong>The site has no content yet.</strong>
      <p style={{ margin: '6px 0 12px', opacity: 0.75 }}>
        Load the Plen Dev pages, packages, portfolio and blog posts. This takes about a minute.
      </p>
      <button type="button" className="btn btn--style-primary btn--size-medium" onClick={run} disabled={state === 'loading' || state === 'done'}>
        {state === 'loading' ? 'Loading content…' : state === 'done' ? 'Done, reloading…' : 'Load website content'}
      </button>
      {state === 'error' && <p style={{ color: 'var(--theme-error-500)' }}>{msg}</p>}
    </div>
  )
}
