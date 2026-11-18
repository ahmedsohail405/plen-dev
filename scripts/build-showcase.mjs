// Builds the portfolio demo sites: showcase-src/<slug>.html -> public/showcase/<slug>/index.html
// Replaces {{i:icon-name}} with inline Lucide SVG icons (so nothing depends on emoji fonts).
import fs from 'fs'
import path from 'path'

const root = path.resolve(import.meta.dirname, '..')
const src = path.join(root, 'showcase-src')
const icons = path.join(root, 'node_modules/lucide-static/icons')

for (const f of fs.readdirSync(src).filter((f) => f.endsWith('.html'))) {
  const slug = f.replace(/\.html$/, '')
  let html = fs.readFileSync(path.join(src, f), 'utf8')
  html = html.replace(/\{\{i:([a-z0-9-]+)(?::(\d+))?\}\}/g, (_, name, size) => {
    const file = path.join(icons, `${name}.svg`)
    if (!fs.existsSync(file)) throw new Error(`Unknown icon ${name} in ${f}`)
    let svg = fs.readFileSync(file, 'utf8').replace(/<!--[\s\S]*?-->/g, '').trim()
    if (size) svg = svg.replace(/width="24"/, `width="${size}"`).replace(/height="24"/, `height="${size}"`)
    return svg.replace('<svg', '<svg aria-hidden="true"')
  })
  const out = path.join(root, 'public/showcase', slug)
  fs.mkdirSync(out, { recursive: true })
  fs.writeFileSync(path.join(out, 'index.html'), html)
  console.log('built', slug)
}
