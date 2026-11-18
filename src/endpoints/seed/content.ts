/* eslint-disable */
// Seed content for Plen Dev. Keyword targets come from
// /mnt/project-files/plen-dev/keywords-and-packages.md (one primary keyword per page).
// Everything here is editable afterwards in the CMS.

type Block = Record<string, unknown> & { blockType: string }
export type PageSeed = {
  title: string
  slug: string
  parent?: string // slug of parent page
  hero: Record<string, unknown>
  layout: Block[]
  meta: { title: string; description: string; keywords?: string; schemaType?: string }
}

const link = (label: string, url: string) => ({ link: { type: 'custom', url, label, newTab: false } })

/* ---------------- shared sections ---------------- */

export const SERVICE_ITEMS = [
  { icon: 'code', title: 'Custom web development', text: 'Hand-built Next.js websites that load in under two seconds and are easy to grow.', href: '/services/web-development' },
  { icon: 'palette', title: 'Website design', text: 'Creative, conversion-focused design with motion that feels like your brand, not a template.', href: '/services/web-design' },
  { icon: 'database', title: 'Custom CMS', text: 'Edit text and photos with live preview, collect leads, manage SEO and tracking code without a developer.', href: '/services/custom-cms' },
  { icon: 'cart', title: 'Ecommerce', text: 'Shopify or custom stores with fast checkout, product filters and inventory that syncs.', href: '/services/ecommerce' },
  { icon: 'layout', title: 'Web apps & portals', text: 'Client portals, booking systems, dashboards and internal tools built on the same stack.', href: '/services/web-apps' },
  { icon: 'shield', title: 'Care plans', text: 'Hosting, backups, security updates and monthly edits so your site never goes stale.', href: '/services/website-maintenance' },
]

export const servicesBlock = (opts: Partial<Block> = {}): Block => ({
  blockType: 'services',
  eyebrow: 'What we build',
  heading: 'One studio for the *whole* website',
  intro: 'Design, development and the CMS your team edits every day. No hand-offs between agencies, no templates bought off a marketplace.',
  items: SERVICE_ITEMS,
  columns: '3',
  ...opts,
})

export const processBlock = (dark = true): Block => ({
  blockType: 'process',
  dark,
  eyebrow: 'How it works',
  heading: 'From first call to *launch* in weeks, not months',
  intro: 'A fixed scope, a fixed price and a clickable preview of your site at every step.',
  steps: [
    { title: 'Discover', text: 'A 30-minute call and a free audit of your current site. We agree pages, features and a fixed quote.', duration: 'Week 1' },
    { title: 'Design', text: 'You get a live, clickable design of your homepage and key pages to review on your phone.', duration: 'Week 1–2' },
    { title: 'Build', text: 'We build on Next.js with the Plen CMS, move your content in and wire up forms, tracking and schema.', duration: 'Week 2–4' },
    { title: 'Launch & train', text: 'We launch, submit your sitemap to Google and train your team on the CMS in a 45-minute session.', duration: 'Week 4+' },
  ],
})

export const AREAS = [
  { name: 'Brooklyn', href: '/locations/brooklyn', neighborhoods: 'Williamsburg, Park Slope, DUMBO, Bay Ridge, Bushwick, Downtown Brooklyn' },
  { name: 'Queens', href: '/locations/queens', neighborhoods: 'Astoria, Long Island City, Flushing, Forest Hills, Jamaica, Bayside' },
  { name: 'New York City', href: '/locations/new-york-city', neighborhoods: 'Manhattan, the Bronx, Staten Island and all five boroughs' },
  { name: 'Long Island', href: '/locations/long-island', neighborhoods: 'Nassau County and Suffolk County: Garden City, Hicksville, Huntington, Smithtown' },
]

export const areasBlock = (opts: Partial<Block> = {}): Block => ({
  blockType: 'areas',
  eyebrow: 'Where we work',
  heading: 'Local to *New York*',
  intro: 'We meet clients in person across the city and Long Island, and work remotely with everyone else.',
  areas: AREAS,
  ...opts,
})

export const auditBlock = (opts: Partial<Block> = {}): Block => ({
  blockType: 'leadForm',
  formType: 'website_audit',
  dark: true,
  eyebrow: 'Free website audit',
  heading: 'Is your website *costing* you customers?',
  intro: 'Send us your URL. We check speed, mobile layout, search visibility and conversion and email you a plain-English report with the fixes that matter most.',
  bullets: [
    { text: 'Page speed and Core Web Vitals on mobile' },
    { text: 'Google and AI-search readiness (titles, schema, indexing)' },
    { text: 'Broken links, forms and accessibility issues' },
    { text: 'A prioritized fix list, no obligation' },
  ],
  submitLabel: 'Get my free audit',
  successMessage: "Thanks! Your audit is in the queue. We'll review it personally and email your report within one business day.",
  anchor: 'audit',
  ...opts,
})

export const statementBlock = (text: string, dark = false): Block => ({
  blockType: 'statement',
  dark,
  text,
  links: [link('Start a project', '/contact'), link('See packages', '/packages')],
})

export const marquee = (items: string[], style = 'outline'): Block => ({ blockType: 'marquee', style, items: items.map((text) => ({ text })) })

const faq = (heading: string, items: [string, string][], intro?: string): Block => ({
  blockType: 'faq',
  eyebrow: 'FAQ',
  heading,
  intro,
  items: items.map(([question, answer]) => ({ question, answer })),
})

const workBlock = (opts: Partial<Block> = {}): Block => ({
  blockType: 'work',
  eyebrow: 'Selected work',
  heading: 'Sites that look like the *business* they sell',
  intro: 'Every project is designed from scratch around the client’s customers, then handed over with a CMS their team actually uses.',
  source: 'featured',
  style: 'stack',
  ...opts,
})

const contactForm = (opts: Partial<Block> = {}): Block => ({
  blockType: 'leadForm',
  formType: 'quote',
  eyebrow: 'Start a project',
  heading: 'Tell us what you’re *building*',
  intro: 'Share a few details and we’ll reply within one business day with questions, a rough timeline and a price range.',
  bullets: [{ text: 'Fixed quotes, no hourly surprises' }, { text: 'You own your code, content and domain' }, { text: 'In-person meetings in NYC and Long Island' }],
  submitLabel: 'Send project details',
  successMessage: "Thanks! We've got your brief and will reply within one business day.",
  anchor: 'contact',
  dark: true,
  ...opts,
})

/* ---------------- pages ---------------- */

const home: PageSeed = {
  title: 'Home',
  slug: 'home',
  hero: {
    type: 'studio',
    eyebrow: 'Web design & development studio · New York',
    title: 'Websites that *win* customers in New York',
    subtitle: 'Plen Dev designs and builds fast, creative websites for businesses in Brooklyn, Queens, NYC and Long Island, with a CMS your team can edit in minutes.',
    answer: 'Plen Dev is a New York web development company. We build custom Next.js websites, online stores and web apps with a built-in CMS (live preview editing, lead inbox, SEO and tracking settings), starting at $1,499.',
    links: [link('Get a free website audit', '/website-audit'), link('See our work', '/work')],
    badges: [
      { value: '2–6 wk', label: 'typical launch time' },
      { value: '$1,499', label: 'websites from' },
      { value: '<2.5s', label: 'mobile load target' },
      { value: '100%', label: 'of sites include the CMS' },
    ],
  },
  layout: [
    marquee(['Web design', 'Development', 'Custom CMS', 'Ecommerce', 'Web apps', 'Brooklyn', 'Queens', 'Long Island']),
    servicesBlock(),
    workBlock(),
    {
      blockType: 'stats',
      eyebrow: 'Built in, not bolted on',
      heading: 'Every site ships with the *Plen CMS*',
      intro: 'No plugins to update, no page builder slowing you down. Your team edits text and photos with a live preview, sees every lead in one inbox and controls SEO and tracking code page by page.',
      items: [
        { value: 'Live', label: 'preview while you edit' },
        { value: '1', label: 'inbox for every form lead' },
        { value: '∞', label: 'header code snippets, site-wide or per page' },
        { value: 'AI', label: 'readable: schema, sitemap & llms.txt' },
      ],
    },
    processBlock(true),
    {
      blockType: 'packagesBlock',
      eyebrow: 'Packages',
      heading: 'Clear prices, *no* surprises',
      intro: 'Fixed-price website packages for New York small businesses. Every package includes the Plen CMS, mobile design and on-page SEO.',
      groups: ['websites'],
      note: 'Need a store, portal or something bigger? See all packages, including ecommerce, custom CMS and monthly care plans.',
    },
    areasBlock(),
    faq('Questions we hear *every* week', [
      ['How much does a website cost in New York?', 'Most small business websites we build cost between $1,499 and $6,999 as a one-time project. Ecommerce stores start at $2,999, and larger custom platforms start at $12,000. You get a fixed quote before any work starts.'],
      ['How long does it take to build a website?', 'A 5-page Launch site takes about 2 weeks. A 12-page custom Growth site takes about 4 weeks. Bigger sites with booking, ecommerce or integrations usually take 6 to 10 weeks.'],
      ['Can I edit the website myself?', 'Yes. Every site comes with the Plen CMS. You click a page, change text or swap a photo, see the result in a live preview and publish. No code and no page-builder plugins.'],
      ['Do you only work with businesses in NYC?', 'Our clients are mostly in Brooklyn, Queens, Manhattan and Long Island, and we meet in person when it helps. We also build for businesses anywhere in the US.'],
      ['Will my website show up in Google and AI tools like ChatGPT?', 'Every site is built with clean, server-rendered HTML, schema markup, a sitemap and an llms.txt file so search engines and AI assistants can read it. We set up Google Search Console and Analytics at launch.'],
    ]),
    auditBlock(),
  ],
  meta: {
    title: 'Web Design & Development Company in NYC | Plen Dev',
    description: 'Plen Dev builds fast, creative websites with an easy custom CMS for businesses in Brooklyn, Queens, NYC and Long Island. Websites from $1,499.',
    keywords: 'web design company NYC, web development company New York, custom website development NYC',
    schemaType: 'WebPage',
  },
}

