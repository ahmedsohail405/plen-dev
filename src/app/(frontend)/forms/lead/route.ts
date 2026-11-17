import configPromise from '@payload-config'
import { getPayload } from 'payload'

const hits = new Map<string, number[]>()
const LIMIT = 5 // submissions per IP
const WINDOW = 10 * 60 * 1000 // per 10 minutes

const str = (v: unknown, max = 500) => (typeof v === 'string' ? v.trim().slice(0, max) : '')

const normaliseUrl = (v: string) => {
  if (!v) return ''
  const withProto = /^https?:\/\//i.test(v) ? v : `https://${v}`
  try {
    const u = new URL(withProto)
    return u.hostname.includes('.') ? u.toString() : ''
  } catch {
    return ''
  }
}

export async function POST(request: Request) {
  let body: Record<string, unknown>
  try {
    body = await request.json()
  } catch {
    return Response.json({ ok: false, error: 'Invalid request' }, { status: 400 })
  }

  // Honeypot: real visitors never see or fill the "company_site" field.
  if (str(body.company_site)) return Response.json({ ok: true })

  const ip = (request.headers.get('x-forwarded-for') || 'local').split(',')[0]!.trim()
  const now = Date.now()
  const recent = (hits.get(ip) || []).filter((t) => now - t < WINDOW)
  if (recent.length >= LIMIT) {
    return Response.json({ ok: false, error: 'Too many requests, please try again shortly.' }, { status: 429 })
  }
  hits.set(ip, [...recent, now])

  const type = ['website_audit', 'contact', 'quote'].includes(str(body.type)) ? str(body.type) : 'contact'
  const name = str(body.name, 120)
  const email = str(body.email, 200)
  const website_url = normaliseUrl(str(body.website_url, 300))

  const errors: Record<string, string> = {}
  if (!name) errors.name = 'Please enter your name.'
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errors.email = 'Please enter a valid email.'
  if (type === 'website_audit' && !website_url) errors.website_url = 'Please enter your website address.'
  if (type === 'website_audit' && body.consent_marketing !== true)
    errors.consent_marketing = 'Please agree so we can email your report.'
  if (Object.keys(errors).length) return Response.json({ ok: false, errors }, { status: 422 })

  const utm = (body.utm && typeof body.utm === 'object' ? body.utm : {}) as Record<string, unknown>
  const payload = await getPayload({ config: configPromise })
  const lead = await payload.create({
    collection: 'leads',
    overrideAccess: true,
    data: {
      type: type as 'website_audit' | 'contact' | 'quote',
      name,
      email,
      phone: str(body.phone, 40),
      company: str(body.company, 160),
      website_url,
      industry: str(body.industry, 120),
      package: str(body.package, 120),
      budget: str(body.budget, 60),
      message: str(body.message, 4000),
      consent_marketing: body.consent_marketing === true,
      source_page: str(body.source_page, 300),
      referrer: str(body.referrer, 300),
      utm: { source: str(utm.source, 100), medium: str(utm.medium, 100), campaign: str(utm.campaign, 100) },
      ip,
    },
  })

  return Response.json({ ok: true, id: lead.id })
}
