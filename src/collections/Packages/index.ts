import type { CollectionConfig } from 'payload'

import { anyone } from '../../access/anyone'
import { authenticated } from '../../access/authenticated'
import { revalidateTagHook } from '@/hooks/revalidateTagHook'

export const PACKAGE_GROUPS = [
  { label: 'Websites', value: 'websites' },
  { label: 'Ecommerce', value: 'ecommerce' },
  { label: 'Custom CMS & Web Apps', value: 'cms-apps' },
  { label: 'SEO', value: 'seo' },
  { label: 'Care Plans', value: 'care' },
  { label: 'Add-ons', value: 'addons' },
]

export const Packages: CollectionConfig = {
  slug: 'packages',
  access: { create: authenticated, delete: authenticated, read: anyone, update: authenticated },
  admin: {
    useAsTitle: 'name',
    group: 'Content',
    defaultColumns: ['name', 'group', 'price', 'billing', 'order'],
    description: 'Shown on the Packages page and any Packages block. Drag order with the "Order" number.',
  },
  defaultSort: 'order',
  fields: [
    {
      type: 'row',
      fields: [
        { name: 'name', type: 'text', required: true },
        { name: 'group', type: 'select', required: true, options: PACKAGE_GROUPS },
        { name: 'order', type: 'number', defaultValue: 10, admin: { width: '15%' } },
      ],
    },
    {
      type: 'row',
      fields: [
        { name: 'price', type: 'number', admin: { description: 'In USD. Leave empty for "Custom quote".' } },
        { name: 'pricePrefix', type: 'text', admin: { placeholder: 'From' } },
        {
          name: 'billing',
          type: 'select',
          defaultValue: 'one-time',
          options: [
            { label: 'One-time', value: 'one-time' },
            { label: 'Per month', value: 'monthly' },
            { label: 'Each', value: 'each' },
            { label: 'Per page', value: 'per-page' },
          ],
        },
        { name: 'priceNote', type: 'text', admin: { placeholder: 'e.g. $499 to $1,499' } },
      ],
    },
    { name: 'tagline', type: 'text', admin: { description: 'Short line, e.g. "Best for new businesses"' } },
    {
      type: 'row',
      fields: [
        { name: 'scope', type: 'text', admin: { placeholder: 'Up to 12 pages' } },
        { name: 'timeline', type: 'text', admin: { placeholder: '4-week delivery' } },
      ],
    },
    {
      name: 'features',
      type: 'array',
      fields: [{ name: 'feature', type: 'text', required: true }],
      admin: { initCollapsed: false },
    },
    {
      type: 'row',
      fields: [
        { name: 'highlighted', type: 'checkbox', label: 'Highlight as most popular' },
        { name: 'ctaLabel', type: 'text', defaultValue: 'Get started' },
      ],
    },
  ],
  hooks: { afterChange: [revalidateTagHook('packages')] },
}