/* ---- services ---- */
const servicesHub: PageSeed = {
  title: 'Services',
  slug: 'services',
  hero: { type: 'page', eyebrow: 'Services', title: 'Everything your website needs, *under one roof*', subtitle: 'Design, development, a custom CMS and ongoing care, from one New York studio.', links: [link('Get a quote', '/contact'), link('See packages', '/packages')] },
  layout: [servicesBlock({ eyebrow: undefined, heading: undefined, intro: undefined }), processBlock(true), auditBlock()],
  meta: { title: 'Web Design & Development Services NYC | Plen Dev', description: 'Custom web development, website design, custom CMS, ecommerce, web apps and website care plans for New York businesses.', keywords: 'web development services NYC', schemaType: 'CollectionPage' },
}

type ServiceSpec = {
  slug: string
  title: string
  h1: string
  eyebrow: string
  sub: string
  answer: string
  metaTitle: string
  metaDesc: string
  keywords: string
  featuresHeading: string
  featuresIntro: string
  features: { icon: string; title: string; text: string }[]
  statement: string
  faqs: [string, string][]
  packages?: string[]
  work?: boolean
}

const servicePage = (s: ServiceSpec): PageSeed => ({
  title: s.title,
  slug: s.slug,
  parent: 'services',
  hero: { type: 'page', eyebrow: s.eyebrow, title: s.h1, subtitle: s.sub, answer: s.answer, links: [link('Get a free quote', '/contact'), link('Free website audit', '/website-audit')] },
  layout: [
    { blockType: 'services', eyebrow: 'What you get', heading: s.featuresHeading, intro: s.featuresIntro, items: s.features, columns: s.features.length === 4 ? '2' : '3' },
    statementBlock(s.statement, true),
    ...(s.work ? [workBlock({ style: 'grid', heading: 'Recent *builds*' })] : []),
    ...(s.packages ? [{ blockType: 'packagesBlock', eyebrow: 'Pricing', heading: 'Packages for this *service*', groups: s.packages } as Block] : []),
    processBlock(false),
    faq(`${s.title}: *questions*`, s.faqs),
    areasBlock({ heading: `${s.title} across *New York*` }),
    auditBlock(),
  ],
  meta: { title: s.metaTitle, description: s.metaDesc, keywords: s.keywords, schemaType: 'Service' },
})

