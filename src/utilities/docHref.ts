/** Public URL for a page or post document. Pages use their nested `path`. */
export const docHref = (relationTo: string | undefined, doc: { slug?: string | null; path?: string | null } | null | undefined) => {
  if (!doc) return null
  if (relationTo === 'posts') return doc.slug ? `/blog/${doc.slug}` : null
  if (relationTo === 'projects') return doc.slug ? `/work/${doc.slug}` : null
  if (doc.path) return doc.path
  if (!doc.slug) return null
  return doc.slug === 'home' ? '/' : `/${doc.slug}`
}
