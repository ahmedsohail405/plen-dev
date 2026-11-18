import type { Metadata, Viewport } from 'next'
import { GeistMono } from 'geist/font/mono'
import { GeistSans } from 'geist/font/sans'
import { Instrument_Serif } from 'next/font/google'
import { draftMode } from 'next/headers'
import React from 'react'

import { AdminBar } from '@/components/AdminBar'
import { CodeSnippets, type Snippet } from '@/components/studio/CodeSnippets'
import { Reveal } from '@/components/studio/Reveal'
import { Footer } from '@/Footer/Component'
import { Header } from '@/Header/Component'
import { getSettings } from '@/lib/data'
import { JsonLd, organizationSchema } from '@/lib/schema'
import { getServerSideURL } from '@/utilities/getURL'
import { mergeOpenGraph } from '@/utilities/mergeOpenGraph'

import './globals.css'
import './studio.css'

const serif = Instrument_Serif({ subsets: ['latin'], weight: '400', style: ['italic', 'normal'], variable: '--font-serif-display', display: 'swap' })

/** GA4 / GTM / Meta Pixel generated from the IDs in Site Settings → SEO defaults. */
const trackingSnippets = (s: Awaited<ReturnType<typeof getSettings>>): Snippet[] => {
  const out: Snippet[] = []
  if (s.gtmId)
    out.push(
      { placement: 'head', code: `<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);})(window,document,'script','dataLayer','${s.gtmId}');</script>` },
      { placement: 'bodyStart', code: `<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=${s.gtmId}" height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>` },
    )
  if (s.ga4Id)
    out.push({ placement: 'head', code: `<script async src="https://www.googletagmanager.com/gtag/js?id=${s.ga4Id}"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','${s.ga4Id}');</script>` })
  if (s.metaPixelId)
    out.push({ placement: 'head', code: `<script>!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');fbq('init','${s.metaPixelId}');fbq('track','PageView');</script>` })
  return out
}

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const { isEnabled } = await draftMode()
  const settings = await getSettings()
  // Only "All pages" snippets here; page-scoped ones render from each page.
  const siteWide = [...trackingSnippets(settings), ...((settings.codeSnippets || []) as Snippet[]).filter((s) => (s.scope || 'all') === 'all')]

  return (
    <html className={`studio ${GeistSans.variable} ${GeistMono.variable} ${serif.variable}`} lang="en" data-theme="light" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: "document.documentElement.classList.add('js')" }} />
        <link href="/favicon.svg" rel="icon" type="image/svg+xml" />
        <link href="/apple-touch-icon.png" rel="apple-touch-icon" />
        <link rel="alternate" type="text/plain" href="/llms.txt" title="LLM-readable summary" />
        <JsonLd data={organizationSchema(settings)} />
        <CodeSnippets snippets={siteWide} placement="head" />
      </head>
      <body>
        <CodeSnippets snippets={siteWide} placement="bodyStart" />
        <a href="#main" className="sr-only focus:not-sr-only">
          Skip to content
        </a>
        <AdminBar adminBarProps={{ preview: isEnabled }} />
        <Header />
        <main id="main">{children}</main>
        <Footer />
        <Reveal />
        <div className="grain" aria-hidden />
        <CodeSnippets snippets={siteWide} placement="bodyEnd" />
      </body>
    </html>
  )
}

export async function generateMetadata(): Promise<Metadata> {
  const s = await getSettings()
  return {
    metadataBase: new URL(getServerSideURL()),
    openGraph: mergeOpenGraph({ siteName: s.businessName }),
    twitter: { card: 'summary_large_image' },
    verification: {
      google: s.googleVerification || undefined,
      other: s.bingVerification ? { 'msvalidate.01': s.bingVerification } : undefined,
    },
    robots: s.noindexSite ? { index: false, follow: false } : undefined,
  }
}

export const viewport: Viewport = { themeColor: '#f3f0e8' }