const services: PageSeed[] = [
  servicePage({
    slug: 'web-development', title: 'Web Development', eyebrow: 'Custom web development · NYC',
    h1: 'Custom web development for *New York* businesses',
    sub: 'Fast, secure websites hand-coded on Next.js, with a CMS your team can run without calling a developer.',
    answer: 'Plen Dev is a custom web development company in New York. We build websites on Next.js and our Plen CMS, typically in 2 to 6 weeks, starting at $1,499.',
    metaTitle: 'Custom Web Development NYC | Plen Dev', metaDesc: 'Custom website development in NYC on Next.js with an easy CMS. Fast, secure, built to convert. Serving Brooklyn, Queens and Long Island.',
    keywords: 'custom website development NYC, web developer NYC, website redesign NYC',
    featuresHeading: 'Built for *speed*, built to last', featuresIntro: 'We write the code ourselves. No page builders, no plugin stack to babysit.',
    features: [
      { icon: 'gauge', title: 'Sub-2.5s load times', text: 'Server-rendered pages, optimized images and minimal JavaScript, tuned for Core Web Vitals on real phones.' },
      { icon: 'database', title: 'Plen CMS included', text: 'Live-preview editing, lead inbox, per-page SEO fields and tracking code on every build.' },
      { icon: 'smartphone', title: 'Mobile first', text: 'Designed and tested on phones first, because that is where most of your visitors are.' },
      { icon: 'shield', title: 'Secure by default', text: 'No WordPress plugins to exploit, managed hosting, SSL and daily backups.' },
      { icon: 'bot', title: 'AI-readable', text: 'Schema markup, a sitemap and an llms.txt file so Google and AI assistants understand your business.' },
      { icon: 'wrench', title: 'Redesigns & migrations', text: 'We move your content, keep your URLs and set up redirects so you don’t lose existing traffic.' },
    ],
    statement: 'Your website is your *hardest-working* employee. It should be fast, clear and always on message.',
    packages: ['websites'],
    work: true,
    faqs: [
      ['What technology do you build websites with?', 'We build on Next.js (React) with Payload, an open-source CMS that we customize for each client as the Plen CMS. Sites are hosted on Vercel or your own server.'],
      ['Can you redesign my existing website?', 'Yes. Most of our projects are redesigns. We audit your current site first, keep what works, move your content and set up redirects so your Google rankings carry over.'],
      ['Do I own the website?', 'Yes. You own the code, the content, the domain and the hosting account. There is no lock-in.'],
      ['Is custom development more expensive than WordPress?', 'Our Launch package starts at $1,499, which is in line with a quality WordPress build. You save money afterwards because there are no premium plugins, fewer security issues and less maintenance.'],
    ],
  }),
  servicePage({
    slug: 'web-design', title: 'Website Design', eyebrow: 'Website design agency · NYC',
    h1: 'Creative website design, *built to convert*',
    sub: 'Distinctive design for small businesses that want to look established, earn trust in seconds and turn visitors into calls.',
    answer: 'Plen Dev is a website design agency in New York. We design custom, mobile-first websites for small businesses, with packages from $1,499 to $6,999.',
    metaTitle: 'Website Design Agency NYC | Plen Dev', metaDesc: 'Creative, conversion-focused website design for New York small businesses. Custom design, motion and copy, from $1,499.',
    keywords: 'web design agency NYC, small business website design NYC, affordable web design NYC',
    featuresHeading: 'Design that *sells*, not just shines', featuresIntro: 'Every layout is designed around the one action you want visitors to take.',
    features: [
      { icon: 'palette', title: 'Custom, never templated', text: 'Typography, colour and layout designed for your brand and your customers.' },
      { icon: 'sparkles', title: 'Motion & interaction', text: 'Subtle animation that makes the site feel premium without slowing it down.' },
      { icon: 'chart', title: 'Conversion-led layouts', text: 'Clear calls to action, trust signals and forms placed where people decide.' },
      { icon: 'smartphone', title: 'Phone-first', text: 'Thumb-friendly navigation, tap-to-call and short forms on mobile.' },
      { icon: 'layout', title: 'Design system', text: 'Reusable sections in the CMS so new pages always look on-brand.' },
      { icon: 'search', title: 'Copy that ranks', text: 'Page copy written around what your customers search for.' },
    ],
    statement: 'People judge a business by its website in *50 milliseconds*. We design for that moment.',
    packages: ['websites'],
    work: true,
    faqs: [
      ['How much does website design cost in NYC?', 'Our design and build packages run from $1,499 for a 5-page site to $6,999 for a fully custom 25-page site with motion and booking. Enterprise projects start at $12,000.'],
      ['Do you write the website copy?', 'Growth includes copywriting for 5 pages and Signature includes all pages. You can also add copywriting to any package at $150 per page.'],
      ['How many design revisions do I get?', 'Launch includes 2 rounds and Growth 3 rounds. Signature includes unlimited small revisions during the design phase.'],
      ['Can I see the design before it is built?', 'Yes. You review a clickable design of your key pages on your own phone and computer before we start development.'],
    ],
  }),
  servicePage({
    slug: 'custom-cms', title: 'Custom CMS Development', eyebrow: 'Custom CMS development · NYC',
    h1: 'A CMS your team will *actually* enjoy using',
    sub: 'The Plen CMS: edit any text or photo with a live preview, see every lead in one inbox and manage SEO and tracking code page by page.',
    answer: 'Plen Dev builds custom CMS platforms in New York. The Plen CMS is a headless CMS (Payload + Next.js) with live preview, a lead inbox, SEO fields and per-page header code. Moving an existing site onto it starts at $2,499.',
    metaTitle: 'Custom CMS Development NYC | Plen Dev', metaDesc: 'Custom and headless CMS development in NYC. Live preview editing, lead inbox, SEO fields and header code per page. CMS upgrades from $2,499.',
    keywords: 'custom CMS development NYC, headless CMS development, custom CMS development',
    featuresHeading: 'Everything in *one* dashboard', featuresIntro: 'Built on Payload, the open-source headless CMS, and shaped around how your team works.',
    features: [
      { icon: 'layout', title: 'Live preview editing', text: 'Change text, swap images or rearrange sections and watch the page update beside you before publishing.' },
      { icon: 'database', title: 'Lead inbox', text: 'Every contact, quote and audit request saved with source page and UTM data. Mark status as you follow up.' },
      { icon: 'search', title: 'SEO on every page', text: 'Title, meta description, canonical, noindex, social image and custom schema, with a Google preview.' },
      { icon: 'code', title: 'Header code manager', text: 'Add unlimited snippets (GTM, pixels, chat widgets, verification tags) site-wide or on chosen pages.' },
      { icon: 'shield', title: 'Roles & drafts', text: 'Admin and editor roles, drafts, scheduled publishing and full version history with one-click restore.' },
      { icon: 'bot', title: 'API & automation', text: 'A secure REST and GraphQL API so your CRM, booking tool or AI agents can read and write content.' },
    ],
    statement: 'If changing a phone number needs a *developer*, your CMS is working against you.',
    packages: ['cms-apps'],
    faqs: [
      ['What is a headless CMS?', 'A headless CMS stores your content separately from the website design and serves it through an API. It makes sites faster and more secure, and lets the same content power a website, an app or an AI assistant.'],
      ['Custom CMS or WordPress: which is better for a small business?', 'WordPress is fine for a simple blog. A custom CMS is better when you want a fast, secure site with no plugin updates, an editing screen designed for your team and built-in lead management.'],
      ['Can you move my existing website onto the Plen CMS?', 'Yes. The CMS Upgrade package ($2,499) moves your current pages and content onto the Plen CMS, keeps your URLs and adds live preview, the lead inbox and SEO controls.'],
      ['Is the CMS hard to learn?', 'No. Most clients are comfortable after our 45-minute training session. Every page shows a live preview, so you always see what visitors will see.'],
    ],
  }),
  servicePage({
    slug: 'ecommerce', title: 'Ecommerce Development', eyebrow: 'Ecommerce website development · NYC',
    h1: 'Online stores that *sell* around the clock',
    sub: 'Shopify and custom ecommerce stores with fast product pages, smooth checkout and inventory that stays in sync.',
    answer: 'Plen Dev builds ecommerce websites in New York on Shopify or a custom Next.js stack. Stores start at $2,999 for up to 50 products.',
    metaTitle: 'Ecommerce Website Development NYC | Plen Dev', metaDesc: 'Shopify and custom ecommerce website development in NYC. Fast stores with smooth checkout, from $2,999.',
    keywords: 'ecommerce website development NYC, Shopify developer NYC, ecommerce website design for small business',
    featuresHeading: 'Stores built for *checkout*', featuresIntro: 'Every decision is measured against one thing: does it help people buy?',
    features: [
      { icon: 'cart', title: 'Shopify or custom', text: 'Shopify for most brands, custom Next.js commerce when you need full control.' },
      { icon: 'gauge', title: 'Fast product pages', text: 'Instant filters, optimized images and quick add-to-cart on mobile.' },
      { icon: 'chart', title: 'Conversion features', text: 'Reviews, bundles, upsells and abandoned-cart emails.' },
      { icon: 'database', title: 'Inventory sync', text: 'Bulk CSV uploads, POS sync and ERP or inventory integrations.' },
      { icon: 'search', title: 'Product SEO', text: 'Product schema, Google Merchant Center feeds and clean collection URLs.' },
      { icon: 'shield', title: 'Payments & tax', text: 'Stripe, Shop Pay, Apple Pay, shipping rules and sales tax set up correctly.' },
    ],
    statement: 'A store that loads one second faster can sell *noticeably more*. We obsess over that second.',
    packages: ['ecommerce'],
    work: true,
    faqs: [
      ['Should I use Shopify or a custom store?', 'Shopify is the right choice for most product brands: reliable checkout, apps and easy management. We recommend custom ecommerce for subscriptions, B2B pricing or complex catalogs.'],
      ['How much does an ecommerce website cost?', 'Our Storefront package is $2,999 for up to 50 products, Commerce is $5,999 for up to 500 products and Commerce Pro starts at $11,999.'],
      ['Can you migrate my store from another platform?', 'Yes. We migrate products, customers and order history from WooCommerce, Squarespace, Wix or BigCommerce, with redirects to protect your rankings.'],
    ],
  }),
  servicePage({
    slug: 'web-apps', title: 'Web App Development', eyebrow: 'Custom web applications · NYC',
    h1: 'Portals, dashboards and *web apps*',
    sub: 'Client portals, booking systems and internal tools built on the same fast stack as your website.',
    answer: 'Plen Dev builds custom web applications in New York with React and Next.js: client portals, booking platforms, dashboards and SaaS MVPs. Portals start at $9,999.',
    metaTitle: 'Custom Web App Development NYC | Plen Dev', metaDesc: 'Custom web application development in NYC: client portals, booking systems, dashboards and SaaS MVPs built with React and Next.js.',
    keywords: 'custom web application development NYC, client portal development, React Next.js developer NYC',
    featuresHeading: 'Software shaped around *your* workflow', featuresIntro: 'When spreadsheets and off-the-shelf tools stop fitting, we build exactly what you need.',
    features: [
      { icon: 'layout', title: 'Client portals', text: 'Secure logins, file sharing, invoices and project status for your customers.' },
      { icon: 'chart', title: 'Dashboards', text: 'Live reporting that pulls from your CRM, store or database.' },
      { icon: 'cpu', title: 'Booking & scheduling', text: 'Online booking with payments, reminders and staff calendars.' },
      { icon: 'bot', title: 'AI features', text: 'Assistants, document processing and automations connected to your data.' },
    ],
    statement: 'Good software makes the *busywork* disappear. That’s the whole brief.',
    packages: ['cms-apps'],
    faqs: [
      ['How much does a custom web app cost?', 'Client portals start at $9,999 and custom platforms such as marketplaces or SaaS MVPs start at $19,999. We scope every app in a paid discovery session first.'],
      ['How long does it take to build a web app?', 'A focused client portal takes 6 to 10 weeks. Larger platforms are released in phases, with a first usable version in about 8 to 12 weeks.'],
      ['Who owns the code?', 'You do. We hand over the repository, documentation and admin access at launch.'],
    ],
  }),
  servicePage({
    slug: 'website-maintenance', title: 'Website Maintenance', eyebrow: 'Website maintenance · NYC',
    h1: 'Care plans that keep your site *fast and safe*',
    sub: 'Managed hosting, backups, security updates and monthly edits, so your website never goes stale.',
    answer: 'Plen Dev offers website maintenance plans in New York from $79 per month, covering hosting, SSL, daily backups, uptime monitoring, security updates and monthly edits.',
    metaTitle: 'Website Maintenance NYC | Plen Dev', metaDesc: 'Website maintenance and care plans in NYC from $79/month: hosting, backups, security updates, uptime monitoring and monthly edits.',
    keywords: 'website maintenance services NYC, website support, website security',
    featuresHeading: 'We look after it, *you* run the business', featuresIntro: 'One monthly plan instead of a hosting bill, a security plugin and a freelancer you can never reach.',
    features: [
      { icon: 'shield', title: 'Security & updates', text: 'Dependencies patched, SSL renewed and firewalls monitored.' },
      { icon: 'database', title: 'Daily backups', text: 'Off-site backups with one-click restore.' },
      { icon: 'gauge', title: 'Speed checks', text: 'Monthly performance and site health checks with a short report.' },
      { icon: 'wrench', title: 'Edits included', text: 'Two to six hours of changes each month, depending on your plan.' },
    ],
    statement: 'A website is never *finished*. It should get better every month.',
    packages: ['care'],
    faqs: [
      ['What does website maintenance include?', 'All plans include managed hosting, SSL, daily backups, uptime monitoring and security updates. Pro Care adds 2 hours of edits and monthly health checks; Partner Care adds 6 hours, priority support and A/B testing.'],
      ['Can you maintain a website you didn’t build?', 'Yes, after a quick audit. If the site has serious issues we’ll quote a fix first.'],
      ['Is there a contract?', 'Plans are month to month. Pay yearly and get 10% off.'],
    ],
  }),
]

