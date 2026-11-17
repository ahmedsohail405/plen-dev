import type { CollectionConfig, FieldAccess } from 'payload'

import { anyUser, authenticated } from '../../access/authenticated'
import { sendLeadWebhook } from './hooks/sendLeadWebhook'

const staffOnly: FieldAccess = ({ req }) =>
  Boolean(req.user) && (req.user as { role?: string }).role !== 'service'
const anyLoggedIn: FieldAccess = ({ req }) => Boolean(req.user)

/** Fields the audit agent may write back (PATCH /api/leads/:id). */
const auditField = { access: { create: anyLoggedIn, update: anyLoggedIn, read: anyLoggedIn } }
/** Lead fields: anyone can submit them, only staff can edit them afterwards. */
const leadField = { access: { update: staffOnly } }

export const Leads: CollectionConfig = {
  slug: 'leads',
  labels: { singular: 'Lead', plural: 'Leads' },
  access: {
    // Website forms submit through /forms/lead (honeypot + rate limit), which
    // creates the lead server-side. The REST create stays closed to the public.
    create: anyUser,
    read: anyUser,
    update: anyUser,
    delete: authenticated,
  },
  admin: {
    useAsTitle: 'name',
    group: 'Leads',
    defaultColumns: ['name', 'type', 'website_url', 'status', 'audit_status', 'createdAt'],
    listSearchableFields: ['name', 'email', 'company', 'website_url', 'phone'],
    description:
      'Every form submission on the website lands here. Website-audit requests are sent to the audit agent automatically.',
  },
  defaultSort: '-createdAt',
  fields: [
    {
      type: 'row',
      fields: [
        {
          name: 'type',
          type: 'select',
          required: true,
          defaultValue: 'contact',
          options: [
            { label: 'Website audit', value: 'website_audit' },
            { label: 'Contact', value: 'contact' },
            { label: 'Quote / package', value: 'quote' },
          ],
          ...leadField,
        },
        {
          name: 'status',
          type: 'select',
          defaultValue: 'new',
          options: [
            { label: 'New', value: 'new' },
            { label: 'Contacted', value: 'contacted' },
            { label: 'Proposal sent', value: 'proposal' },
            { label: 'Won', value: 'won' },
            { label: 'Lost', value: 'lost' },
          ],
          access: { create: staffOnly, update: staffOnly },
        },
      ],
    },
    {
      type: 'row',
      fields: [
        { name: 'name', type: 'text', required: true, ...leadField },
        { name: 'email', type: 'email', required: true, ...leadField },
        { name: 'phone', type: 'text', ...leadField },
      ],
    },
    {
      type: 'row',
      fields: [
        { name: 'company', type: 'text', ...leadField },
        { name: 'website_url', label: 'Website URL', type: 'text', ...leadField },
        { name: 'industry', label: 'Business type', type: 'text', ...leadField },
      ],
    },
    { name: 'package', type: 'text', admin: { description: 'Package the visitor picked, if any.' }, ...leadField },
    { name: 'budget', type: 'text', ...leadField },
    { name: 'message', type: 'textarea', ...leadField },
    {
      name: 'consent_marketing',
      label: 'Agreed to receive the report / follow-up by email',
      type: 'checkbox',
      defaultValue: false,
      ...leadField,
    },
    {
      type: 'collapsible',
      label: 'Source & tracking',
      admin: { initCollapsed: true },
      fields: [
        { name: 'source_page', type: 'text', ...leadField },
        {
          name: 'utm',
          type: 'group',
          fields: [
            { name: 'source', type: 'text' },
            { name: 'medium', type: 'text' },
            { name: 'campaign', type: 'text' },
          ],
          ...leadField,
        },
        { name: 'referrer', type: 'text', ...leadField },
        { name: 'ip', type: 'text', access: { create: staffOnly, update: staffOnly, read: staffOnly } },
        { name: 'webhook_delivered_at', type: 'date', admin: { readOnly: true }, access: { create: staffOnly, update: staffOnly } },
      ],
    },
    {
      type: 'collapsible',
      label: 'Website audit',
      admin: { condition: (data) => data?.type === 'website_audit' || Boolean(data?.website_url) },
      fields: [
        {
          type: 'row',
          fields: [
            {
              name: 'audit_status',
              type: 'select',
              defaultValue: 'none',
              options: [
                { label: 'None', value: 'none' },
                { label: 'Queued', value: 'queued' },
                { label: 'Auditing', value: 'auditing' },
                { label: 'Awaiting approval', value: 'awaiting_approval' },
                { label: 'Approved', value: 'approved' },
                { label: 'Sent to client', value: 'sent' },
                { label: 'Failed', value: 'failed' },
              ],
              ...auditField,
            },
            { name: 'audit_score', type: 'number', min: 0, max: 100, ...auditField },
          ],
        },
        { name: 'audit_report_url', type: 'text', ...auditField },
        { name: 'audit_sent_at', type: 'date', admin: { date: { pickerAppearance: 'dayAndTime' } }, ...auditField },
        { name: 'audit_notes', type: 'textarea', ...auditField },
      ],
    },
    { name: 'internal_notes', type: 'textarea', access: { create: staffOnly, update: staffOnly, read: staffOnly }, admin: { position: 'sidebar' } },
  ],
  hooks: {
    beforeChange: [
      ({ data, operation, req }) => {
        if (operation === 'create') {
          if (data.type === 'website_audit' && (!data.audit_status || data.audit_status === 'none')) {
            data.audit_status = 'queued'
          }
          const fwd = req.headers?.get?.('x-forwarded-for')
          if (fwd) data.ip = fwd.split(',')[0]?.trim()
        }
        return data
      },
    ],
    afterChange: [sendLeadWebhook],
  },
  timestamps: true,
}
