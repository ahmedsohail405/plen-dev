import type { CollectionConfig } from 'payload'
import crypto from 'crypto'

import { authenticated, isAdmin } from '../../access/authenticated'

export const SERVICE_EMAIL = 'audit-agent@service.plendev.local'

const safeEqual = (a: string, b: string) => {
  const ab = Buffer.from(a)
  const bb = Buffer.from(b)
  return ab.length === bb.length && crypto.timingSafeEqual(ab, bb)
}

export const Users: CollectionConfig = {
  slug: 'users',
  access: {
    admin: authenticated,
    create: isAdmin,
    delete: isAdmin,
    read: authenticated,
    update: ({ req, id }) => isAdmin({ req } as never) || req.user?.id === id,
  },
  admin: {
    defaultColumns: ['name', 'email', 'role'],
    useAsTitle: 'name',
    group: 'Settings',
  },
  auth: {
    strategies: [
      {
        // Lets the audit/SEO agent call the REST API with
        // `Authorization: Bearer <CMS_API_TOKEN>`. It acts as a "service" user
        // that can only read/update leads (see access/authenticated.ts).
        name: 'bearer-service-token',
        authenticate: async ({ headers, payload }) => {
          const token = process.env.CMS_API_TOKEN
          const header = headers.get('authorization') || ''
          if (!token || !header.startsWith('Bearer ')) return { user: null }
          if (!safeEqual(header.slice(7).trim(), token)) return { user: null }

          let found = await payload.find({
            collection: 'users',
            where: { email: { equals: SERVICE_EMAIL } },
            limit: 1,
            overrideAccess: true,
          })
          let user = found.docs[0]
          if (!user) {
            user = await payload.create({
              collection: 'users',
              overrideAccess: true,
              data: {
                email: SERVICE_EMAIL,
                name: 'Audit agent (API)',
                role: 'service',
                password: crypto.randomBytes(32).toString('hex'),
              },
            })
          }
          return { user: { ...user, collection: 'users', _strategy: 'bearer-service-token' } }
        },
      },
    ],
  },
  fields: [
    {
      name: 'name',
      type: 'text',
    },
    {
      name: 'role',
      type: 'select',
      required: true,
      defaultValue: 'editor',
      saveToJWT: true,
      options: [
        { label: 'Admin', value: 'admin' },
        { label: 'Editor', value: 'editor' },
        { label: 'Service (API only)', value: 'service' },
      ],
      access: {
        update: ({ req }) => (req.user as { role?: string } | null)?.role === 'admin',
      },
    },
  ],
  hooks: {
    beforeChange: [
      async ({ data, operation, req }) => {
        // The very first account created is always an admin.
        if (operation === 'create') {
          const { totalDocs } = await req.payload.count({ collection: 'users', overrideAccess: true })
          if (totalDocs === 0) data.role = 'admin'
        }
        return data
      },
    ],
  },
  timestamps: true,
}