/* ---- core pages ---- */
const packagesPage: PageSeed = {
  title: 'Packages & Pricing',
  slug: 'packages',
  hero: {
    type: 'page',
    eyebrow: 'Packages & pricing',
    title: 'Packages and *pricing*',
    subtitle: 'Fixed prices for New York businesses. Every website includes the Plen CMS, mobile design, on-page SEO and AI-readable markup.',
    answer: 'Plen Dev websites cost $1,499 to $6,999 for most small businesses, with enterprise sites from $12,000. Ecommerce stores start at $2,999 and care plans at $79 per month.',
    links: [link('Get a custom quote', '/contact'), link('Free website audit', '/website-audit')],
  },
  layout: [
    { blockType: 'packagesBlock', note: 'Payment terms: 50% deposit and 50% at launch for builds under $5,000; 40/30/30 for larger builds. Monthly plans are billed on the 1st, with 10% off when paid yearly. Bundle any website with a yearly care plan and get 10% off the build. All prices in USD.' },
    faq('Pricing *questions*', [
      ['How much does a website cost in NYC in 2026?', 'Small business websites in New York usually cost between $2,000 and $15,000. Plen Dev websites start at $1,499 for 5 pages, $3,499 for a 12-page custom site and $6,999 for a fully custom 25-page site.'],
      ['Are there any hidden costs?', 'No. The quote covers design, development, the CMS and launch. Hosting and maintenance are optional monthly care plans from $79. Domain names and paid third-party apps are billed at cost.'],
      ['What is included in every website?', 'The Plen CMS with live preview, lead forms connected to your CMS inbox, mobile-first design, on-page SEO, schema markup, a sitemap and an llms.txt file for AI tools.'],
      ['Can I upgrade later?', 'Yes. Packages are a starting point. You can add pages ($199 each), integrations or ecommerce at any time.'],
    ]),
    contactForm({ heading: 'Not sure which package *fits*?', intro: 'Tell us about your business and we’ll recommend the right package with a fixed quote.' }),
  ],
  meta: { title: 'Website Packages & Pricing | Plen Dev', description: 'Website packages from $1,499, ecommerce from $2,999 and care plans from $79/mo. Transparent web design pricing for NYC businesses.', keywords: 'website design cost NYC, web design packages, website pricing NYC', schemaType: 'WebPage' },
}

const auditPage: PageSeed = {
  title: 'Free Website Audit',
  slug: 'website-audit',
  hero: {
    type: 'page',
    eyebrow: 'Free website audit',
    title: 'Get a free *website audit*',
    subtitle: 'Find out what is slowing your site down, hiding it from Google and costing you leads. Free, personal and in plain English.',
    answer: 'Plen Dev’s free website audit checks speed, mobile usability, search and AI visibility, broken links and conversion issues, and emails you a prioritized fix list, usually within one business day.',
    links: [link('Start my audit', '#audit')],
  },
  layout: [
    auditBlock({ eyebrow: 'Request your audit', heading: 'Send us your *URL*', dark: false }),
    {
      blockType: 'services',
      dark: true,
      eyebrow: 'What we check',
      heading: 'A real review, not a *robot score*',
      intro: 'Automated tools find the issues; a person checks every report before it reaches you.',
      columns: '3',
      items: [
        { icon: 'gauge', title: 'Speed & Core Web Vitals', text: 'Load time, LCP, CLS and INP on mobile, with the biggest causes named.' },
        { icon: 'smartphone', title: 'Mobile experience', text: 'Tap targets, layout shifts, pop-ups and readability on phones.' },
        { icon: 'search', title: 'Search visibility', text: 'Titles, meta descriptions, headings, indexing, sitemap and robots.txt.' },
        { icon: 'bot', title: 'AI readiness', text: 'Schema markup, llms.txt and whether AI tools can read your key facts.' },
        { icon: 'shield', title: 'Security & health', text: 'SSL, outdated software, broken links and forms that don’t send.' },
        { icon: 'chart', title: 'Conversion', text: 'Calls to action, trust signals and the path from landing to enquiry.' },
      ],
    },
    faq('About the *audit*', [
      ['Is the website audit really free?', 'Yes. There is no cost and no obligation. We send the report by email and you decide whether you want help with the fixes.'],
      ['How long does it take?', 'Most reports arrive within one business day. Larger sites can take up to two.'],
      ['What do I need to provide?', 'Just your website address and an email. Access to Google Search Console or Analytics is optional and makes the report more detailed.'],
      ['What if my website is fine?', 'Then we’ll tell you, and point out the two or three small improvements that are still worth making.'],
    ]),
  ],
  meta: { title: 'Free Website Audit | Plen Dev', description: 'Get a free website audit: speed, mobile, search and AI visibility, broken links and conversion. Personal report by email within one business day.', keywords: 'free website audit, website speed test, website redesign NYC', schemaType: 'WebPage' },
}

const workPage: PageSeed = {
  title: 'Work',
  slug: 'work',
  hero: { type: 'page', eyebrow: 'Portfolio', title: 'Selected *work*', subtitle: 'Websites for dentists, real estate teams, home care agencies, tech companies and online brands. Each one designed from scratch and run on the Plen CMS.' },
  layout: [statementBlock('Want your business *here* next?', true)],
  meta: { title: 'Web Design Portfolio | Plen Dev', description: 'Web design portfolio: dental, real estate, home healthcare, tech and ecommerce websites designed and built by Plen Dev in New York.', keywords: 'web design portfolio NYC, website examples', schemaType: 'CollectionPage' },
}

const aboutPage: PageSeed = {
  title: 'About',
  slug: 'about',
  hero: {
    type: 'page',
    eyebrow: 'About Plen Dev',
    title: 'A small studio with *big-agency* craft',
    subtitle: 'Plen Dev is a New York web design and development studio. We build websites that look custom because they are, and we hand them over with a CMS that makes your team independent.',
    answer: 'Plen Dev is a web development company based in New York, serving Brooklyn, Queens, Manhattan and Long Island. We design and build custom websites, online stores, CMS platforms and web apps.',
    links: [link('Start a project', '/contact'), link('See our work', '/work')],
  },
  layout: [
    statementBlock('We believe small businesses deserve the *same quality* of website as the brands they compete with.'),
    {
      blockType: 'services', dark: true, eyebrow: 'How we work', heading: 'What you can *expect*', columns: '2',
      items: [
        { icon: 'sparkles', title: 'Designed from scratch', text: 'No marketplace themes. Every site starts from your customers and your goals.' },
        { icon: 'code', title: 'Written by us', text: 'We write the code ourselves, which is why our sites are fast and easy to extend.' },
        { icon: 'database', title: 'You stay in control', text: 'You own the code, domain and content, and the CMS lets you change anything.' },
        { icon: 'map', title: 'Local and reachable', text: 'Based in New York, available to meet across the five boroughs and Long Island.' },
      ],
    },
    processBlock(false),
    areasBlock(),
    contactForm(),
  ],
  meta: { title: 'About Plen Dev | Web Development Studio in New York', description: 'Plen Dev is a New York web design and development studio building custom websites and CMS platforms for local businesses.', keywords: 'Plen Dev, web developer New York', schemaType: 'AboutPage' },
}

const contactPage: PageSeed = {
  title: 'Contact',
  slug: 'contact',
  hero: {
    type: 'page',
    eyebrow: 'Contact',
    title: 'Let’s talk about your *website*',
    subtitle: 'Email info@plendev.com or send the form. We reply within one business day.',
    answer: 'Contact Plen Dev at info@plendev.com for web design, web development, ecommerce or custom CMS projects in Brooklyn, Queens, NYC and Long Island.',
  },
  layout: [contactForm({ dark: false, eyebrow: 'Project brief' }), areasBlock({ dark: true })],
  meta: { title: 'Contact Plen Dev | Web Developer Near You in NYC', description: 'Contact Plen Dev for a website quote. Web design and development for businesses in Brooklyn, Queens, NYC and Long Island.', keywords: 'web developer near me, contact Plen Dev', schemaType: 'ContactPage' },
}

/* ---- locations ---- */
type LocSpec = {
  slug: string
  parent?: string
  title: string
  h1: string
  eyebrow: string
  sub: string
  answer: string
  metaTitle: string
  metaDesc: string
  keywords: string
  why: string
  neighborhoods: string[]
  industries: string
  faqs: [string, string][]
  areas?: Block
}

const locationPage = (l: LocSpec): PageSeed => ({
  title: l.title,
  slug: l.slug,
  parent: l.parent || 'locations',
  hero: { type: 'page', eyebrow: l.eyebrow, title: l.h1, subtitle: l.sub, answer: l.answer, links: [link('Free website audit', '/website-audit'), link('See packages', '/packages')] },
  layout: [
    marquee(l.neighborhoods, 'small'),
    statementBlock(l.why),
    servicesBlock({ eyebrow: `Services in ${l.title.replace(/^Web Design /, '')}`, heading: `What we build for *${l.title.replace(/^Web Design |^Website Design in /, '')}* businesses`, intro: l.industries }),
    workBlock({ style: 'grid', dark: true, heading: 'Recent *projects*' }),
    { blockType: 'packagesBlock', eyebrow: 'Pricing', heading: 'Transparent *packages*', groups: ['websites'], note: 'Ecommerce, custom CMS and care plans are on the full packages page.' },
    ...(l.areas ? [l.areas] : []),
    faq('Local *questions*', l.faqs),
    auditBlock(),
  ],
  meta: { title: l.metaTitle, description: l.metaDesc, keywords: l.keywords, schemaType: 'Service' },
})

const locationsHub: PageSeed = {
  title: 'Locations',
  slug: 'locations',
  hero: { type: 'page', eyebrow: 'Areas we serve', title: 'Web design across *New York*', subtitle: 'Brooklyn, Queens, the rest of NYC and Long Island. Local meetings, local knowledge, one studio.' },
  layout: [areasBlock({ eyebrow: undefined, heading: undefined, intro: undefined }), auditBlock()],
  meta: { title: 'Web Design Locations in New York | Plen Dev', description: 'Plen Dev builds websites for businesses in Brooklyn, Queens, New York City and Long Island (Nassau and Suffolk County).', keywords: 'web design New York locations', schemaType: 'CollectionPage' },
}

