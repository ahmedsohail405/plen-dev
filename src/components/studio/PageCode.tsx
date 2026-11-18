import React from 'react'

import { getSettings } from '@/lib/data'
import { CodeSnippets, snippetApplies, type Snippet } from './CodeSnippets'

/**
 * Page-level code: site-wide snippets scoped to specific pages plus the page's
 * own snippets. <meta>/<link> are hoisted into <head> by React; scripts run
 * where they are rendered.
 */
export const PageCode = async ({ path, docId, own }: { path: string; docId?: string | number | null; own?: Snippet[] | null }) => {
  const s = await getSettings()
  const scoped = ((s.codeSnippets || []) as Snippet[]).filter((x) => x.scope && x.scope !== 'all' && snippetApplies(x, path, docId))
  const list = [...scoped, ...((own || []) as Snippet[])].filter((x) => x.enabled !== false)
  if (!list.length) return null
  return (
    <>
      <CodeSnippets snippets={list} placement="head" />
      <CodeSnippets snippets={list} placement="bodyStart" />
      <CodeSnippets snippets={list} placement="bodyEnd" />
    </>
  )
}
