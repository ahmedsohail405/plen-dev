import type { NextConfig } from 'next'

export const redirects: NextConfig['redirects'] = async () => {
  const internetExplorerRedirect = {
    destination: '/ie-incompatible.html',
    has: [
      {
        type: 'header' as const,
        key: 'user-agent',
        value: '(.*Trident.*)', // all ie browsers
      },
    ],
    permanent: false,
    source: '/:path((?!ie-incompatible.html$).*)', // all pages except the incompatibility page
  }

  // Demo renamed from dental to medical practices
  const renamed = [
    { source: '/industries/dental', destination: '/industries/medical-practices', permanent: true },
    { source: '/work/lumen-pine-dental', destination: '/work/northbridge-medical', permanent: true },
    { source: '/showcase/lumen-pine-dental/:path*', destination: '/showcase/northbridge-medical/', permanent: true },
  ]

  return [internetExplorerRedirect, ...renamed]
}