const locations: PageSeed[] = [
  locationPage({
    slug: 'brooklyn', title: 'Web Design Brooklyn', eyebrow: 'Brooklyn, NY',
    h1: '*Brooklyn* web design and development',
    sub: 'Creative, fast websites for Brooklyn restaurants, studios, clinics, contractors and shops, from Williamsburg to Bay Ridge.',
    answer: 'Plen Dev is a Brooklyn web design company. We design and build custom websites with an easy CMS for Brooklyn businesses, starting at $1,499, with in-person meetings across the borough.',
    metaTitle: 'Web Design Brooklyn, NY | Plen Dev', metaDesc: 'Brooklyn web design and development company. Custom websites with an easy CMS for Brooklyn businesses, from $1,499. Free website audit.',
    keywords: 'web design Brooklyn, Brooklyn web design company, web developer Brooklyn, web development company Brooklyn',
    why: 'Brooklyn customers *compare* before they call. Your website has to look as good as the business behind it.',
    neighborhoods: ['Williamsburg', 'Greenpoint', 'Park Slope', 'DUMBO', 'Brooklyn Heights', 'Bushwick', 'Bay Ridge', 'Crown Heights', 'Sunset Park', 'Bed-Stuy'],
    industries: 'Restaurants and cafés, dental and medical practices, salons and studios, contractors, real estate teams and independent shops.',
    faqs: [
      ['How much does a website cost in Brooklyn?', 'Plen Dev websites for Brooklyn businesses start at $1,499 for a 5-page site. Most custom small business sites cost $3,499 to $6,999.'],
      ['Can we meet in person in Brooklyn?', 'Yes. We regularly meet clients at their business or a café anywhere in Brooklyn for kickoff and training sessions.'],
      ['Do you help Brooklyn businesses show up in local search?', 'Every site we build is set up for local search: location schema, Google Business Profile link-up, fast mobile pages and a sitemap submitted to Google at launch.'],
    ],
  }),
  locationPage({
    slug: 'queens', title: 'Web Design Queens', eyebrow: 'Queens, NY',
    h1: '*Queens* web design and development',
    sub: 'Websites for Queens businesses that serve one of the most diverse markets in the world, including multilingual sites when you need them.',
    answer: 'Plen Dev is a web design and development company serving Queens, NY: Astoria, Long Island City, Flushing, Forest Hills, Jamaica and beyond. Websites start at $1,499 and can launch in multiple languages.',
    metaTitle: 'Web Design Queens, NY | Plen Dev', metaDesc: 'Queens web design and development: custom, multilingual-ready websites with an easy CMS for businesses in Astoria, LIC, Flushing and Forest Hills.',
    keywords: 'web design Queens NY, web development company Queens, web developer Queens NY',
    why: 'In Queens your customers might search in *five languages*. Your website can speak all of them.',
    neighborhoods: ['Astoria', 'Long Island City', 'Flushing', 'Forest Hills', 'Jackson Heights', 'Jamaica', 'Bayside', 'Sunnyside', 'Ridgewood', 'Elmhurst'],
    industries: 'Home care agencies, medical and dental practices, restaurants, immigration and law offices, contractors and retail stores.',
    faqs: [
      ['Can you build a multilingual website for my Queens business?', 'Yes. The Plen CMS supports multiple languages, so you can publish pages in English, Spanish, Chinese, Korean, Bengali or any other language and edit each version yourself.'],
      ['How much does a website cost in Queens?', 'Plen Dev websites start at $1,499 for 5 pages. A 12-page custom site with copywriting is $3,499.'],
      ['Do you work with home care agencies in Queens?', 'Yes. We build home care websites with service-area pages, caregiver recruiting forms and HIPAA-conscious intake flows.'],
    ],
  }),
  locationPage({
    slug: 'new-york-city', title: 'New York City Web Development', eyebrow: 'New York City',
    h1: '*New York City* web development',
    sub: 'Custom web development for companies across Manhattan, the Bronx, Staten Island, Brooklyn and Queens.',
    answer: 'Plen Dev is a web development company in New York City. We build custom websites, online stores, CMS platforms and web apps for NYC businesses, from $1,499.',
    metaTitle: 'Web Development Company NYC | Plen Dev', metaDesc: 'New York City web development company: custom websites, ecommerce, custom CMS and web apps for NYC businesses. Fixed prices from $1,499.',
    keywords: 'web development company New York, website design New York',
    why: 'New York is the most *competitive* market in the country. A generic template won’t cut it here.',
    neighborhoods: ['Manhattan', 'Midtown', 'Financial District', 'Upper West Side', 'Harlem', 'The Bronx', 'Staten Island', 'Brooklyn', 'Queens'],
    industries: 'Professional services, healthcare, real estate, hospitality, startups and growing ecommerce brands.',
    faqs: [
      ['What makes Plen Dev different from other NYC web agencies?', 'We combine agency-level design with a custom CMS and fixed, published prices. You get a site that is fast, easy to edit and fully owned by you.'],
      ['Do you work with startups?', 'Yes. We build marketing sites and MVPs for startups, typically on Next.js so they can grow with the product.'],
      ['How quickly can you launch?', 'A Launch site can go live in about 2 weeks. Most custom sites launch in 4 to 6 weeks.'],
    ],
  }),
  locationPage({
    slug: 'long-island', title: 'Web Design Long Island', eyebrow: 'Long Island, NY',
    h1: '*Long Island* web design and development',
    sub: 'Websites for Nassau and Suffolk County businesses that want to look established and win more local customers.',
    answer: 'Plen Dev is a Long Island web development company serving Nassau County and Suffolk County. We build custom websites with an easy CMS for local businesses, starting at $1,499.',
    metaTitle: 'Web Design Long Island, NY | Plen Dev', metaDesc: 'Long Island web design and development for Nassau and Suffolk County businesses. Custom websites with an easy CMS, from $1,499.',
    keywords: 'web design Long Island, Long Island web development company, web developer Long Island',
    why: 'Long Island customers search *locally* and choose quickly. Your site needs to win that first visit.',
    neighborhoods: ['Garden City', 'Hicksville', 'Mineola', 'Massapequa', 'Great Neck', 'Huntington', 'Smithtown', 'Hauppauge', 'Patchogue', 'Riverhead'],
    industries: 'Contractors and home services, dental and medical practices, real estate teams, law firms, landscapers and retail.',
    areas: {
      blockType: 'areas',
      eyebrow: 'Counties',
      heading: 'Nassau and *Suffolk*',
      areas: [
        { name: 'Nassau County', href: '/locations/long-island/nassau-county', neighborhoods: 'Garden City, Hicksville, Mineola, Massapequa, Great Neck, Freeport' },
        { name: 'Suffolk County', href: '/locations/long-island/suffolk-county', neighborhoods: 'Huntington, Smithtown, Hauppauge, Patchogue, Riverhead, Babylon' },
      ],
    },
    faqs: [
      ['Do you meet clients on Long Island?', 'Yes. We meet clients in person across Nassau and Suffolk County for kickoff and CMS training.'],
      ['How much does a website cost on Long Island?', 'Plen Dev websites start at $1,499. Most Long Island small business sites land between $3,499 and $6,999.'],
      ['Can you build a site for a contractor or home services company?', 'Yes. We build contractor sites with service-area pages, project galleries, quote forms and click-to-call on mobile.'],
    ],
  }),
  locationPage({
    slug: 'nassau-county', parent: 'long-island', title: 'Website Design in Nassau County', eyebrow: 'Nassau County, NY',
    h1: 'Website design in *Nassau County*',
    sub: 'Custom websites for businesses in Garden City, Hicksville, Mineola, Massapequa, Great Neck and across Nassau.',
    answer: 'Plen Dev designs and builds websites for Nassau County businesses, including Garden City, Hicksville, Mineola, Massapequa and Great Neck, starting at $1,499.',
    metaTitle: 'Website Design Nassau County | Plen Dev', metaDesc: 'Website design in Nassau County, NY: custom websites with an easy CMS for businesses in Garden City, Hicksville, Massapequa and Great Neck.',
    keywords: 'website design Nassau County, web design Garden City, web design Hicksville',
    why: 'Nassau businesses compete with *Manhattan* brands one train ride away. Look the part.',
    neighborhoods: ['Garden City', 'Hicksville', 'Mineola', 'Massapequa', 'Great Neck', 'Freeport', 'Levittown', 'Valley Stream', 'Rockville Centre', 'Westbury'],
    industries: 'Medical and dental offices, law firms, contractors, real estate agencies, restaurants and retail.',
    faqs: [
      ['Which Nassau County towns do you serve?', 'All of them, including Garden City, Hicksville, Mineola, Massapequa, Great Neck, Freeport, Levittown and Rockville Centre.'],
      ['How long does a Nassau County website project take?', 'Most sites launch in 2 to 6 weeks depending on the package.'],
    ],
  }),
  locationPage({
    slug: 'suffolk-county', parent: 'long-island', title: 'Website Design in Suffolk County', eyebrow: 'Suffolk County, NY',
    h1: 'Website design in *Suffolk County*',
    sub: 'Custom websites for businesses in Huntington, Smithtown, Hauppauge, Patchogue, Riverhead and across Suffolk.',
    answer: 'Plen Dev designs and builds websites for Suffolk County businesses, including Huntington, Smithtown, Hauppauge, Patchogue and Riverhead, starting at $1,499.',
    metaTitle: 'Website Design Suffolk County | Plen Dev', metaDesc: 'Website design in Suffolk County, NY: custom websites with an easy CMS for businesses in Huntington, Smithtown, Hauppauge and Riverhead.',
    keywords: 'website design Suffolk County, web design Huntington, web design Smithtown',
    why: 'From Huntington to the *Hamptons*, your website is the first place customers meet you.',
    neighborhoods: ['Huntington', 'Smithtown', 'Hauppauge', 'Patchogue', 'Riverhead', 'Babylon', 'Islip', 'Port Jefferson', 'Stony Brook', 'Southampton'],
    industries: 'Home services and contractors, marinas and hospitality, wineries, medical practices and professional services.',
    faqs: [
      ['Which Suffolk County towns do you serve?', 'All of Suffolk, including Huntington, Smithtown, Hauppauge, Patchogue, Islip, Riverhead and the East End.'],
      ['Do you build websites for seasonal businesses?', 'Yes. The CMS makes it easy to switch seasonal menus, hours and offers without calling us.'],
    ],
  }),
]

