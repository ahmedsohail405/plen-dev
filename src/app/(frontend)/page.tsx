import PageTemplate, { generateMetadata as gm } from './[...slug]/page'

export default function Home() {
  return <PageTemplate params={Promise.resolve({ slug: [] })} />
}

export const generateMetadata = () => gm({ params: Promise.resolve({ slug: [] }) })
