import { createLocalReq, getPayload } from 'payload'
import config from '@payload-config'
import { seed } from '../src/endpoints/seed'

/** pnpm seed — seeds content; also creates a first admin when SEED_ADMIN_EMAIL/PASSWORD are set and no users exist. */
const payload = await getPayload({ config })
const { totalDocs } = await payload.count({ collection: 'users', overrideAccess: true })
if (!totalDocs && process.env.SEED_ADMIN_EMAIL && process.env.SEED_ADMIN_PASSWORD) {
  await payload.create({ collection: 'users', overrideAccess: true, data: { email: process.env.SEED_ADMIN_EMAIL, password: process.env.SEED_ADMIN_PASSWORD, name: 'Admin', role: 'admin' } })
  payload.logger.info(`Created admin ${process.env.SEED_ADMIN_EMAIL}`)
}
const req = await createLocalReq({}, payload)
await seed({ payload, req })
process.exit(0)
