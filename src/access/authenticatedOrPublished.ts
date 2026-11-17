import type { Access } from 'payload'

export const authenticatedOrPublished: Access = ({ req: { user } }) => {
  if (user && (user as { role?: string }).role !== 'service') {
    return true
  }

  return {
    _status: {
      equals: 'published',
    },
  }
}
