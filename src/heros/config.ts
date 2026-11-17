import type { Field } from 'payload'

import { linkGroup } from '@/fields/linkGroup'

export const hero: Field = {
  name: 'hero',
  type: 'group',
  label: false,
  fields: [
    {
      name: 'type',
      type: 'select',
      defaultValue: 'page',
      required: true,
      options: [
        { label: 'Studio (big creative homepage hero)', value: 'studio' },
        { label: 'Page header', value: 'page' },
        { label: 'None', value: 'none' },
      ],
    },
    { name: 'eyebrow', type: 'text', admin: { condition: (_, s) => s?.type !== 'none', placeholder: 'Brooklyn · Queens · NYC · Long Island' } },
    {
      name: 'title',
      label: 'H1 headline',
      type: 'text',
      admin: {
        condition: (_, s) => s?.type !== 'none',
        description: 'Wrap words in *asterisks* to give them the highlighted creative style. Leave empty to use the page title.',
      },
    },
    { name: 'subtitle', type: 'textarea', admin: { condition: (_, s) => s?.type !== 'none' } },
    {
      name: 'answer',
      label: 'Quick answer (for Google & AI)',
      type: 'textarea',
      admin: {
        condition: (_, s) => s?.type !== 'none',
        description: 'One or two plain sentences that directly answer what this page is about. Shown under the header and read by AI tools.',
      },
    },
    linkGroup({ overrides: { maxRows: 2, admin: { condition: (_: unknown, s: { type?: string }) => s?.type !== 'none' } } }),
    {
      name: 'media',
      type: 'upload',
      relationTo: 'media',
      admin: { condition: (_, s) => s?.type === 'page', description: 'Optional image on the right of the page header.' },
    },
    {
      name: 'showcase',
      type: 'relationship',
      relationTo: 'projects',
      hasMany: true,
      maxRows: 5,
      admin: { condition: (_, s) => s?.type === 'studio', description: 'Portfolio pieces floating in the hero.' },
    },
    {
      name: 'badges',
      type: 'array',
      maxRows: 4,
      admin: { condition: (_, s) => s?.type === 'studio' },
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
  ],
}
