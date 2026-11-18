'use client'
import React, { useState } from 'react'

/** One-time button that loads the Plen Dev pages, packages and portfolio into an empty database. */
export const LoadContentButton: React.FC<{ mode?: 'all' | 'media' | 'reset' }> = ({ mode = 'all' }) => {
  const [state, setState] = useState<'idle' | 'loading' | 'done' | 'error'>('idle')
  const [msg, setMsg] = useState('')
  const run = async () => {
    if (state === 'loading') return
    if (mode === 'reset' && !window.confirm('Reload all website content? This replaces pages, packages, portfolio and blog posts with the latest Plen Dev content. Leads, users and media are kept.')) return
    setState('loading')
    try {
      const res = await fetch(mode === 'media' ? '/next/seed?mode=media' : '/next/seed', { method: 'POST', credentials: 'include' })
      if (!res.ok) throw new Error(await res.text())
      const json = (await res.json()) as { mediaErrors?: string[] }
      if (json.mediaErrors?.length) {
        setState('error')
        setMsg(`Content loaded, but some demo videos/images failed: ${json.mediaErrors.join('; ')}`)
        return
      }
      setState('done')
      setTimeout(() => window.location.reload(), 1200)
    } catch (e) {
      setState('error')
      setMsg(e instanceof Error ? e.message : 'Something went wrong')
    }
  }
  return (
    <div style={{ marginTop: 16, padding: '16px 20px', borderRadius: 12, border: '1px dashed var(--theme-elevation-250)' }}>
      <strong>{mode === 'media' ? 'Some portfolio videos or images are missing.' : mode === 'reset' ? 'Reload website content' : 'The site has no content yet.'}</strong>
      <p style={{ margin: '6px 0 12px', opacity: 0.75 }}>
        {mode === 'media'
          ? 'Add the missing demo videos and cover images. Your pages and edits are not changed.'
          : mode === 'reset'
            ? 'Replaces pages, packages, portfolio and blog posts with the latest Plen Dev content. Edits you made to those are lost. Leads and users are kept.'
            : 'Load the Plen Dev pages, packages, portfolio and blog posts. This takes about a minute.'}
      </p>
      <button type="button" className="btn btn--style-primary btn--size-medium" onClick={run} disabled={state === 'loading' || state === 'done'}>
        {state === 'loading' ? 'Loading…' : state === 'done' ? 'Done, reloading…' : mode === 'media' ? 'Add missing media' : mode === 'reset' ? 'Reload content' : 'Load website content'}
      </button>
      {state === 'error' && <p style={{ color: 'var(--theme-error-500)' }}>{msg}</p>}
    </div>
  )
}
