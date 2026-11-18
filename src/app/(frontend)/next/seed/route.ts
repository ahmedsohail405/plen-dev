import { createLocalReq, getPayload } from 'payload'
import { seed } from '@/endpoints/seed'
import config from '@payload-config'
import { headers } from 'next/headers'

export const maxDuration = 60

/** Re-seeds demo content. Disabled in production because it replaces all pages. */
export async function POST(): Promise<Response> {
  if (process.env.NODE_ENV === 'production' && process.env.ALLOW_SEED !== 'true') {
    return new Response('Seeding is disabled in production.', { status: 403 })
  }
  const payload = await getPayload({ config })
  const { user } = await payload.auth({ headers: await headers() })
  if (!user || (user as { role?: string }).role !== 'admin') return new Response('Action forbidden.', { status: 403 })
  try {
    await seed({ payload, req: await createLocalReq({ user }, payload) })
    return Response.json({ success: true })
  } catch (e) {
    payload.logger.error({ err: e, message: 'Error seeding data' })
    return new Response('Error seeding data.', { status: 500 })
  }
}
