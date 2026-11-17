import type { GlobalConfig } from 'payload'

import { authenticated } from '../../access/authenticated'
import { codeSnippets } from '@/fields/codeSnippets'
import { revalidateTagHook } from '@/hooks/revalidateTagHook'

export const SiteSettings: GlobalConfig = {
  slug: 'site-settings',
  label: 'Site Settings',
  admin: { group: 'Settings' },
  access: { read: () => true, update: authenticated },
  fields: [
    {
      type: 'tabs',
      tabs: [
        {
          label: 'Business',
          description: 'Used in the footer, contact page, schema markup (Google + AI tools) and llms.txt. Keep it identical to your Google Business Profile.',
          fields: [
            {
              type: 'row',
              fields: [
                { name: 'businessName', type: 'text', defaultValue: 'Plen Dev', required: true },
                { name: 'legalName', type: 'text' },
              ],
            },
            { name: 'tagline', type: 'text', defaultValue: 'Web design & development studio in New York' },
            { name: 'description', type: 'textarea', admin: { description: 'One plain-language paragraph about the company. AI tools quote this.' } },
            {
              type: 'row',
              fields: [
                { name: 'phone', type: 'text' },
                { name: 'email', type: 'email' },
              ],
            },
            {
              name: 'address',
              type: 'group',
              fields: [
                {
                  type: 'row',
                  fields: [
                    { name: 'street', type: 'text' },
                    { name: 'city', type: 'text', defaultValue: 'Brooklyn' },
                    { name: 'region', type: 'text', defaultValue: 'NY' },
                    { name: 'postalCode', type: 'text' },
                  ],
                },
                { name: 'hideStreet', type: 'checkbox', label: 'Service-area business (hide street address)', defaultValue: true },
              ],
            },
            {
              name: 'areasServed',
              type: 'array',
              admin: { description: 'Listed in schema as areaServed.' },
              fields: [{ name: 'area', type: 'text', required: true }],
            },
            { name: 'hours', type: 'text', defaultValue: 'Mo-Fr 09:00-18:00' },
            {
              name: 'social',
              type: 'array',
              fields: [
                {
                  type: 'row',
                  fields: [
                    { name: 'platform', type: 'text', required: true },
                    { name: 'url', type: 'text', required: true },
                  ],
                },
              ],
            },
            { name: 'logo', type: 'upload', relationTo: 'media' },
          ],
        },
        {
          label: 'SEO defaults',
          fields: [
            { name: 'titleSuffix', type: 'text', defaultValue: ' | Plen Dev', admin: { description: 'Appended to every page title.' } },
            { name: 'defaultDescription', type: 'textarea' },
            { name: 'defaultOgImage', type: 'upload', relationTo: 'media' },
            {
              type: 'row',
              fields: [
                { name: 'googleVerification', type: 'text', label: 'Google Search Console verification code' },
                { name: 'bingVerification', type: 'text', label: 'Bing Webmaster verification code' },
              ],
            },
            {
              type: 'row',
              fields: [
                { name: 'ga4Id', type: 'text', label: 'Google Analytics 4 ID', admin: { placeholder: 'G-XXXXXXX' } },
                { name: 'gtmId', type: 'text', label: 'Google Tag Manager ID', admin: { placeholder: 'GTM-XXXXXX' } },
                { name: 'metaPixelId', type: 'text', label: 'Meta Pixel ID' },
              ],
            },
            {
              name: 'noindexSite',
              type: 'checkbox',
              label: 'Hide the whole site from search engines (staging)',
              defaultValue: false,
            },
          ],
        },
        {
          label: 'Header & custom code',
          description: 'Add as many snippets as you need: tracking, chat widgets, verification tags, extra schema. Each can run site-wide or on chosen pages. Pages also have their own code tab.',
          fields: [codeSnippets({ name: 'codeSnippets', label: 'Code snippets', withScope: true })],
        },
        {
          label: 'AI & crawlers',
          description: 'Controls robots.txt and /llms.txt, which AI tools such as ChatGPT, Claude, Perplexity and Gemini read.',
          fields: [
            { name: 'allowAiCrawlers', type: 'checkbox', defaultValue: true, label: 'Allow AI crawlers (GPTBot, ClaudeBot, PerplexityBot, Google-Extended…)' },
            { name: 'llmsIntro', type: 'textarea', label: 'llms.txt summary', admin: { description: 'A short summary placed at the top of /llms.txt.' } },
            {
              name: 'llmsFacts',
              type: 'array',
              label: 'Key facts for AI answers',
              fields: [{ name: 'fact', type: 'text', required: true }],
            },
            { name: 'robotsExtra', type: 'textarea', label: 'Extra robots.txt rules' },
          ],
        },
        {
          name: 'integrations',
          label: 'Leads & integrations',
          fields: [
            { name: 'leadWebhookEnabled', type: 'checkbox', defaultValue: true, label: 'Send new leads to the audit agent' },
            {
              name: 'leadWebhookUrl',
              type: 'text',
              label: 'Audit agent webhook URL',
              admin: { description: 'Leave empty to use the AUDIT_WEBHOOK_URL environment variable. Requests are signed with AUDIT_WEBHOOK_SECRET.' },
            },
          ],
        },
      ],
    },
  ],
  hooks: { afterChange: [revalidateTagHook('site-settings')] },
}
