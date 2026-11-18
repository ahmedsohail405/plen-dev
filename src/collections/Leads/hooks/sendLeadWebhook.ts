import crypto from 'crypto'
import { after } from 'next/server'
import type { CollectionAfterChangeHook } from 'payload'

/**
 * POSTs every new lead to the audit agent (contract:
 * /mnt/project-files/audit-agent/LEAD_CONTRACT.md). URL comes from Site Settings
 * (falls back to AUDIT_WEBHOOK_URL env); body is HMAC-SHA256 signed with
 * AUDIT_WEBHOOK_SECRET in the X-PlenDev-Signature header. Sent with Next's after(),
 * so the visitor's response is not delayed and Vercel keeps the function alive until
 * delivery finishes. Outside a request (scripts), it is awaited instead.
 */
export const sendLeadWebhook: CollectionAfterChangeHook = async ({ doc, operation, req }) => {
  if (operation !== 'create') return doc

  let url = process.env.AUDIT_WEBHOOK_URL || ''
  try {
    const settings = await req.payload.findGlobal({ slug: 'site-settings', depth: 0, overrideAccess: true })
    const s = settings as { integrations?: { leadWebhookUrl?: string | null; leadWebhookEnabled?: boolean | null } }
    if (s.integrations?.leadWebhookEnabled === false) return doc
    if (s.integrations?.leadWebhookUrl) url = s.integrations.leadWebhookUrl
  } catch {
    /* settings not created yet */
  }
  if (!url) return doc

  const body = JSON.stringify({
    event: 'lead.created',
    lead: {
      id: String(doc.id),
      type: doc.type,
      created_at: doc.createdAt,
      name: doc.name || '',
      email: doc.email || '',
      phone: doc.phone || '',
      company: doc.company || '',
      website_url: doc.website_url || '',
      industry: doc.industry || '',
      message: doc.message || '',
      source_page: doc.source_page || '',
      utm: {
        source: doc.utm?.source || '',
        medium: doc.utm?.medium || '',
        campaign: doc.utm?.campaign || '',
      },
      consent_marketing: Boolean(doc.consent_marketing),
    },
  })
  const secret = process.env.AUDIT_WEBHOOK_SECRET || ''
  const signature = 'sha256=' + crypto.createHmac('sha256', secret).update(body).digest('hex')

  const payload = req.payload
  const id = doc.id
  const deliver = async () => {
    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'content-type': 'application/json', 'x-plendev-signature': signature },
        body,
        signal: AbortSignal.timeout(10000),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      await payload.update({
        collection: 'leads',
        id,
        data: { webhook_delivered_at: new Date().toISOString() },
        overrideAccess: true,
        context: { skipWebhook: true },
      })
    } catch (err) {
      payload.logger.error(`Lead webhook failed for ${id}: ${String(err)}`)
    }
  }

  try {
    after(deliver)
  } catch {
    // Not inside a Next.js request (for example a seed script): just wait for it.
    await deliver()
  }

  return doc
}
