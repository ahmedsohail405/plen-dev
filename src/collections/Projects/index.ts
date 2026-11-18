import type { CollectionConfig } from 'payload'
import { slugField } from 'payload'

import { anyone } from '../../access/anyone'
import { authenticated } from '../../access/authenticated'
import { generatePreviewPath } from '@/utilities/generatePreviewPath'
import { revalidateTagHook } from '@/hooks/revalidateTagHook'

export const Projects: CollectionConfig<'projects'> = {
  slug: 'projects',
  labels: { singular: 'Project', plural: 'Portfolio' },
  access: { create: authenticated, delete: authenticated, read: anyone, update: authenticated },
  admin: {
    useAsTitle: 'title',
    group: 'Content',
    defaultColumns: ['title', 'industry', 'featured', 'order'],
    livePreview: {
      url: ({ data, req }) => generatePreviewPath({ collection: 'projects', slug: data?.slug, req }),
    },
  },
  defaultSort: 'order',
  defaultPopulate: { title: true, slug: true, industry: true, summary: true, cover: true, accent: true, video: true, liveUrl: true, domain: true, location: true, year: true, results: true, featured: true },
  fields: [
    { name: 'title', type: 'text', required: true, admin: { description: 'Client / brand name' } },
    {
      type: 'row',
      fields: [
        { name: 'industry', type: 'text', required: true },
        { name: 'location', type: 'text' },
        { name: 'year', type: 'text' },
      ],
    },
    { name: 'summary', type: 'textarea', required: true },
    {
      type: 'row',
      fields: [
        { name: 'cover', type: 'upload', relationTo: 'media' },
        { name: 'video', type: 'upload', relationTo: 'media', admin: { description: 'Screen-recorded walkthrough (mp4/webm)' } },
      ],
    },
    {
      type: 'row',
      fields: [
        { name: 'liveUrl', type: 'text', admin: { description: 'Link to the live site' } },
        { name: 'domain', type: 'text', admin: { description: 'Shown in the browser bar on cards, e.g. brightdental.com' } },
        { name: 'accent', type: 'text', defaultValue: '#7c5cff', admin: { description: 'Brand colour used on cards' } },
      ],
    },
    { name: 'services', type: 'array', fields: [{ name: 'service', type: 'text' }] },
    {
      name: 'results',
      type: 'array',
      maxRows: 4,
      fields: [
        {
          type: 'row',
          fields: [
            { name: 'value', type: 'text', required: true },
            { name: 'label', type: 'text', required: true },
          ],
        },
      ],
    },
    { name: 'challenge', type: 'textarea' },
    { name: 'solution', type: 'textarea' },
    {
      type: 'row',
      fields: [
        { name: 'featured', type: 'checkbox' },
        { name: 'order', type: 'number', defaultValue: 10 },
      ],
    },
    {
      name: 'meta',
      type: 'group',
      label: 'SEO',
      fields: [
        { name: 'title', type: 'text' },
        { name: 'description', type: 'textarea' },
      ],
    },
    slugField(),
  ],
  hooks: { afterChange: [revalidateTagHook('projects')] },
  versions: { drafts: { autosave: { interval: 200 } } },
}
