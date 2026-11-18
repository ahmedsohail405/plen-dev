import type { Metadata } from 'next'
import { getServerSideURL } from './getURL'

const defaultOpenGraph: Metadata['openGraph'] = {
  type: 'website',
  description: 'Plen Dev designs and builds fast, creative websites with an easy custom CMS for businesses in Brooklyn, Queens, NYC and Long Island.',
  images: [{ url: `${getServerSideURL()}/og.png`, width: 1200, height: 630 }],
  siteName: 'Plen Dev',
  title: 'Plen Dev — Web design & development in New York',
  locale: 'en_US',
}

export const mergeOpenGraph = (og?: Metadata['openGraph']): Metadata['openGraph'] => ({
  ...defaultOpenGraph,
  ...og,
  images: og?.images ? og.images : defaultOpenGraph.images,
})