/* ---- industries ---- */
type IndSpec = {
  slug: string
  title: string
  h1: string
  sub: string
  answer: string
  metaTitle: string
  metaDesc: string
  keywords: string
  project: string // project slug
  features: { icon: string; title: string; text: string }[]
  statement: string
  faqs: [string, string][]
}

const industryPage = (i: IndSpec): PageSeed => ({
  title: i.title,
  slug: i.slug,
  parent: 'industries',
  hero: { type: 'page', eyebrow: `${i.title} websites`, title: i.h1, subtitle: i.sub, answer: i.answer, links: [link('See the example', `/work/${i.project}`), link('Get a quote', '/contact')] },
  layout: [
    workBlock({ source: 'pick', projects: [i.project], heading: 'A recent *build*', intro: undefined, eyebrow: 'Example' }),
    { blockType: 'services', eyebrow: 'Built for your industry', heading: 'What the site *does* for you', items: i.features, columns: '2' },
    statementBlock(i.statement, true),
    { blockType: 'packagesBlock', eyebrow: 'Pricing', heading: 'Packages', groups: [i.slug === 'ecommerce' ? 'ecommerce' : 'websites'] },
    faq(`${i.title} website *questions*`, i.faqs),
    auditBlock(),
  ],
  meta: { title: i.metaTitle, description: i.metaDesc, keywords: i.keywords, schemaType: 'Service' },
})

const industriesHub: PageSeed = {
  title: 'Industries',
  slug: 'industries',
  hero: { type: 'page', eyebrow: 'Industries', title: 'Websites built for *your* industry', subtitle: 'We know what patients, buyers, families and customers look for before they pick up the phone.' },
  layout: [
    {
      blockType: 'services', heading: undefined, columns: '3',
      items: [
        { icon: 'tooth', title: 'Dental practices', text: 'Online booking, insurance info and before-and-after galleries.', href: '/industries/dental' },
        { icon: 'home', title: 'Real estate', text: 'Live listings, agent pages and lead capture.', href: '/industries/real-estate' },
        { icon: 'heart', title: 'Home healthcare', text: 'Service areas, family enquiries and caregiver recruiting.', href: '/industries/home-healthcare' },
        { icon: 'cpu', title: 'Tech & SaaS', text: 'Product storytelling, pricing pages and docs.', href: '/industries/tech' },
        { icon: 'cart', title: 'Ecommerce', text: 'Fast stores that turn browsers into buyers.', href: '/industries/ecommerce' },
      ],
    },
    workBlock({ source: 'all', style: 'grid', dark: true }),
    auditBlock(),
  ],
  meta: { title: 'Website Design by Industry | Plen Dev', description: 'Websites for dental practices, real estate, home healthcare, tech and SaaS companies and ecommerce brands, designed and built in New York.', keywords: 'industry website design NYC', schemaType: 'CollectionPage' },
}

const industries: PageSeed[] = [
  industryPage({
    slug: 'dental', title: 'Dental', project: 'lumen-pine-dental',
    h1: 'Websites that fill *dental chairs*',
    sub: 'Dental websites with online booking, insurance information and treatment pages that answer patients’ questions before they call.',
    answer: 'Plen Dev designs dental websites in NYC with online booking, insurance and financing pages, treatment pages and reviews. Dental websites start at $3,499.',
    metaTitle: 'Dental Website Design NYC | Plen Dev', metaDesc: 'Dentist website design in NYC: online booking, insurance info, treatment pages and reviews. Built to bring in new patients.',
    keywords: 'dentist website design NYC, dental website design, dental practice website',
    features: [
      { icon: 'cpu', title: 'Online booking', text: 'Connect to your scheduling software or take requests straight into the CMS lead inbox.' },
      { icon: 'tooth', title: 'Treatment pages', text: 'Implants, Invisalign, whitening and emergency pages written to answer real patient questions.' },
      { icon: 'shield', title: 'Insurance & financing', text: 'Clear accepted-plans lists and financing options to remove the biggest objection.' },
      { icon: 'map', title: 'Local search', text: 'Dentist schema, location pages and Google Business Profile integration.' },
    ],
    statement: 'Patients choose a dentist they *trust*. Your website builds that trust before the first visit.',
    faqs: [
      ['What should a dental website include?', 'Online booking, a clear list of accepted insurance, treatment pages, doctor bios with photos, patient reviews, emergency information and click-to-call on mobile.'],
      ['Can patients book appointments online?', 'Yes. We integrate with popular dental scheduling tools or send booking requests to your CMS inbox and email.'],
      ['Is the site HIPAA compliant?', 'We keep sensitive health information out of standard web forms and can connect secure, HIPAA-compliant intake tools when you need them.'],
    ],
  }),
  industryPage({
    slug: 'real-estate', title: 'Real Estate', project: 'kestrel-row-realty',
    h1: 'Real estate websites with *live listings*',
    sub: 'Brokerage and agent websites with IDX listings, neighborhood guides and lead capture that feeds your CRM.',
    answer: 'Plen Dev builds real estate websites in NYC and Long Island with IDX listing search, agent profiles, neighborhood guides and CRM-connected lead forms.',
    metaTitle: 'Real Estate Website Design NYC | Plen Dev', metaDesc: 'Real estate website design in NYC and Long Island: IDX listings, agent pages, neighborhood guides and lead capture into your CRM.',
    keywords: 'real estate website design NYC, IDX website, realtor website',
    features: [
      { icon: 'home', title: 'IDX listing search', text: 'Searchable listings with map view, saved searches and alerts.' },
      { icon: 'map', title: 'Neighborhood guides', text: 'Local pages that rank for “homes for sale in…” searches.' },
      { icon: 'database', title: 'Lead capture', text: 'Showing requests and valuations sent straight to your CRM.' },
      { icon: 'layout', title: 'Agent profiles', text: 'Each agent manages their own page and listings in the CMS.' },
    ],
    statement: 'Buyers browse on their *phones* at midnight. Your listings should look incredible there.',
    faqs: [
      ['What is an IDX website?', 'IDX (Internet Data Exchange) lets your website show MLS listings automatically, so visitors can search homes on your site instead of Zillow.'],
      ['Can agents edit their own pages?', 'Yes. Each agent can have their own login with access only to their profile and listings.'],
      ['Do you integrate with real estate CRMs?', 'Yes, including Follow Up Boss, kvCORE and HubSpot, among others.'],
    ],
  }),
  industryPage({
    slug: 'home-healthcare', title: 'Home Healthcare', project: 'hearthside-home-care',
    h1: 'Websites for *home care* agencies',
    sub: 'Home care websites that reassure families, explain services clearly and help you recruit caregivers.',
    answer: 'Plen Dev builds home health care websites for agencies in NYC and Long Island, with service pages, family enquiry forms, caregiver recruiting and multilingual support.',
    metaTitle: 'Home Health Care Website Design | Plen Dev', metaDesc: 'Home health care website design for agencies in NY: service pages, family enquiries, caregiver recruiting and multilingual support.',
    keywords: 'home health care website design, home care agency marketing NY, caregiver recruiting website',
    features: [
      { icon: 'heart', title: 'Family-first messaging', text: 'Warm, clear service pages that answer the questions families ask at 2 a.m.' },
      { icon: 'database', title: 'Caregiver recruiting', text: 'Job listings and applications that go straight into the CMS.' },
      { icon: 'map', title: 'Service-area pages', text: 'Borough and county pages so families find you locally.' },
      { icon: 'smartphone', title: 'Multilingual', text: 'Publish pages in the languages your clients and caregivers speak.' },
    ],
    statement: 'Families are making one of the *hardest decisions* of their lives. Your website should make it easier.',
    faqs: [
      ['What should a home care agency website include?', 'Clear service descriptions, areas served, insurance and Medicaid information, a simple enquiry form, caregiver job listings and phone numbers that are easy to tap.'],
      ['Can the site help us hire caregivers?', 'Yes. We add a careers section with applications that go straight to your CMS lead inbox.'],
      ['Can the website be in more than one language?', 'Yes. The Plen CMS supports multiple languages with separate editable versions of every page.'],
    ],
  }),
  industryPage({
    slug: 'tech', title: 'Tech & SaaS', project: 'relaywave',
    h1: 'Websites for *tech and SaaS* teams',
    sub: 'Marketing sites that make complex products easy to understand, with pricing, docs and changelog your team can update.',
    answer: 'Plen Dev designs and builds websites for tech startups and SaaS companies in NYC on Next.js, with product pages, pricing, docs and a CMS for the marketing team.',
    metaTitle: 'Tech & SaaS Website Design NYC | Plen Dev', metaDesc: 'Tech startup and SaaS website design in NYC: product storytelling, pricing pages, docs and a CMS your marketing team controls.',
    keywords: 'tech startup website design NYC, SaaS website design agency',
    features: [
      { icon: 'sparkles', title: 'Product storytelling', text: 'Interactive sections and motion that show how the product works.' },
      { icon: 'chart', title: 'Pricing & signup', text: 'Pricing pages, comparison tables and signup flows that convert.' },
      { icon: 'code', title: 'Docs & changelog', text: 'MDX docs, changelog and blog in the same CMS.' },
      { icon: 'gauge', title: 'Built on Next.js', text: 'The same stack as your product, so your engineers can contribute.' },
    ],
    statement: 'Great products lose deals to *clearer* websites. Let’s make yours the clear one.',
    faqs: [
      ['Do you work with early-stage startups?', 'Yes. We often build a launch site in 2 to 3 weeks and grow it with the company.'],
      ['Can our engineers work on the codebase?', 'Yes. It is a standard Next.js and TypeScript project in your own repository.'],
      ['Do you design product UI as well?', 'We design marketing sites and can build dashboards and portals through our web app service.'],
    ],
  }),
  industryPage({
    slug: 'ecommerce', title: 'Ecommerce', project: 'saltgrain-ceramics',
    h1: 'Online stores for *growing brands*',
    sub: 'Beautiful, fast stores for makers and product brands, built on Shopify or a custom stack.',
    answer: 'Plen Dev designs ecommerce websites for small businesses and product brands, on Shopify or custom Next.js, starting at $2,999.',
    metaTitle: 'Ecommerce Store Design | Plen Dev', metaDesc: 'Ecommerce website design for small businesses and product brands: Shopify or custom stores with fast checkout, from $2,999.',
    keywords: 'ecommerce website design for small business, Shopify store design',
    features: [
      { icon: 'cart', title: 'Fast checkout', text: 'Shop Pay, Apple Pay and a checkout with as few steps as possible.' },
      { icon: 'palette', title: 'Brand-led design', text: 'Product pages that feel like your brand, not a theme.' },
      { icon: 'database', title: 'Easy catalog', text: 'Bulk uploads, variants and collections managed in one place.' },
      { icon: 'chart', title: 'Growth tools', text: 'Reviews, bundles, email capture and abandoned-cart flows.' },
    ],
    statement: 'Your products are *one of a kind*. Your store should be too.',
    faqs: [
      ['How much does an ecommerce website cost for a small business?', 'Our Storefront package is $2,999 for up to 50 products. Most growing brands choose Commerce at $5,999.'],
      ['Shopify or custom?', 'Shopify suits most brands. Custom makes sense for subscriptions, wholesale pricing or unusual product setups.'],
    ],
  }),
]

