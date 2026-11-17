import type { Block } from 'payload'

import { linkGroup } from '@/fields/linkGroup'
import { PACKAGE_GROUPS } from '@/collections/Packages'

const heading = [
  { name: 'eyebrow', type: 'text' as const },
  { name: 'heading', type: 'text' as const, admin: { description: 'Wrap words in *asterisks* to highlight them.' } },
  { name: 'intro', type: 'textarea' as const },
]

export const ICONS = [
  'code', 'palette', 'database', 'cart', 'search', 'sparkles', 'shield', 'gauge', 'layout', 'smartphone', 'map', 'bot', 'chart', 'wrench', 'tooth', 'home', 'heart', 'cpu',
].map((v) => ({ label: v, value: v }))

export const MarqueeBlock: Block = {
  slug: 'marquee',
  labels: { singular: 'Scrolling ticker', plural: 'Scrolling tickers' },
  fields: [
    { name: 'items', type: 'array', required: true, fields: [{ name: 'text', type: 'text', required: true }] },
    { name: 'style', type: 'select', defaultValue: 'outline', options: ['outline', 'solid', 'small'].map((v) => ({ label: v, value: v })) },
  ],
}

export const ServicesBlock: Block = {
  slug: 'services',
  labels: { singular: 'Services grid', plural: 'Services grids' },
  fields: [
    ...heading,
    {
      name: 'items',
      type: 'array',
      fields: [
        {
          type: 'row',
          fields: [
            { name: 'icon', type: 'select', options: ICONS, defaultValue: 'code' },
            { name: 'title', type: 'text', required: true },
          ],
        },
        { name: 'text', type: 'textarea' },
        { name: 'href', type: 'text', admin: { description: 'Link, e.g. /services/custom-cms' } },
      ],
    },
    { name: 'columns', type: 'select', defaultValue: '3', options: ['2', '3', '4'].map((v) => ({ label: v, value: v })) },
  ],
}

export const WorkBlock: Block = {
  slug: 'work',
  labels: { singular: 'Portfolio showcase', plural: 'Portfolio showcases' },
  fields: [
    ...heading,
    {
      name: 'source',
      type: 'select',
      defaultValue: 'featured',
      options: [
        { label: 'Featured projects', value: 'featured' },
        { label: 'All projects', value: 'all' },
        { label: 'Pick projects', value: 'pick' },
      ],
    },
    { name: 'projects', type: 'relationship', relationTo: 'projects', hasMany: true, admin: { condition: (_, s) => s?.source === 'pick' } },
    { name: 'style', type: 'select', defaultValue: 'stack', options: [{ label: 'Sticky stacked cards', value: 'stack' }, { label: 'Grid', value: 'grid' }] },
  ],
}

export const PackagesBlockConfig: Block = {
  slug: 'packagesBlock',
  labels: { singular: 'Packages & pricing', plural: 'Packages & pricing' },
  fields: [
    ...heading,
    { name: 'groups', type: 'select', hasMany: true, options: PACKAGE_GROUPS, admin: { description: 'Leave empty to show all groups as tabs.' } },
    { name: 'note', type: 'textarea', admin: { description: 'Small print under the packages (payment terms etc.)' } },
  ],
}

export const ProcessBlock: Block = {
  slug: 'process',
  labels: { singular: 'Process steps', plural: 'Process steps' },
  fields: [...heading, { name: 'steps', type: 'array', fields: [{ name: 'title', type: 'text', required: true }, { name: 'text', type: 'textarea' }, { name: 'duration', type: 'text' }] }],
}

export const StatsBlock: Block = {
  slug: 'stats',
  labels: { singular: 'Stats', plural: 'Stats' },
  fields: [...heading, { name: 'items', type: 'array', maxRows: 4, fields: [{ type: 'row', fields: [{ name: 'value', type: 'text', required: true }, { name: 'label', type: 'text', required: true }] }] }],
}

export const TestimonialsBlock: Block = {
  slug: 'testimonials',
  labels: { singular: 'Testimonials', plural: 'Testimonials' },
  fields: [
    ...heading,
    {
      name: 'items',
      type: 'array',
      fields: [
        { name: 'quote', type: 'textarea', required: true },
        { type: 'row', fields: [{ name: 'name', type: 'text', required: true }, { name: 'role', type: 'text' }, { name: 'company', type: 'text' }] },
        { name: 'rating', type: 'number', min: 1, max: 5, defaultValue: 5 },
      ],
    },
  ],
}

export const FaqBlock: Block = {
  slug: 'faq',
  labels: { singular: 'FAQ', plural: 'FAQs' },
  fields: [
    ...heading,
    {
      name: 'items',
      type: 'array',
      admin: { description: 'Automatically published as FAQPage schema for Google and AI answers.' },
      fields: [{ name: 'question', type: 'text', required: true }, { name: 'answer', type: 'textarea', required: true }],
    },
  ],
}

export const LeadFormBlock: Block = {
  slug: 'leadForm',
  labels: { singular: 'Lead form', plural: 'Lead forms' },
  fields: [
    {
      name: 'formType',
      type: 'select',
      defaultValue: 'website_audit',
      required: true,
      options: [
        { label: 'Free website audit', value: 'website_audit' },
        { label: 'Contact', value: 'contact' },
        { label: 'Quote / project brief', value: 'quote' },
      ],
    },
    ...heading,
    { name: 'bullets', type: 'array', fields: [{ name: 'text', type: 'text', required: true }] },
    { name: 'submitLabel', type: 'text', defaultValue: 'Send' },
    { name: 'successMessage', type: 'textarea', defaultValue: "Thanks! We've got it and will be in touch within one business day." },
    { name: 'anchor', type: 'text', admin: { description: 'Optional id so buttons can link to #anchor' } },
  ],
}

export const AreasBlock: Block = {
  slug: 'areas',
  labels: { singular: 'Areas served', plural: 'Areas served' },
  fields: [
    ...heading,
    {
      name: 'areas',
      type: 'array',
      fields: [
        { type: 'row', fields: [{ name: 'name', type: 'text', required: true }, { name: 'href', type: 'text' }] },
        { name: 'neighborhoods', type: 'text', admin: { description: 'Comma separated' } },
      ],
    },
  ],
}

export const StatementBlock: Block = {
  slug: 'statement',
  labels: { singular: 'Big statement', plural: 'Big statements' },
  fields: [
    { name: 'text', type: 'textarea', required: true, admin: { description: 'Large display text. Wrap words in *asterisks* to highlight.' } },
    linkGroup({ overrides: { maxRows: 2 } }),
  ],
}
