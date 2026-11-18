import type { MetadataRoute } from 'next'

import { getSettings } from '@/lib/data'
import { SITE } from '@/lib/schema'

export const revalidate = 3600

const AI_BOTS = ['GPTBot', 'OAI-SearchBot', 'ChatGPT-User', 'ClaudeBot', 'Claude-SearchBot', 'Claude-User', 'PerplexityBot', 'Perplexity-User', 'Google-Extended', 'Applebot-Extended', 'CCBot', 'Bytespider', 'Meta-ExternalAgent']

export default async function robots(): Promise<MetadataRoute.Robots> {
  const s = await getSettings()
  if (s.noindexSite) return { rules: [{ userAgent: '*', disallow: '/' }] }
  const disallow = ['/admin', '/api', '/next/', '/forms/', '/search']
  return {
    rules: [
      { userAgent: '*', allow: '/', disallow },
      { userAgent: AI_BOTS, ...(s.allowAiCrawlers === false ? { disallow: '/' } : { allow: ['/', '/llms.txt', '/llms-full.txt'], disallow }) },
    ],
    sitemap: `${SITE()}/sitemap.xml`,
    host: SITE(),
  }
}