export const PAGES: PageSeed[] = [
  home,
  servicesHub,
  ...services,
  packagesPage,
  auditPage,
  workPage,
  aboutPage,
  contactPage,
  locationsHub,
  ...locations,
  industriesHub,
  ...industries,
]

/* ---------------- packages (web development only, no SEO plans) ---------------- */
export const PACKAGES = [
  { group: 'websites', order: 1, name: 'Launch', price: 1499, billing: 'one-time', tagline: 'New businesses and solo practices', scope: 'Up to 5 pages', timeline: '2-week delivery', features: ['Creative design from our template library', 'Plen CMS with live preview', 'Lead forms into your CMS inbox', 'Google Business Profile setup', 'Basic on-page SEO', '2 revision rounds'] },
  { group: 'websites', order: 2, name: 'Growth', price: 3499, billing: 'one-time', tagline: 'Established local businesses', scope: 'Up to 12 pages', timeline: '4-week delivery', highlighted: true, features: ['Fully custom design', 'Copywriting for 5 pages', 'Blog', 'Schema markup', 'Speed optimization', 'Google Analytics 4 & Search Console', '1 location page', '3 revision rounds'] },
  { group: 'websites', order: 3, name: 'Signature', price: 6999, billing: 'one-time', tagline: 'Multi-location or competitive markets', scope: 'Up to 25 pages', timeline: '6–8 weeks', features: ['Custom design with motion & interactions', 'Full copywriting', 'Booking or quote system', '4 location or industry pages', 'CRM integration', 'Multilingual option', '90 days of support'] },
  { group: 'websites', order: 4, name: 'Enterprise', price: 12000, pricePrefix: 'From', billing: 'one-time', tagline: 'Larger companies, complex needs', scope: 'Unlimited pages', timeline: 'Scoped', ctaLabel: 'Book a call', features: ['Discovery workshop', 'Design system', 'Custom integrations', 'Role-based CMS', 'WCAG 2.2 AA accessibility audit', 'Dedicated project manager'] },
  { group: 'ecommerce', order: 10, name: 'Storefront', price: 2999, billing: 'one-time', tagline: 'Launch your first store', scope: 'Up to 50 products', features: ['Shopify or custom store', 'Payments, shipping & tax setup', 'Product SEO', 'Mobile-first product pages'] },
  { group: 'ecommerce', order: 11, name: 'Commerce', price: 5999, billing: 'one-time', tagline: 'Growing product brands', scope: 'Up to 500 products', highlighted: true, features: ['Custom theme', 'Reviews', 'Abandoned-cart emails', 'Bulk CSV upload', 'Google Merchant Center'] },
  { group: 'ecommerce', order: 12, name: 'Commerce Pro', price: 11999, pricePrefix: 'From', billing: 'one-time', tagline: 'Complex catalogs and B2B', scope: 'Unlimited products', ctaLabel: 'Book a call', features: ['Subscriptions', 'B2B / wholesale pricing', 'ERP or inventory integration', 'Multi-currency'] },
  { group: 'cms-apps', order: 20, name: 'CMS Upgrade', price: 2499, billing: 'one-time', tagline: 'Move your site onto the Plen CMS', features: ['Live-preview editing', 'Lead inbox', 'Per-page header code', 'SEO fields on every page', 'Content migration'] },
  { group: 'cms-apps', order: 21, name: 'Client Portal', price: 9999, pricePrefix: 'From', billing: 'one-time', tagline: 'Logins, dashboards and files', highlighted: true, ctaLabel: 'Book a call', features: ['User accounts', 'Dashboards', 'File sharing', 'Admin panel', '180 days of support'] },
  { group: 'cms-apps', order: 22, name: 'Custom Platform', price: 19999, pricePrefix: 'From', billing: 'one-time', tagline: 'Marketplaces, booking, SaaS MVPs', ctaLabel: 'Book a call', features: ['Discovery & scoping', 'Marketplace, booking platform or SaaS MVP', 'Phased releases'] },
  { group: 'care', order: 30, name: 'Essential Care', price: 79, billing: 'monthly', tagline: 'Keep it online and safe', features: ['Managed hosting', 'SSL', 'Daily backups', 'Uptime monitoring', 'Security updates'] },
  { group: 'care', order: 31, name: 'Pro Care', price: 199, billing: 'monthly', tagline: 'Most small businesses', highlighted: true, features: ['Everything in Essential', '2 hours of edits per month', 'Speed & site health checks', 'Monthly report'] },
  { group: 'care', order: 32, name: 'Partner Care', price: 449, billing: 'monthly', tagline: 'Sites that keep evolving', features: ['Everything in Pro', '6 hours of edits per month', 'Priority support', 'Quarterly design refresh', 'A/B testing'] },
  { group: 'addons', order: 40, name: 'Free website audit', price: 0, billing: 'one-time', tagline: 'Speed, mobile, search & conversion review' },
  { group: 'addons', order: 41, name: 'Full website audit with fix plan', price: 499, billing: 'one-time' },
  { group: 'addons', order: 42, name: 'Logo and brand kit', priceNote: '$499 to $1,499', billing: 'one-time' },
  { group: 'addons', order: 43, name: 'Extra page', price: 199, billing: 'each' },
  { group: 'addons', order: 44, name: 'Copywriting', price: 150, billing: 'per-page' },
  { group: 'addons', order: 45, name: 'Professional photo or video shoot (NYC)', price: 750, pricePrefix: 'From', billing: 'one-time' },
  { group: 'addons', order: 46, name: 'Brand or explainer video (60 sec)', price: 1499, pricePrefix: 'From', billing: 'one-time' },
  { group: 'addons', order: 47, name: 'Website migration', price: 399, pricePrefix: 'From', billing: 'one-time' },
  { group: 'addons', order: 48, name: 'Third-party integration (CRM, booking, payments)', price: 499, pricePrefix: 'From', billing: 'each' },
]

