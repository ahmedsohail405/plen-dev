import type { Package, SiteSetting } from '@/payload-types'
import { getServerSideURL } from '@/utilities/getURL'

export const SITE = () => getServerSideURL().replace(/\/$/, '')

export const orgId = () => `${SITE()}/#organization`

/** ProfessionalService + WebSite graph, rendered on every page. */
export const organizationSchema = (s: SiteSetting) => {
  const url = SITE()
  const addr = s.address || {}
  const logo = s.logo && typeof s.logo === 'object' && s.logo.url ? url + s.logo.url : `${url}/favicon.svg`
  return {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': ['ProfessionalService', 'LocalBusiness'],
        '@id': orgId(),
        name: s.businessName,
        legalName: s.legalName || undefined,
        description: s.description || s.tagline || undefined,
        slogan: s.tagline || undefined,
        url,
        logo,
        image: logo,
        email: s.email || undefined,
        telephone: s.phone || undefined,
        priceRange: '$$',
        openingHours: s.hours || undefined,
        address: {
          '@type': 'PostalAddress',
          streetAddress: addr.hideStreet ? undefined : addr.street || undefined,
          addressLocality: addr.city || undefined,
          addressRegion: addr.region || undefined,
          postalCode: addr.postalCode || undefined,
          addressCountry: 'US',
        },
        areaServed: (s.areasServed || []).map((a) => ({ '@type': 'Place', name: a.area })),
        sameAs: (s.social || []).map((x) => x.url),
        knowsAbout: ['Web design', 'Web development', 'Custom CMS development', 'Ecommerce development', 'Local SEO', 'AI search optimization'],
      },
      {
        '@type': 'WebSite',
        '@id': `${url}/#website`,
        url,
        name: s.businessName,
        publisher: { '@id': orgId() },
        inLanguage: 'en-US',
      },
    ],
  }
}

export const breadcrumbSchema = (crumbs: { name: string; path: string }[]) => ({
  '@context': 'https://schema.org',
  '@type': 'BreadcrumbList',
  itemListElement: crumbs.map((c, i) => ({ '@type': 'ListItem', position: i + 1, name: c.name, item: SITE() + c.path })),
})

export const faqSchema = (items: { question: string; answer: string }[]) => ({
  '@context': 'https://schema.org',
  '@type': 'FAQPage',
  mainEntity: items.map((i) => ({ '@type': 'Question', name: i.question, acceptedAnswer: { '@type': 'Answer', text: i.answer } })),
})

const billingUnit: Record<string, string | undefined> = { monthly: 'MON', 'one-time': undefined, each: undefined, 'per-page': undefined }

export const offerCatalogSchema = (pkgs: Package[], groupLabel: (g: string) => string) => {
  const groups = Array.from(new Set(pkgs.map((p) => p.group)))
  return {
    '@context': 'https://schema.org',
    '@type': 'OfferCatalog',
    name: 'Plen Dev packages and pricing',
    url: `${SITE()}/packages`,
    itemListElement: groups.map((g) => ({
      '@type': 'OfferCatalog',
      name: groupLabel(g),
      itemListElement: pkgs
        .filter((p) => p.group === g)
        .map((p) => ({
          '@type': 'Offer',
          name: p.name,
          description: [p.tagline, ...(p.features || []).map((f) => f.feature)].filter(Boolean).join('. '),
          priceCurrency: 'USD',
          ...(p.price != null
            ? billingUnit[p.billing || '']
              ? { priceSpecification: { '@type': 'UnitPriceSpecification', price: p.price, priceCurrency: 'USD', unitCode: billingUnit[p.billing || ''] } }
              : { price: p.price }
            : {}),
          itemOffered: { '@type': 'Service', name: p.name, provider: { '@id': orgId() } },
          seller: { '@id': orgId() },
        })),
    })),
  }
}

export const JsonLd = ({ data }: { data: unknown }) => (
  <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(data).replace(/</g, '\\u003c') }} />
)
