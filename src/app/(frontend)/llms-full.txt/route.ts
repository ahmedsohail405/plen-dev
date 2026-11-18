import { buildLlms } from '@/lib/llms'

export const revalidate = 3600

export async function GET() {
  const body = await buildLlms(true)
  return new Response(body, { headers: { 'content-type': 'text/plain; charset=utf-8', 'cache-control': 'public, max-age=0, s-maxage=3600' } })
}
