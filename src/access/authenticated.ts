import type { AccessArgs } from 'payload'

import type { User } from '@/payload-types'

type isAuthenticated = (args: AccessArgs<User>) => boolean

/**
 * Staff = a logged-in human (admin or editor). The "service" role used by the
 * audit agent's API token is deliberately excluded so it can only touch leads.
 */
export const authenticated: isAuthenticated = ({ req: { user } }) => {
  return Boolean(user) && (user as User | null)?.role !== 'service'
}

export const isAdmin: isAuthenticated = ({ req: { user } }) =>
  (user as User | null)?.role === 'admin'

export const anyUser: isAuthenticated = ({ req: { user } }) => Boolean(user)
