import type { CollectionBeforeChangeHook } from 'payload'

/** Builds the public URL path from the parent chain + slug (e.g. /locations/long-island/nassau-county). */
export const setPagePath: CollectionBeforeChangeHook = async ({ data, originalDoc, req }) => {
  const slug = data.slug ?? originalDoc?.slug
  if (!slug) return data
  if (slug === 'home') {
    data.path = '/'
    return data
  }
  const parentRef = data.parent !== undefined ? data.parent : originalDoc?.parent
  const parentId = parentRef && typeof parentRef === 'object' ? parentRef.id : parentRef
  let prefix = ''
  if (parentId) {
    const parent = await req.payload.findByID({ collection: 'pages', id: parentId, depth: 0, draft: true, overrideAccess: true, req })
    if (parent?.path && parent.path !== '/') prefix = parent.path
    else if (parent?.slug && parent.slug !== 'home') prefix = `/${parent.slug}`
  }
  data.path = `${prefix}/${slug}`
  return data
}