/* ---------------- portfolio (demo sites in /public/showcase) ---------------- */
export const PROJECTS = [
  {
    slug: 'lumen-pine-dental', title: 'Lumen & Pine Dental', industry: 'Dental', location: 'Park Slope, Brooklyn', year: '2026', accent: '#2f8f83', domain: 'lumenpinedental.com', order: 1,
    summary: 'A calm, modern website for a family and cosmetic dental studio, with online booking, insurance information and treatment pages.',
    challenge: 'A growing two-dentist practice needed a site that felt as calm and modern as the studio itself, and that answered insurance and booking questions without a phone call.',
    solution: 'A warm, airy design with a sticky “Book a visit” bar, treatment pages written around patient questions, an insurance checker section and new-patient specials editable in the CMS.',
    services: ['Website design', 'Development', 'Plen CMS', 'Online booking'],
    results: [{ value: '1 tap', label: 'to call or book on mobile' }, { value: '8', label: 'treatment pages in the CMS' }],
  },
  {
    slug: 'kestrel-row-realty', title: 'Kestrel Row Realty', industry: 'Real estate', location: 'North Shore, Long Island', year: '2026', accent: '#b8893b', domain: 'kestrelrow.com', order: 2,
    summary: 'A boutique brokerage site with featured listings, neighborhood guides and a home-valuation lead form.',
    challenge: 'A boutique North Shore brokerage was losing buyers to the big portals and needed a site that showcased listings as beautifully as the homes themselves.',
    solution: 'An editorial, image-led design with a listing search, neighborhood guides for each town and a “What’s my home worth?” form that drops sellers straight into the lead inbox.',
    services: ['Website design', 'Development', 'Listings', 'Lead capture'],
    results: [{ value: '6', label: 'neighborhood guides' }, { value: '2-step', label: 'home valuation form' }],
  },
  {
    slug: 'relaywave', title: 'Relaywave', industry: 'Tech / SaaS', location: 'Flatiron, Manhattan', year: '2026', accent: '#6d5dfc', domain: 'relaywave.io', order: 3, featured: true,
    summary: 'A product marketing site for a workflow automation platform, with interactive product sections, pricing and a changelog.',
    challenge: 'A Series A automation startup had a product that demoed well but a website that explained it badly.',
    solution: 'A dark, high-contrast site with an animated workflow diagram, integration grid, three-tier pricing and a changelog the marketing team updates in the CMS.',
    services: ['Website design', 'Next.js development', 'Motion', 'Pricing page'],
    results: [{ value: '3-tier', label: 'pricing with comparison' }, { value: '40+', label: 'integration logos managed in CMS' }],
  },
  {
    slug: 'hearthside-home-care', title: 'Hearthside Home Care', industry: 'Home healthcare', location: 'Forest Hills, Queens', year: '2026', accent: '#d9774b', domain: 'hearthsidehomecare.com', order: 4, featured: true,
    summary: 'A warm, reassuring website for a licensed home care agency, with service pages, family enquiries and caregiver recruiting.',
    challenge: 'A family-run home care agency needed to reassure worried families and recruit caregivers from the same website.',
    solution: 'Soft colours, plain-language service pages, a “Talk to a care coordinator” form, borough service areas and a careers section with applications flowing into the CMS.',
    services: ['Website design', 'Development', 'Recruiting', 'Multilingual-ready'],
    results: [{ value: '2', label: 'lead types: families & caregivers' }, { value: '5', label: 'service-area pages' }],
  },
  {
    slug: 'saltgrain-ceramics', title: 'Saltgrain Ceramics', industry: 'Ecommerce', location: 'Red Hook, Brooklyn', year: '2026', accent: '#c2410c', domain: 'saltgrain.shop', order: 5, featured: true,
    summary: 'An online store for a handmade ceramics studio, with collections, product pages, a cart drawer and a workshop booking section.',
    challenge: 'A ceramics studio selling through Instagram DMs needed a proper store that felt as handmade as the work.',
    solution: 'A tactile, editorial storefront with collection filters, rich product pages, a slide-out cart and studio workshop listings.',
    services: ['Ecommerce design', 'Storefront', 'Product pages', 'Workshops'],
    results: [{ value: '3', label: 'collections at launch' }, { value: '1-page', label: 'cart & checkout flow' }],
  },
]

/* ---------------- blog posts (markdown-ish, converted to Lexical) ---------------- */
export const POSTS = [
  {
    slug: 'website-cost-nyc',
    title: 'How Much Does a Website Cost in NYC in 2026?',
    description: 'Real 2026 price ranges for small business websites in New York, what drives the cost and how to budget for a site that pays for itself.',
    body: `Most New York small businesses pay between $2,000 and $15,000 for a professionally designed website in 2026. Where you land depends on four things: the number of pages, how custom the design is, the features you need and who writes the copy.

## Typical price ranges

- **Starter sites (up to 5 pages): $1,500 to $3,000.** Good for new businesses and solo practices.
- **Custom small business sites (10 to 15 pages): $3,500 to $7,000.** Custom design, copywriting, a blog and local landing pages.
- **Advanced sites (20+ pages): $7,000 to $15,000.** Booking systems, integrations, multiple locations and motion design.
- **Ecommerce stores: $3,000 to $12,000+.** Depends mostly on product count and integrations.

## What drives the cost

1. **Design.** A template you customize is cheaper than a design built around your brand and customers.
2. **Content.** Professional copywriting and photography add cost but usually pay for themselves in conversions.
3. **Features.** Online booking, quote calculators, member areas and CRM integrations each add development time.
4. **The CMS.** A CMS your team can actually use saves you paying a developer for every small change.

## Ongoing costs to budget for

Hosting, SSL, backups and security updates usually run $50 to $200 per month. Plen Dev care plans start at $79 per month and include all of these.

## How to get an accurate quote

Ask for a fixed price with a written list of pages and features. If you already have a website, start with a [free website audit](/website-audit) so the quote is based on what actually needs to change. You can compare our [packages and pricing](/packages) or read about [custom web development in NYC](/services/web-development).`,
  },
  {
    slug: 'custom-cms-vs-wordpress',
    title: 'Custom CMS vs WordPress: Which Is Better for a Small Business?',
    description: 'An honest comparison of WordPress and a custom headless CMS for small businesses: speed, security, editing, cost and when each one makes sense.',
    body: `WordPress powers a huge share of the web, so it is the default choice for many small businesses. But a custom CMS is often the better fit for a business that wants a fast, secure site its team can edit without fear of breaking it.

## When WordPress makes sense

- You mainly publish blog posts.
- You are comfortable updating plugins and themes every month.
- You need a very specific plugin that has no alternative.

## When a custom CMS is better

- **Speed matters.** Custom sites built on frameworks like Next.js ship far less code than a typical WordPress theme with ten plugins.
- **Security matters.** Most WordPress hacks come through outdated plugins. A custom CMS has no plugin marketplace to exploit.
- **Your team edits often.** A custom editing screen shows only the fields your team needs, with a live preview of the page.
- **You want leads in one place.** The Plen CMS saves every form submission in a lead inbox with source and campaign data.

## What about cost?

Upfront costs are similar for a quality build. A custom CMS usually costs less to run because there are no premium plugins to renew and far fewer emergency fixes.

## Our recommendation

If your website is a sales tool rather than a blog, a custom CMS is usually the better long-term choice. Read more about our [custom CMS development](/services/custom-cms) or see how we work with businesses in [Brooklyn](/locations/brooklyn).`,
  },
  {
    slug: 'website-audit-checklist',
    title: 'Website Audit Checklist: 20 Things to Check Before a Redesign',
    description: 'A practical website audit checklist covering speed, mobile, search, AI visibility, security and conversion, so you know what to fix before you redesign.',
    body: `A redesign without an audit is a guess. Before you spend money on a new website, check these 20 points so you keep what works and fix what doesn’t.

## Speed and technical health

1. Mobile load time under 2.5 seconds (Largest Contentful Paint).
2. No layout jumping while the page loads (CLS under 0.1).
3. Images in modern formats and correctly sized.
4. SSL certificate valid on every page.
5. No broken links or 404 pages linked from your menu.

## Mobile experience

6. Text readable without zooming.
7. Buttons big enough to tap.
8. Phone number tap-to-call.
9. No pop-ups covering the content on phones.

## Search and AI visibility

10. Every page has a unique title and meta description.
11. One clear H1 per page.
12. A sitemap submitted to Google Search Console.
13. Schema markup for your business type.
14. An llms.txt file that summarizes your business for AI tools.
15. Your name, address and phone match your Google Business Profile.

## Conversion

16. A clear call to action above the fold.
17. Forms that actually send (test them!).
18. Reviews or proof near the call to action.
19. Prices or price ranges where customers expect them.
20. Analytics tracking form submissions as conversions.

Want us to run this for you? Request a [free website audit](/website-audit) and we’ll email a prioritized report, or see our [website maintenance plans](/services/website-maintenance).`,
  },
]
