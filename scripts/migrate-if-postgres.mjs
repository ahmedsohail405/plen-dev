// Runs Payload database migrations before `next build` when DATABASE_URL is Postgres
// (Vercel / Neon). Locally on SQLite the schema is pushed in dev, so this is skipped.
import { execSync } from 'node:child_process'

if ((process.env.DATABASE_URL || '').startsWith('postgres')) {
  execSync('pnpm payload migrate', { stdio: 'inherit', env: { ...process.env, NODE_OPTIONS: '--no-deprecation' } })
} else {
  console.log('[migrate] DATABASE_URL is not Postgres, skipping migrations')
}
