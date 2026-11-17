import type { Field } from 'payload'

/** Extra SEO controls appended to the SEO tab of pages and posts. */
export const seoExtras: Field[] = [
  {
    type: 'row',
    fields: [
      { name: 'canonical', type: 'text', admin: { width: '60%', description: 'Leave empty to use this page’s own URL.' } },
      { name: 'noindex', type: 'checkbox', label: 'Hide from search engines (noindex)', admin: { width: '40%', style: { alignSelf: 'center' } } },
    ],
  },
  { name: 'keywords', type: 'text', admin: { description: 'Primary keyword first, comma separated. Used for internal tracking and the llms.txt summary (not a ranking factor).' } },
  {
    name: 'schemaType',
    type: 'select',
    defaultValue: 'WebPage',
    options: ['WebPage', 'Service', 'AboutPage', 'ContactPage', 'CollectionPage', 'FAQPage'].map((v) => ({ label: v, value: v })),
  },
  {
    name: 'schemaJson',
    label: 'Custom schema (JSON-LD)',
    type: 'code',
    admin: { language: 'json', description: 'Optional extra structured data. Paste a JSON object or array, without <script> tags.' },
  },
]
