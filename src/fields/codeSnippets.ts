import type { ArrayField } from 'payload'

/** Reusable "custom code" array: tracking pixels, verification tags, chat widgets, schema, etc. */
export const codeSnippets = (opts: { name: string; label: string; withScope?: boolean; description?: string }): ArrayField => ({
  name: opts.name,
  label: opts.label,
  type: 'array',
  admin: {
    initCollapsed: true,
    description: opts.description,
    components: { RowLabel: '@/fields/CodeSnippetRowLabel#CodeSnippetRowLabel' },
  },
  fields: [
    {
      type: 'row',
      fields: [
        { name: 'label', type: 'text', required: true, admin: { width: '40%', placeholder: 'e.g. Google Tag Manager' } },
        {
          name: 'placement',
          type: 'select',
          required: true,
          defaultValue: 'head',
          admin: { width: '30%' },
          options: [
            { label: 'Inside <head>', value: 'head' },
            { label: 'Start of <body>', value: 'bodyStart' },
            { label: 'End of <body>', value: 'bodyEnd' },
          ],
        },
        { name: 'enabled', type: 'checkbox', defaultValue: true, admin: { width: '30%', style: { alignSelf: 'center' } } },
      ],
    },
    ...(opts.withScope
      ? [
          {
            type: 'row' as const,
            fields: [
              {
                name: 'scope',
                type: 'select' as const,
                defaultValue: 'all',
                required: true,
                admin: { width: '40%' },
                options: [
                  { label: 'All pages', value: 'all' },
                  { label: 'Only selected pages', value: 'include' },
                  { label: 'All except selected pages', value: 'exclude' },
                ],
              },
              {
                name: 'pages',
                type: 'relationship' as const,
                relationTo: ['pages', 'posts'] as ('pages' | 'posts')[],
                hasMany: true,
                admin: { width: '60%', condition: (_: unknown, sib: { scope?: string }) => sib?.scope !== 'all' },
              },
            ],
          },
          {
            name: 'paths',
            type: 'text' as const,
            admin: {
              condition: (_: unknown, sib: { scope?: string }) => sib?.scope !== 'all',
              description: 'Optional: extra URL paths, comma separated. Use * as a wildcard, e.g. /services/*, /contact',
            },
          },
        ]
      : []),
    {
      name: 'code',
      type: 'code',
      required: true,
      admin: { language: 'html', description: 'Paste the full snippet including <script>, <meta>, <link> or <noscript> tags.' },
    },
  ],
})
