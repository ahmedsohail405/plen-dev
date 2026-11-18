import { parse, HTMLElement, NodeType, type Node } from 'node-html-parser'
import React from 'react'

export type Snippet = {
  id?: string | null
  label?: string | null
  code?: string | null
  placement?: 'head' | 'bodyStart' | 'bodyEnd' | null
  enabled?: boolean | null
  scope?: 'all' | 'include' | 'exclude' | null
  pages?: { relationTo: string; value: unknown }[] | null
  paths?: string | null
}

const toReactAttrs = (el: HTMLElement) => {
  const out: Record<string, string | boolean> = {}
  for (const [k, v] of Object.entries(el.attributes)) {
    const key =
      k === 'class' ? 'className' : k === 'charset' ? 'charSet' : k === 'http-equiv' ? 'httpEquiv' : k === 'crossorigin' ? 'crossOrigin' : k === 'referrerpolicy' ? 'referrerPolicy' : k
    out[key] = ['async', 'defer', 'nomodule'].includes(k) ? true : v
  }
  return out
}

/**
 * Turns raw pasted HTML into React elements. <meta>/<link>/<title> are hoisted
 * into <head> by React 19 wherever they render; scripts keep their inline code
 * and run when the HTML loads.
 */
const renderNode = (node: Node, key: string): React.ReactNode => {
  if (node.nodeType === NodeType.COMMENT_NODE) return null
  if (node.nodeType === NodeType.TEXT_NODE) {
    const t = node.rawText.trim()
    return t ? <React.Fragment key={key}>{t}</React.Fragment> : null
  }
  const el = node as HTMLElement
  const tag = el.rawTagName?.toLowerCase()
  if (!tag) return null
  const attrs = toReactAttrs(el)
  if (tag === 'script' || tag === 'style' || tag === 'noscript') {
    return React.createElement(tag, { key, ...attrs, dangerouslySetInnerHTML: { __html: el.innerHTML } })
  }
  if (tag === 'meta' || tag === 'link' || tag === 'base') return React.createElement(tag, { key, ...attrs })
  if (tag === 'title') return <title key={key}>{el.text}</title>
  return React.createElement(tag, { key, ...attrs, dangerouslySetInnerHTML: { __html: el.innerHTML } })
}

export const renderSnippetHtml = (code: string, keyPrefix: string) =>
  parse(code, { comment: false, blockTextElements: { script: true, noscript: true, style: true } })
    .childNodes.map((n, i) => renderNode(n, `${keyPrefix}-${i}`))
    .filter(Boolean)

const globToRegex = (p: string) => new RegExp('^' + p.trim().replace(/\/+$/, '').replace(/[.+?^${}()|[\]\\]/g, '\\$&').replace(/\*/g, '.*') + '/?$')

/** Does a scoped site-wide snippet apply to this document / path? */
export const snippetApplies = (s: Snippet, path: string, docId?: string | number | null) => {
  if (s.enabled === false || !s.code) return false
  const scope = s.scope || 'all'
  if (scope === 'all') return true
  const ids = (s.pages || []).map((p) => (p.value && typeof p.value === 'object' ? (p.value as { id: unknown }).id : p.value)).map(String)
  const byId = docId != null && ids.includes(String(docId))
  const byPath = (s.paths || '')
    .split(',')
    .filter((p) => p.trim())
    .some((p) => globToRegex(p).test(path.replace(/\/+$/, '') || '/'))
  const hit = byId || byPath
  return scope === 'include' ? hit : !hit
}

export const CodeSnippets: React.FC<{ snippets: Snippet[]; placement: 'head' | 'bodyStart' | 'bodyEnd' }> = ({ snippets, placement }) => {
  const list = snippets.filter((s) => s.enabled !== false && s.code && (s.placement || 'head') === placement)
  if (!list.length) return null
  return <>{list.flatMap((s, i) => renderSnippetHtml(s.code as string, `${placement}-${s.id || i}`))}</>
}
