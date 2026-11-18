/** Minimal Markdown → Lexical JSON for seed posts: ## headings, paragraphs, - / 1. lists, **bold**, [links](url). */
type Node = Record<string, unknown>

const text = (t: string, format = 0): Node => ({ type: 'text', text: t, format, detail: 0, mode: 'normal', style: '', version: 1 })

const inline = (s: string): Node[] => {
  const out: Node[] = []
  const re = /(\*\*([^*]+)\*\*)|(\[([^\]]+)\]\(([^)]+)\))/g
  let last = 0
  let m: RegExpExecArray | null
  while ((m = re.exec(s))) {
    if (m.index > last) out.push(text(s.slice(last, m.index)))
    if (m[2]) out.push(text(m[2], 1))
    else if (m[4])
      out.push({
        type: 'link',
        version: 3,
        direction: 'ltr',
        format: '',
        indent: 0,
        fields: { linkType: 'custom', url: m[5], newTab: false },
        children: [text(m[4])],
      })
    last = m.index + m[0].length
  }
  if (last < s.length) out.push(text(s.slice(last)))
  return out
}

const block = (type: string, children: Node[], extra: Node = {}): Node => ({ type, version: 1, direction: 'ltr', format: '', indent: 0, children, ...extra })

export const mdToLexical = (md: string) => {
  const children: Node[] = []
  const chunks = md.trim().split(/\n\s*\n/)
  for (const chunk of chunks) {
    const lines = chunk.split('\n').map((l) => l.trim())
    const h = /^(#{2,4})\s+(.*)$/.exec(lines[0]!)
    if (h && lines.length === 1) {
      children.push(block('heading', inline(h[2]!), { tag: `h${h[1]!.length}` }))
      continue
    }
    if (lines.every((l) => /^[-*]\s+/.test(l)) || lines.every((l) => /^\d+\.\s+/.test(l))) {
      const ordered = /^\d+\./.test(lines[0]!)
      children.push(
        block(
          'list',
          lines.map((l, i) => block('listitem', inline(l.replace(/^([-*]|\d+\.)\s+/, '')), { value: i + 1 })),
          { listType: ordered ? 'number' : 'bullet', start: 1, tag: ordered ? 'ol' : 'ul' },
        ),
      )
      continue
    }
    children.push(block('paragraph', inline(lines.join(' ')), { textFormat: 0, textStyle: '' }))
  }
  return { root: { type: 'root', format: '', indent: 0, version: 1, direction: 'ltr', children } }
}
