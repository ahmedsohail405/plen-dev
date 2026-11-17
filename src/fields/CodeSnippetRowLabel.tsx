'use client'
import { useRowLabel } from '@payloadcms/ui'

export const CodeSnippetRowLabel = () => {
  const { data, rowNumber } = useRowLabel<{ label?: string; placement?: string; enabled?: boolean; scope?: string }>()
  const where = { head: '<head>', bodyStart: 'body start', bodyEnd: 'body end' }[data?.placement || 'head']
  const scope = data?.scope && data.scope !== 'all' ? ` · ${data.scope === 'include' ? 'selected pages' : 'excluding pages'}` : ''
  return (
    <span>
      {data?.label || `Snippet ${String((rowNumber ?? 0) + 1).padStart(2, '0')}`} — {where}
      {scope}
      {data?.enabled === false ? ' (off)' : ''}
    </span>
  )
}
