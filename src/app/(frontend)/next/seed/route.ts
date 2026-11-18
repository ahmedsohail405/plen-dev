import { createLocalReq, getPayload } from 'payload'
import { seed } from '@/endpoints/seed'
import config from '@payload-config'
import { headers } from 'next/headers'
import { revalidatePath, revalidateTag } from 'next/cache'

export const maxDuration = 300

/** Re-seeds demo content. Disabled in production because it replaces all pages. */
export async function POST(): Promise<Response> {
  if (process.env.NODE_ENV === 'production' && process.env.ALLOW_SEED !== 'true') {
    return new Response('Seeding is disabled in production.', { status: 403 })
  }
  const payload = await getPayload({ config })
  const { user } = await payload.auth({ headers: await headers() })
  if (!user || (user as { role?: string }).role !== 'admin') return new Response('Action forbidden.', { status: 403 })
  try {
    const { mediaErrors } = await seed({ payload, req: await createLocalReq({ user }, payload) })
    // Seeding skips per-document revalidation, so clear every cached page and data entry once
    for (const tag of ['packages', 'projects', 'redirects', 'pages-sitemap', 'global_site-settings', 'global_header', 'global_footer']) {
      revalidateTag(tag, 'max')
    }
    revalidatePath('/', 'layout')
    return Response.json({ success: true, mediaErrors })
  } catch (e) {
    payload.logger.error({ err: e, message: 'Error seeding data' })
    const detail = e instanceof Error ? e.message : String(e)
    return new Response(`Error loading content: ${detail.slice(0, 400)}`, { status: 500 })
  }
}
