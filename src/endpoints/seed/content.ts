/* eslint-disable */
// Seed content for Plen Dev. Keyword targets come from
// /mnt/project-files/plen-dev/keywords-and-packages.md (one primary keyword per page).
// Copy style: plain American English for NYC small business owners. No agency jargon, no em-dashes.
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
  { icon: 'code', title: 'Custom web development', text: 'A website coded from scratch for your business. It loads fast on phones and grows with you.', href: '/services/web-development' },
  { icon: 'palette', title: 'Website design', text: 'A design made for your business and your customers, not a template with your logo dropped in.', href: '/services/web-design' },
  { icon: 'database', title: 'Easy website editor', text: 'Change text, photos and prices yourself, see every inquiry in one place, and never wait on a developer.', href: '/services/custom-cms' },
  { icon: 'cart', title: 'Online stores', text: 'Shopify or custom online stores with quick checkout on phones and inventory that stays up to date.', href: '/services/ecommerce' },
  { icon: 'layout', title: 'Web apps and portals', text: 'Customer logins, online booking, dashboards and tools that replace your spreadsheets.', href: '/services/web-apps' },
  { icon: 'shield', title: 'Website care plans', text: 'Hosting, backups, security and small edits every month for one flat price.', href: '/services/website-maintenance' },
]

export const servicesBlock = (opts: Partial<Block> = {}): Block => ({
  blockType: 'services',
  eyebrow: 'What we build',
  heading: 'Everything your website needs, from *one team*',
  intro: 'We design it, build it, launch it and look after it. You deal with the same people from the first call to years after launch.',
  items: SERVICE_ITEMS,
  columns: '3',
  ...opts,
})

export const processBlock = (dark = true): Block => ({
  blockType: 'process',
  dark,
  eyebrow: 'How it works',
  heading: 'Your new website, live in *2 to 6 weeks*',
  intro: 'You get a fixed price before we start, and you can see your site on your own phone at every step.',
  steps: [
    { title: 'Free call and audit', text: 'We talk for 30 minutes and review your current website for free. Then you get a written quote with a fixed price.', duration: 'Week 1' },
    { title: 'Design', text: 'We design your home page and main pages. You click through them on your phone and tell us what to change.', duration: 'Weeks 1 to 2' },
    { title: 'Build', text: 'We build the site, move your content over, and set up your forms, phone links and Google tracking.', duration: 'Weeks 2 to 4' },
    { title: 'Launch and training', text: 'We put the site live, submit it to Google, and show your team how to make changes in a 45-minute session.', duration: 'Week 4 and on' },
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
  heading: 'Web design across *New York*',
  intro: 'We build websites for businesses in Brooklyn, Queens, Manhattan and Long Island, and we are happy to meet you in person.',
  areas: AREAS,
  ...opts,
})

export const auditBlock = (opts: Partial<Block> = {}): Block => ({
  blockType: 'leadForm',
  formType: 'website_audit',
  dark: true,
  eyebrow: 'Free website audit',
  heading: 'Is your website *losing* you customers?',
  intro: 'Enter your website address. A real person on our team will check it and email you a short report: what is wrong, why it matters and what to fix first.',
  bullets: [
    { text: 'How fast your site loads on a phone' },
    { text: 'How easy it is to find you on Google' },
    { text: 'Broken links, forms and pages' },
    { text: 'A simple list of fixes, ranked by importance' },
  ],
  submitLabel: 'Send my free audit',
  successMessage: "Thanks! We got your request. A real person will review your site and email your report within one business day.",
  anchor: 'audit',
  ...opts,
})

export const statementBlock = (text: string, dark = false): Block => ({
  blockType: 'statement',
  dark,
  text,
  links: [link('Get a free quote', '/contact'), link('See prices', '/packages')],
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
  eyebrow: 'Our work',
  heading: 'Websites we have *built*',
  intro: 'Every site is designed from scratch for the business and its customers. Each one comes with an editor the owner can use without help.',
  source: 'featured',
  style: 'stack',
  ...opts,
})

const contactForm = (opts: Partial<Block> = {}): Block => ({
  blockType: 'leadForm',
  formType: 'quote',
  eyebrow: 'Get a quote',
  heading: 'Tell us about your *business*',
  intro: 'Answer a few quick questions. We will reply within one business day with a price range and a timeline.',
  bullets: [{ text: 'A fixed price, agreed before we start' }, { text: 'You own your website, domain and content' }, { text: 'We meet in person in NYC and Long Island' }],
  submitLabel: 'Get my quote',
  successMessage: "Thanks! We got your details and will reply within one business day.",
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
    eyebrow: 'Web design and development company in New York',
    title: 'Websites that bring *New York* businesses more customers',
    subtitle: 'Plen Dev designs and builds websites for businesses in Brooklyn, Queens, NYC and Long Island. Your site loads fast, looks great on phones, and is easy for you to update.',
    answer: 'Plen Dev is a web development company in New York. We build custom websites, online stores and web apps for small businesses, with an easy editor built in. Websites start at $1,499.',
    links: [link('Get a free website audit', '/website-audit'), link('See our work', '/work')],
    badges: [
      { value: '2 to 6 wk', label: 'to launch' },
      { value: '$1,499', label: 'websites from' },
      { value: '<2s', label: 'load time on phones' },
      { value: '$0', label: 'monthly fees to own it' },
    ],
  },
  layout: [
    marquee(['Web design', 'Web development', 'Online stores', 'Web apps', 'Brooklyn', 'Queens', 'NYC', 'Long Island']),
    servicesBlock(),
    workBlock(),
    {
      blockType: 'services',
      dark: true,
      eyebrow: 'Why New York businesses choose Plen Dev',
      heading: 'What you *actually* get',
      intro: 'Not a template with your logo on it. A website that loads fast, stays secure, brings in calls and bookings, and belongs to you.',
      columns: '3',
      items: [
        { icon: 'zap', title: 'Loads in under 2 seconds', text: 'Built to be fast on a phone, not just on office Wi-Fi. Faster sites rank higher on Google and lose fewer visitors before they call.' },
        { icon: 'trending', title: 'Built to bring in leads', text: 'Call buttons, booking and quote forms where customers look for them. You see which ad, search or post every lead came from.' },
        { icon: 'lock', title: 'Nothing to hack or patch', text: 'No WordPress plugins and no outdated themes. Secure hosting, SSL, daily backups and 24/7 monitoring come standard.' },
        { icon: 'accessibility', title: 'ADA-ready from day one', text: 'Built to meet accessibility standards (WCAG 2.2 AA), so more people can use your site and you lower the risk of an ADA lawsuit.' },
        { icon: 'key', title: 'You own everything', text: 'Your domain, website, content and accounts stay in your name. No long contract and no monthly fee just to keep your site online.' },
        { icon: 'headset', title: 'A real person, same day', text: 'A New York team that answers within one business day, makes small changes for you and meets in person when it helps.' },
      ],
    },
    {
      blockType: 'packagesBlock',
      eyebrow: 'Prices',
      heading: 'Website packages with *clear* prices',
      intro: 'Fixed prices for New York small businesses. Every package includes mobile design, Google basics and the editor to update your site yourself.',
      groups: ['websites'],
      note: 'Need an online store, a customer portal or something bigger? See all packages, including ecommerce and monthly care plans.',
    },
    processBlock(false),
    areasBlock(),
    faq('Questions we hear *every* week', [
      ['How much does a website cost in New York?', 'Most small business websites we build cost between $1,499 and $6,999, paid once. Online stores start at $2,999, and larger custom projects start at $12,000. You get a fixed price before any work starts.'],
      ['How long does it take to build a website?', 'A 5-page website takes about 2 weeks. A 12-page custom website takes about 4 weeks. Bigger sites with booking, online sales or connections to other software usually take 6 to 10 weeks.'],
      ['Can I update the website myself?', 'Yes. Every site comes with our easy editor. Click a page, change the text or swap a photo, preview it, and publish. No code needed.'],
      ['Do you only work with businesses in NYC?', 'Most of our clients are in Brooklyn, Queens, Manhattan and Long Island, and we meet in person when it helps. We also build websites for businesses anywhere in the US.'],
      ['Will my website show up on Google and in ChatGPT?', 'Every site is built so Google and AI tools like ChatGPT can read it easily. We set up Google Search Console and Google Analytics when your site goes live.'],
    ]),
    auditBlock(),
  ],
  meta: {
    title: 'Web Design & Development Company in NYC | Plen Dev',
    description: 'Plen Dev builds fast, custom websites for businesses in Brooklyn, Queens, NYC and Long Island. Easy to update yourself. Websites from $1,499.',
    keywords: 'web design company NYC, web development company New York, custom website development NYC',
    schemaType: 'WebPage',
  },
}

/* ---- services ---- */
const servicesHub: PageSeed = {
  title: 'Services',
  slug: 'services',
  hero: { type: 'page', eyebrow: 'Web development services in NYC', title: 'Web design and development *services*', subtitle: 'Website design, custom development, online stores, web apps and monthly care, all from one New York team.', links: [link('Get a free quote', '/contact'), link('See prices', '/packages')] },
  layout: [servicesBlock({ eyebrow: undefined, heading: undefined, intro: undefined }), processBlock(true), auditBlock()],
  meta: { title: 'Web Design & Development Services NYC | Plen Dev', description: 'Website design, custom web development, online stores, web apps and website care plans for New York small businesses.', keywords: 'web development services NYC', schemaType: 'CollectionPage' },
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
    ...(s.work ? [workBlock({ style: 'grid', heading: 'Recent *websites*' })] : []),
    ...(s.packages ? [{ blockType: 'packagesBlock', eyebrow: 'Prices', heading: `${s.title} *prices*`, groups: s.packages } as Block] : []),
    statementBlock(s.statement, true),
    processBlock(false),
    faq(`${s.title}: *common questions*`, s.faqs),
    auditBlock(),
  ],
  meta: { title: s.metaTitle, description: s.metaDesc, keywords: s.keywords, schemaType: 'Service' },
})

const services: PageSeed[] = [
  servicePage({
    slug: 'web-development', title: 'Web Development', eyebrow: 'Custom web development in NYC',
    h1: 'Custom website development in *NYC*',
    sub: 'We code your website from scratch, so it loads fast, stays secure and is easy for your team to update.',
    answer: 'Plen Dev is a custom web development company in New York. Most websites go live in 2 to 6 weeks, and prices start at $1,499.',
    metaTitle: 'Custom Website Development NYC | Plen Dev', metaDesc: 'Custom website development in NYC. Fast, secure websites you can update yourself. Serving Brooklyn, Queens, Manhattan and Long Island. From $1,499.',
    keywords: 'custom website development NYC, web developer NYC, website redesign NYC',
    featuresHeading: 'Fast, secure and *easy to update*', featuresIntro: 'We write the code ourselves. No page builders and no pile of plugins to keep updated.',
    features: [
      { icon: 'gauge', title: 'Fast on every phone', text: 'Pages open in about 2 seconds on a phone. Google ranks faster sites higher, and customers stay instead of hitting the back button.' },
      { icon: 'database', title: 'Update it yourself', text: 'Change text, photos and prices in a simple editor and see the change before it goes live.' },
      { icon: 'smartphone', title: 'Designed for phones first', text: 'Most of your customers visit on a phone, so that is where we design and test first.' },
      { icon: 'shield', title: 'Hard to hack', text: 'No WordPress plugins for hackers to break into. Secure hosting, SSL and daily backups are included.' },
      { icon: 'bot', title: 'Easy for Google and ChatGPT to read', text: 'We add the behind-the-scenes details that help Google and AI tools understand what you do and where you are.' },
      { icon: 'wrench', title: 'Website redesigns', text: 'Already have a site? We move your content over and keep your Google rankings, so you do not lose traffic.' },
    ],
    statement: 'A slow website sends customers to your *competitors*. Yours should open before they lose interest.',
    packages: ['websites'],
    work: true,
    faqs: [
      ['What do you build websites with?', 'We build with Next.js, the same technology used by Nike, Twitch and many other big brands. It is fast, secure and does not need plugins. Your site can be hosted with us or on your own account.'],
      ['Can you redesign my current website?', 'Yes. Most of our projects are redesigns. We review your current site first, keep what works, move your content and redirect old pages so your Google rankings carry over.'],
      ['Do I own the website?', 'Yes. You own the website, the content, the domain and the hosting account. There is no long contract.'],
      ['Is a custom website more expensive than WordPress?', 'Our websites start at $1,499, about the same as a good WordPress site. You usually save money after launch because there are no paid plugins and far fewer security problems.'],
    ],
  }),
  servicePage({
    slug: 'web-design', title: 'Website Design', eyebrow: 'Small business website design in NYC',
    h1: 'Website design for *NYC small businesses*',
    sub: 'A website that makes your business look established, earns trust fast and turns visitors into phone calls.',
    answer: 'Plen Dev is a web design agency in New York. We design custom websites for small businesses, with packages from $1,499 to $6,999.',
    metaTitle: 'Web Design Agency NYC | Small Business Websites | Plen Dev', metaDesc: 'Website design for New York small businesses. Custom designs that look great on phones and turn visitors into customers. From $1,499.',
    keywords: 'web design agency NYC, small business website design NYC, affordable web design NYC',
    featuresHeading: 'Design that brings in *customers*', featuresIntro: 'Every page is designed around the one thing you want visitors to do: call, book or buy.',
    features: [
      { icon: 'palette', title: 'Made for your business', text: 'Colors, fonts and layout chosen for your brand and your customers. Never a store-bought template.' },
      { icon: 'sparkles', title: 'Smooth animation', text: 'Small touches of movement that make your site feel high-end without slowing it down.' },
      { icon: 'chart', title: 'Built to get calls', text: 'Clear buttons, reviews and short forms placed exactly where people decide to contact you.' },
      { icon: 'smartphone', title: 'Easy on phones', text: 'Big buttons, tap-to-call and short forms, because most visitors are on a phone.' },
      { icon: 'layout', title: 'Always on brand', text: 'Ready-made sections in your editor, so every new page you add matches the rest of the site.' },
      { icon: 'search', title: 'Words people search for', text: 'We write your pages around the words customers type into Google, so the right people find you.' },
    ],
    statement: 'People decide if they trust a business in *a few seconds*. Your website should win that moment.',
    packages: ['websites'],
    work: true,
    faqs: [
      ['How much does website design cost in NYC?', 'Our design and build packages run from $1,499 for a 5-page website to $6,999 for a fully custom 25-page website with animation and online booking. Larger projects start at $12,000.'],
      ['Do you write the words on the website?', 'The Growth package includes writing for 5 pages, and Signature includes writing for every page. You can add writing to any package for $150 per page.'],
      ['How many rounds of changes do I get?', 'Launch includes 2 rounds and Growth includes 3. Signature includes unlimited small changes during the design stage.'],
      ['Can I see the design before you build it?', 'Yes. You click through your main pages on your own phone and computer and approve them before we build anything.'],
    ],
  }),
  servicePage({
    slug: 'custom-cms', title: 'Custom CMS Development', eyebrow: 'Custom CMS development in NYC',
    h1: 'A custom CMS that makes updating your site *easy*',
    sub: 'A CMS is the editor you use to change your website. Ours lets you update any page in minutes, see every inquiry in one place, and control your Google settings without a developer.',
    answer: 'Plen Dev builds custom CMS websites in New York. Our editor shows a live preview of every change, saves every lead, and lets you manage Google settings and tracking codes page by page. Moving an existing site onto it starts at $2,499.',
    metaTitle: 'Custom CMS Development NYC | Plen Dev', metaDesc: 'Custom CMS development in NYC. Update your website yourself with live preview, keep every lead in one inbox, and manage SEO settings without a developer. From $2,499.',
    keywords: 'custom CMS development NYC, headless CMS development, custom CMS development',
    featuresHeading: 'Run your website *without a developer*', featuresIntro: 'Change your hours on Monday, add a new service on Tuesday and see who contacted you on Wednesday. All from one screen.',
    features: [
      { icon: 'layout', title: 'See changes before they go live', text: 'Edit text and photos next to a live preview of the page, then publish when it looks right.' },
      { icon: 'database', title: 'Every lead in one inbox', text: 'Calls back, quote requests and audit requests saved with the page and ad they came from. Mark each one as you follow up.' },
      { icon: 'search', title: 'Google settings on every page', text: 'Set the title and description Google shows, choose the image for social shares, and preview how the page looks in search.' },
      { icon: 'code', title: 'Add tracking codes yourself', text: 'Paste in Google Tag Manager, Meta Pixel, chat widgets or other codes for the whole site or just one page.' },
      { icon: 'shield', title: 'Safe for your whole team', text: 'Give staff their own logins, save drafts, schedule changes and undo any edit with one click.' },
      { icon: 'bot', title: 'Connects to your other tools', text: 'Your CRM, booking system or AI assistant can read and update your website automatically.' },
    ],
    statement: 'If changing your phone number means calling a *developer*, your website is costing you time and money.',
    packages: ['cms-apps'],
    faqs: [
      ['What is a CMS?', 'A CMS (content management system) is the editor you log into to change your website. WordPress is the best-known one. Ours is built for your business, so it only shows the things you actually need to change.'],
      ['What is a headless CMS?', 'A headless CMS keeps your content separate from the design of your website. That makes the site faster and harder to hack, and lets the same content power your website, an app or an AI assistant.'],
      ['Custom CMS or WordPress: which is better for a small business?', 'WordPress is fine for a simple blog. A custom CMS is better if you want a fast, secure site with no plugin updates, an editor that is simple for your staff, and all your leads in one place.'],
      ['Can you move my current website onto your CMS?', 'Yes. The CMS Upgrade package ($2,499) moves your pages onto our editor, keeps your web addresses the same, and adds live preview, the lead inbox and Google settings.'],
      ['Is it hard to learn?', 'No. Most clients are comfortable after one 45-minute training session. You always see a preview, so you know exactly what visitors will see.'],
    ],
  }),
  servicePage({
    slug: 'ecommerce', title: 'Ecommerce Website Development', eyebrow: 'Ecommerce website development in NYC',
    h1: 'Ecommerce websites that *sell* day and night',
    sub: 'Shopify and custom online stores with fast product pages, quick checkout on phones and inventory that stays up to date.',
    answer: 'Plen Dev builds ecommerce websites in New York on Shopify or fully custom. Online stores start at $2,999 for up to 50 products.',
    metaTitle: 'Ecommerce Website Development NYC | Shopify Developer | Plen Dev', metaDesc: 'Ecommerce website development in NYC. Shopify and custom online stores with fast checkout and easy product management. From $2,999.',
    keywords: 'ecommerce website development NYC, Shopify developer NYC, ecommerce website design for small business',
    featuresHeading: 'Online stores built to *sell*', featuresIntro: 'Every choice we make comes back to one question: does it help people buy?',
    features: [
      { icon: 'cart', title: 'Shopify or custom', text: 'Shopify for most stores, or a fully custom store when you need more control.' },
      { icon: 'gauge', title: 'Fast product pages', text: 'Quick filters, sharp photos and an add-to-cart button that works great on phones.' },
      { icon: 'chart', title: 'More sales per visit', text: 'Reviews, bundles, "you may also like" products and reminder emails for abandoned carts.' },
      { icon: 'database', title: 'Easy inventory', text: 'Upload products in bulk and keep stock in sync with your register or warehouse.' },
      { icon: 'search', title: 'Found on Google Shopping', text: 'Your products set up to show in Google search and Google Shopping.' },
      { icon: 'shield', title: 'Payments, shipping and tax', text: 'Credit cards, Apple Pay, Shop Pay, shipping rates and sales tax set up correctly from day one.' },
    ],
    statement: 'Every extra second a store takes to load costs you *sales*. We make yours fast.',
    packages: ['ecommerce'],
    work: true,
    faqs: [
      ['Should I use Shopify or a custom store?', 'Shopify is the right choice for most stores. It has a reliable checkout and is easy to manage. We recommend a custom store for subscriptions, wholesale pricing or complicated product options.'],
      ['How much does an ecommerce website cost?', 'Our Storefront package is $2,999 for up to 50 products. Commerce is $5,999 for up to 500 products. Commerce Pro starts at $11,999.'],
      ['Can you move my store from another platform?', 'Yes. We move your products, customers and order history from WooCommerce, Squarespace, Wix or BigCommerce, and redirect old pages so you keep your Google rankings.'],
    ],
  }),
  servicePage({
    slug: 'web-apps', title: 'Web App Development', eyebrow: 'Custom web application development in NYC',
    h1: 'Custom web apps, portals and *booking systems*',
    sub: 'Customer logins, online booking and dashboards that replace spreadsheets and save your team hours every week.',
    answer: 'Plen Dev builds custom web applications in New York, including customer portals, booking systems, dashboards and startup products. Portals start at $9,999.',
    metaTitle: 'Custom Web Application Development NYC | Plen Dev', metaDesc: 'Custom web application development in NYC: customer portals, booking systems, dashboards and startup products built with React and Next.js.',
    keywords: 'custom web application development NYC, client portal development, React Next.js developer NYC',
    featuresHeading: 'Software that fits how *you* work', featuresIntro: 'When spreadsheets and off-the-shelf apps stop working for you, we build exactly what you need.',
    features: [
      { icon: 'layout', title: 'Customer portals', text: 'Secure logins where customers see files, invoices and the status of their job.' },
      { icon: 'chart', title: 'Dashboards', text: 'Your sales, leads and jobs in one live screen, pulled from the tools you already use.' },
      { icon: 'cpu', title: 'Online booking', text: 'Customers book and pay online. Reminders go out automatically and staff calendars stay in sync.' },
      { icon: 'bot', title: 'AI that saves time', text: 'Assistants that answer common questions, read documents and handle repetitive tasks for your team.' },
    ],
    statement: 'The right software takes the *busywork* off your plate, so your team can focus on customers.',
    packages: ['cms-apps'],
    faqs: [
      ['How much does a custom web app cost?', 'Customer portals start at $9,999. Bigger platforms like marketplaces or startup products start at $19,999. We plan every app with you in a paid planning session first.'],
      ['How long does it take to build a web app?', 'A customer portal takes 6 to 10 weeks. Bigger platforms are released in stages, with a first working version in about 8 to 12 weeks.'],
      ['Who owns the code?', 'You do. At launch we hand over the code, instructions and admin access.'],
    ],
  }),
  servicePage({
    slug: 'website-maintenance', title: 'Website Maintenance', eyebrow: 'Website maintenance services in NYC',
    h1: 'Website maintenance that keeps your site *fast and safe*',
    sub: 'Hosting, backups, security updates and monthly changes for one flat monthly price.',
    answer: 'Plen Dev offers website maintenance plans in New York from $79 per month. Plans include hosting, SSL, daily backups, 24/7 monitoring, security updates and monthly changes.',
    metaTitle: 'Website Maintenance Services NYC | Plen Dev', metaDesc: 'Website maintenance in NYC from $79/month: hosting, backups, security updates, 24/7 monitoring and monthly changes. No long contract.',
    keywords: 'website maintenance services NYC, website support, website security',
    featuresHeading: 'We look after your site, *you* run your business', featuresIntro: 'One monthly plan instead of a hosting bill, a security plugin and a freelancer who never calls back.',
    features: [
      { icon: 'shield', title: 'Security updates', text: 'We keep everything up to date, renew your SSL and watch for attacks.' },
      { icon: 'database', title: 'Daily backups', text: 'A copy of your site saved every day, ready to restore if anything goes wrong.' },
      { icon: 'gauge', title: 'Monthly checkups', text: 'We check your speed and look for problems every month, then send you a short report.' },
      { icon: 'wrench', title: 'Changes included', text: 'Two to six hours of updates each month, depending on your plan. Just email us what you need.' },
    ],
    statement: 'Your website should get *better* every month, not older.',
    packages: ['care'],
    faqs: [
      ['What does website maintenance include?', 'Every plan includes hosting, SSL, daily backups, 24/7 monitoring and security updates. Pro Care adds 2 hours of changes and a monthly checkup. Partner Care adds 6 hours, priority support and testing to improve results.'],
      ['Can you look after a website you did not build?', 'Yes, after a quick review. If the site has serious problems, we will give you a price to fix them first.'],
      ['Is there a contract?', 'No. Plans are month to month. Pay yearly and save 10%.'],
    ],
  }),
]

/* ---- core pages ---- */
const packagesPage: PageSeed = {
  title: 'Packages & Pricing',
  slug: 'packages',
  hero: {
    type: 'page',
    eyebrow: 'Website prices in NYC',
    title: 'Website packages and *prices*',
    subtitle: 'Fixed prices for New York small businesses. Every website includes mobile design, Google basics and an editor to update it yourself.',
    answer: 'Plen Dev websites cost $1,499 to $6,999 for most small businesses. Larger custom websites start at $12,000, online stores at $2,999 and care plans at $79 per month.',
    links: [link('See all prices', '#packages'), link('Get a custom quote', '/contact')],
  },
  layout: [
    { blockType: 'packagesBlock', note: 'Payment: 50% to start and 50% at launch for projects under $5,000. Larger projects are split 40% / 30% / 30%. Monthly plans are billed on the 1st, with 10% off when you pay yearly. Add a yearly care plan to any website and get 10% off the build. All prices in US dollars.' },
    faq('Pricing *questions*', [
      ['How much does a website cost in NYC in 2026?', 'Small business websites in New York usually cost between $2,000 and $15,000. Plen Dev websites start at $1,499 for 5 pages, $3,499 for a 12-page custom site and $6,999 for a fully custom 25-page site.'],
      ['Are there any hidden costs?', 'No. Your price covers design, building, the editor and launch. Hosting and maintenance are optional monthly plans from $79. Domain names and paid outside apps are billed at cost.'],
      ['What comes with every website?', 'An easy editor with live preview, contact forms that save every lead, a design that works on phones, Google basics (page titles, descriptions, sitemap) and setup so AI tools like ChatGPT can read your site.'],
      ['Can I add more later?', 'Yes. You can add pages ($199 each), online booking, an online store or other features at any time.'],
    ]),
    contactForm({ heading: 'Not sure which package is *right for you*?', intro: 'Tell us about your business and we will recommend a package and send you a fixed price.' }),
  ],
  meta: { title: 'Website Design Cost NYC | Packages & Prices | Plen Dev', description: 'How much a website costs in NYC: packages from $1,499, online stores from $2,999 and care plans from $79/month. Clear, fixed prices.', keywords: 'website design cost NYC, web design packages, website pricing NYC', schemaType: 'WebPage' },
}

const auditPage: PageSeed = {
  title: 'Free Website Audit',
  slug: 'website-audit',
  hero: {
    type: 'page',
    eyebrow: 'Free website audit',
    title: 'Free website audit for *NYC businesses*',
    subtitle: 'Find out why your website is not bringing in more customers. We check your speed, your Google visibility and what is broken, then email you a simple list of fixes. It is free, with no strings attached.',
    answer: 'Plen Dev’s free website audit checks how fast your site loads, how it works on phones, how easy it is to find on Google, and whether your forms and links work. A real person reviews it and emails you a list of fixes, usually within one business day.',
    links: [link('Get my free audit', '#audit')],
  },
  layout: [
    auditBlock({ eyebrow: 'Request your free audit', heading: 'Enter your *website address*', dark: false }),
    {
      blockType: 'services',
      dark: true,
      eyebrow: 'What we check',
      heading: 'Checked by a real person, not just *a tool*',
      intro: 'We use the same tools Google uses, then a person on our team reviews every report before it goes to you. You get answers in plain English, not a page of scores.',
      columns: '3',
      items: [
        { icon: 'gauge', title: 'Website speed test', text: 'How long your site takes to load on a phone, and what is slowing it down.' },
        { icon: 'smartphone', title: 'Phone experience', text: 'Whether text is easy to read, buttons are easy to tap and pop-ups get in the way.' },
        { icon: 'search', title: 'Google visibility', text: 'Whether Google can find all your pages, and if your titles and descriptions make people click.' },
        { icon: 'bot', title: 'ChatGPT and AI search', text: 'Whether AI tools can read your business name, services, hours and location correctly.' },
        { icon: 'shield', title: 'Security and errors', text: 'Your SSL certificate, outdated software, broken links and contact forms that do not send.' },
        { icon: 'chart', title: 'Getting more leads', text: 'How easy it is for a visitor to call, book or ask for a quote, and what stops them.' },
      ],
    },
    faq('Free website audit *questions*', [
      ['Is the website audit really free?', 'Yes. There is no cost and no obligation. We email you the report and you decide if you want help with the fixes.'],
      ['How long does it take?', 'Most reports arrive within one business day. Bigger websites can take up to two.'],
      ['What do I need to send you?', 'Just your website address and your email. If you want a more detailed report, you can also give us access to Google Search Console or Google Analytics, but you do not have to.'],
      ['Do I have to be thinking about a website redesign?', 'No. Many business owners just want to know where they stand. If a few small fixes will do the job, we will tell you that.'],
      ['What if my website is already in good shape?', 'Then we will tell you so, and point out the two or three small changes that are still worth making.'],
    ]),
  ],
  meta: { title: 'Free Website Audit & Speed Test | NYC | Plen Dev', description: 'Get a free website audit from a New York web team. We test your speed, phone layout, Google visibility and broken links, and email you a simple fix list.', keywords: 'free website audit, website speed test, website redesign NYC', schemaType: 'WebPage' },
}

const workPage: PageSeed = {
  title: 'Work',
  slug: 'work',
  hero: { type: 'page', eyebrow: 'Web design portfolio', title: 'Our *work*', subtitle: 'Websites for medical practices, real estate agencies, home care agencies, tech companies and online stores. Each one designed from scratch, with an editor the owner can use.' },
  layout: [statementBlock('Want your business to be *next*?', true)],
  meta: { title: 'Web Design Portfolio NYC | Website Examples | Plen Dev', description: 'Website examples from Plen Dev: medical, real estate, home health care, tech and ecommerce websites designed and built in New York.', keywords: 'web design portfolio NYC, website examples', schemaType: 'CollectionPage' },
}

const aboutPage: PageSeed = {
  title: 'About',
  slug: 'about',
  hero: {
    type: 'page',
    eyebrow: 'About Plen Dev',
    title: 'A New York web team that *picks up the phone*',
    subtitle: 'Plen Dev is a web design and development company in New York. We build custom websites for small businesses and teach you to run them yourself.',
    answer: 'Plen Dev is a web development company based in New York, serving Brooklyn, Queens, Manhattan and Long Island. We design and build custom websites, online stores and web apps.',
    links: [link('Get a free quote', '/contact'), link('See our work', '/work')],
  },
  layout: [
    statementBlock('Small businesses deserve websites as good as the *big brands* they compete with.'),
    {
      blockType: 'services', dark: true, eyebrow: 'How we work', heading: 'What you can *count on*', columns: '2',
      items: [
        { icon: 'sparkles', title: 'Designed from scratch', text: 'No store-bought themes. Every site starts with your customers and what you want them to do.' },
        { icon: 'code', title: 'Built by us', text: 'We write the code ourselves. That is why our sites are fast and easy to add to later.' },
        { icon: 'database', title: 'You stay in control', text: 'You own the website, domain and content, and you can change anything yourself.' },
        { icon: 'map', title: 'Local and easy to reach', text: 'Based in New York. We meet clients across the five boroughs and Long Island.' },
      ],
    },
    processBlock(false),
    areasBlock(),
    contactForm(),
  ],
  meta: { title: 'About Plen Dev | Web Developer in New York', description: 'Plen Dev is a New York web design and development company building custom websites for small businesses in Brooklyn, Queens, NYC and Long Island.', keywords: 'Plen Dev, web developer New York', schemaType: 'AboutPage' },
}

const contactPage: PageSeed = {
  title: 'Contact',
  slug: 'contact',
  hero: {
    type: 'page',
    eyebrow: 'Contact us',
    title: 'Talk to a web developer *near you*',
    subtitle: 'Email info@plendev.com or fill out the form below. We reply within one business day.',
    answer: 'Contact Plen Dev at info@plendev.com for website design, web development, online stores or custom CMS projects in Brooklyn, Queens, NYC and Long Island.',
  },
  layout: [contactForm({ dark: false, eyebrow: 'Your project' }), areasBlock({ dark: true })],
  meta: { title: 'Contact Plen Dev | Web Developer Near You in NYC', description: 'Get a website quote from Plen Dev. Web design and development for businesses in Brooklyn, Queens, NYC and Long Island. Reply within one business day.', keywords: 'web developer near me, contact Plen Dev', schemaType: 'ContactPage' },
}

/* ---- locations ---- */
type LocSpec = {
  slug: string
  parent?: string
  title: string
  place: string
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
  hero: { type: 'page', eyebrow: l.eyebrow, title: l.h1, subtitle: l.sub, answer: l.answer, links: [link('Free website audit', '/website-audit'), link('See prices', '/packages')] },
  layout: [
    marquee(l.neighborhoods, 'small'),
    servicesBlock({ eyebrow: `Services in ${l.place}`, heading: `Websites for *${l.place}* businesses`, intro: l.industries }),
    workBlock({ style: 'grid', dark: true, heading: 'Recent *websites*' }),
    { blockType: 'packagesBlock', eyebrow: 'Prices', heading: `Website prices in *${l.place}*`, groups: ['websites'], note: 'Online stores, custom CMS and care plans are on the full prices page.' },
    statementBlock(l.why, true),
    ...(l.areas ? [l.areas] : []),
    faq(`${l.place} web design *questions*`, l.faqs),
    auditBlock(),
  ],
  meta: { title: l.metaTitle, description: l.metaDesc, keywords: l.keywords, schemaType: 'Service' },
})

const locationsHub: PageSeed = {
  title: 'Locations',
  slug: 'locations',
  hero: { type: 'page', eyebrow: 'Areas we serve', title: 'Web design across *New York*', subtitle: 'We build websites for businesses in Brooklyn, Queens, the rest of NYC and Long Island, and we meet in person.' },
  layout: [areasBlock({ eyebrow: undefined, heading: undefined, intro: undefined }), auditBlock()],
  meta: { title: 'Web Design in Brooklyn, Queens, NYC & Long Island | Plen Dev', description: 'Plen Dev builds websites for businesses in Brooklyn, Queens, New York City and Long Island (Nassau and Suffolk County).', keywords: 'web design New York locations', schemaType: 'CollectionPage' },
}

const locations: PageSeed[] = [
  locationPage({
    slug: 'brooklyn', title: 'Web Design Brooklyn', place: 'Brooklyn', eyebrow: 'Brooklyn, NY',
    h1: '*Brooklyn* web design and development',
    sub: 'Fast, custom websites for Brooklyn restaurants, shops, medical offices, contractors and studios, from Williamsburg to Bay Ridge.',
    answer: 'Plen Dev is a Brooklyn web design company. We build custom websites for Brooklyn small businesses, starting at $1,499, and meet in person anywhere in the borough.',
    metaTitle: 'Web Design Brooklyn, NY | Web Developer in Brooklyn | Plen Dev', metaDesc: 'Brooklyn web design and development. Custom small business websites you can update yourself, from $1,499. Get a free website audit.',
    keywords: 'web design Brooklyn, Brooklyn web design company, web developer Brooklyn, web development company Brooklyn',
    why: 'Brooklyn customers *compare* businesses online before they call. Your website should make you the easy choice.',
    neighborhoods: ['Williamsburg', 'Greenpoint', 'Park Slope', 'DUMBO', 'Brooklyn Heights', 'Bushwick', 'Bay Ridge', 'Crown Heights', 'Sunset Park', 'Bed-Stuy'],
    industries: 'We build for Brooklyn restaurants and cafes, medical and dental offices, salons and gyms, contractors, real estate agents and local shops.',
    faqs: [
      ['How much does a website cost in Brooklyn?', 'Plen Dev websites for Brooklyn businesses start at $1,499 for a 5-page site. Most custom small business websites cost $3,499 to $6,999.'],
      ['Can we meet in person in Brooklyn?', 'Yes. We meet clients at their business or a coffee shop anywhere in Brooklyn for the first meeting and for training.'],
      ['Will my Brooklyn business show up on Google Maps and local search?', 'We set up every site for local search: your address and hours marked up for Google, a link to your Google Business Profile, fast phone pages and your sitemap sent to Google at launch.'],
    ],
  }),
  locationPage({
    slug: 'queens', title: 'Web Design Queens', place: 'Queens', eyebrow: 'Queens, NY',
    h1: '*Queens* web design and development',
    sub: 'Websites for Queens businesses in Astoria, Long Island City, Flushing, Forest Hills, Jamaica and beyond, in more than one language if you need it.',
    answer: 'Plen Dev is a web design and development company serving Queens, NY, including Astoria, Long Island City, Flushing, Forest Hills, Jamaica and Bayside. Websites start at $1,499 and can be built in multiple languages.',
    metaTitle: 'Web Design Queens, NY | Web Developer in Queens | Plen Dev', metaDesc: 'Queens web design and development. Custom websites in one or more languages for businesses in Astoria, LIC, Flushing and Forest Hills. From $1,499.',
    keywords: 'web design Queens NY, web development company Queens, web developer Queens NY, website designer Queens',
    why: 'Your Queens customers may search in *English, Spanish, Chinese or Bengali*. Your website can speak to all of them.',
    neighborhoods: ['Astoria', 'Long Island City', 'Flushing', 'Forest Hills', 'Jackson Heights', 'Jamaica', 'Bayside', 'Sunnyside', 'Ridgewood', 'Elmhurst'],
    industries: 'We build for Queens home care agencies, medical and dental offices, restaurants, law and immigration offices, contractors and stores.',
    faqs: [
      ['Can you build a website in more than one language?', 'Yes. You can publish pages in English, Spanish, Chinese, Korean, Bengali or any other language, and update each version yourself.'],
      ['How much does a website cost in Queens?', 'Plen Dev websites start at $1,499 for 5 pages. A 12-page custom site with writing included is $3,499.'],
      ['Do you work with home care agencies in Queens?', 'Yes. We build home care websites with pages for each area you serve, caregiver job applications and private intake forms.'],
    ],
  }),
  locationPage({
    slug: 'new-york-city', title: 'New York City Web Development', place: 'New York City', eyebrow: 'New York City',
    h1: 'Web development company in *New York City*',
    sub: 'Custom websites, online stores and web apps for businesses in Manhattan, the Bronx, Staten Island, Brooklyn and Queens.',
    answer: 'Plen Dev is a web development company in New York City. We build custom websites, online stores and web apps for NYC businesses, starting at $1,499.',
    metaTitle: 'Web Development Company NYC | Website Design New York | Plen Dev', metaDesc: 'New York City web development company. Custom websites, online stores and web apps for NYC businesses, with fixed prices from $1,499.',
    keywords: 'web development company New York, website design New York, web design company NYC',
    why: 'New York is the toughest market in the country. A *generic* website will not stand out here.',
    neighborhoods: ['Manhattan', 'Midtown', 'Financial District', 'Upper West Side', 'Harlem', 'The Bronx', 'Staten Island', 'Brooklyn', 'Queens'],
    industries: 'We build for NYC law firms and other professional services, healthcare, real estate, restaurants and hotels, startups and growing online brands.',
    faqs: [
      ['What makes Plen Dev different from other NYC web design companies?', 'You get custom design, a website you can update yourself, and a fixed price that is published on our site. Your site is fast, easy to change and 100% yours.'],
      ['Do you work with startups?', 'Yes. We build websites and first versions of products for startups, using technology that can grow with the company.'],
      ['How fast can you launch?', 'A 5-page website can go live in about 2 weeks. Most custom websites go live in 4 to 6 weeks.'],
    ],
  }),
  locationPage({
    slug: 'long-island', title: 'Web Design Long Island', place: 'Long Island', eyebrow: 'Long Island, NY',
    h1: '*Long Island* web design and development',
    sub: 'Websites for Nassau County and Suffolk County businesses that want to look established and win more local customers.',
    answer: 'Plen Dev is a Long Island web development company serving Nassau County and Suffolk County. We build custom websites for local businesses, starting at $1,499.',
    metaTitle: 'Web Design Long Island, NY | Web Developer Long Island | Plen Dev', metaDesc: 'Long Island web design and development for Nassau and Suffolk County businesses. Custom websites you can update yourself, from $1,499.',
    keywords: 'web design Long Island, Long Island web development company, web developer Long Island',
    why: 'Long Island customers search *close to home* and decide fast. Your website needs to win that first visit.',
    neighborhoods: ['Garden City', 'Hicksville', 'Mineola', 'Massapequa', 'Great Neck', 'Huntington', 'Smithtown', 'Hauppauge', 'Patchogue', 'Riverhead'],
    industries: 'We build for Long Island contractors and home services, medical and dental offices, real estate agents, law firms, landscapers and stores.',
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
      ['Do you meet clients on Long Island?', 'Yes. We meet clients in person across Nassau and Suffolk County for the first meeting and for training.'],
      ['How much does a website cost on Long Island?', 'Plen Dev websites start at $1,499. Most Long Island small business websites cost between $3,499 and $6,999.'],
      ['Do you build websites for contractors and home service companies?', 'Yes. We build contractor websites with pages for each town you serve, photo galleries of your work, quote forms and tap-to-call on phones.'],
    ],
  }),
  locationPage({
    slug: 'nassau-county', parent: 'long-island', title: 'Website Design in Nassau County', place: 'Nassau County', eyebrow: 'Nassau County, NY',
    h1: 'Website design in *Nassau County*',
    sub: 'Custom websites for businesses in Garden City, Hicksville, Mineola, Massapequa, Great Neck and across Nassau County.',
    answer: 'Plen Dev designs and builds websites for Nassau County businesses in Garden City, Hicksville, Mineola, Massapequa, Great Neck and more, starting at $1,499.',
    metaTitle: 'Website Design Nassau County, NY | Plen Dev', metaDesc: 'Website design in Nassau County, NY. Custom websites for businesses in Garden City, Hicksville, Massapequa and Great Neck. From $1,499.',
    keywords: 'website design Nassau County, web design Garden City, web design Hicksville, web design Massapequa',
    why: 'Nassau businesses compete with *Manhattan* companies one train ride away. Your website should look the part.',
    neighborhoods: ['Garden City', 'Hicksville', 'Mineola', 'Massapequa', 'Great Neck', 'Freeport', 'Levittown', 'Valley Stream', 'Rockville Centre', 'Westbury'],
    industries: 'We build for Nassau County medical and dental offices, law firms, contractors, real estate agencies, restaurants and stores.',
    faqs: [
      ['Which towns in Nassau County do you serve?', 'All of them, including Garden City, Hicksville, Mineola, Massapequa, Great Neck, Freeport, Levittown and Rockville Centre.'],
      ['How long does a website take?', 'Most websites go live in 2 to 6 weeks, depending on the package.'],
    ],
  }),
  locationPage({
    slug: 'suffolk-county', parent: 'long-island', title: 'Website Design in Suffolk County', place: 'Suffolk County', eyebrow: 'Suffolk County, NY',
    h1: 'Website design in *Suffolk County*',
    sub: 'Custom websites for businesses in Huntington, Smithtown, Hauppauge, Patchogue, Riverhead and across Suffolk County.',
    answer: 'Plen Dev designs and builds websites for Suffolk County businesses in Huntington, Smithtown, Hauppauge, Patchogue, Riverhead and more, starting at $1,499.',
    metaTitle: 'Website Design Suffolk County, NY | Plen Dev', metaDesc: 'Website design in Suffolk County, NY. Custom websites for businesses in Huntington, Smithtown, Hauppauge and Riverhead. From $1,499.',
    keywords: 'website design Suffolk County, web design Huntington, web design Smithtown, web design Hauppauge',
    why: 'From Huntington to the *Hamptons*, your website is where most customers meet you first.',
    neighborhoods: ['Huntington', 'Smithtown', 'Hauppauge', 'Patchogue', 'Riverhead', 'Babylon', 'Islip', 'Port Jefferson', 'Stony Brook', 'Southampton'],
    industries: 'We build for Suffolk County contractors and home services, marinas, restaurants and hotels, wineries, medical offices and professional services.',
    faqs: [
      ['Which towns in Suffolk County do you serve?', 'All of Suffolk County, including Huntington, Smithtown, Hauppauge, Patchogue, Islip, Riverhead and the East End.'],
      ['Do you build websites for seasonal businesses?', 'Yes. You can change seasonal menus, hours and specials yourself, without calling us.'],
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
  hero: { type: 'page', eyebrow: `${i.title} websites`, title: i.h1, subtitle: i.sub, answer: i.answer, links: [link('See the example', `/work/${i.project}`), link('Get a free quote', '/contact')] },
  layout: [
    workBlock({ source: 'pick', projects: [i.project], heading: 'A recent *website*', intro: undefined, eyebrow: 'Example' }),
    { blockType: 'services', eyebrow: `Built for ${i.title.toLowerCase()}`, heading: 'What your website *does* for you', items: i.features, columns: '2' },
    { blockType: 'packagesBlock', eyebrow: 'Prices', heading: 'Website *packages*', groups: [i.slug === 'ecommerce' ? 'ecommerce' : 'websites'] },
    statementBlock(i.statement, true),
    faq(`${i.title} website *questions*`, i.faqs),
    auditBlock(),
  ],
  meta: { title: i.metaTitle, description: i.metaDesc, keywords: i.keywords, schemaType: 'Service' },
})

const industriesHub: PageSeed = {
  title: 'Industries',
  slug: 'industries',
  hero: { type: 'page', eyebrow: 'Industries', title: 'Websites built for *your* industry', subtitle: 'We know what patients, home buyers, families and shoppers look for before they pick up the phone.' },
  layout: [
    {
      blockType: 'services', heading: undefined, columns: '3',
      items: [
        { icon: 'heart', title: 'Medical practices', text: 'Online booking, insurance info, doctor profiles and patient portal links.', href: '/industries/medical-practices' },
        { icon: 'home', title: 'Real estate', text: 'Live listings, agent pages and forms that bring in buyers and sellers.', href: '/industries/real-estate' },
        { icon: 'heart', title: 'Home health care', text: 'Clear services, family inquiries and caregiver hiring.', href: '/industries/home-healthcare' },
        { icon: 'cpu', title: 'Tech and software', text: 'Clear product pages, pricing and help docs.', href: '/industries/tech' },
        { icon: 'cart', title: 'Online stores', text: 'Fast stores that turn browsers into buyers.', href: '/industries/ecommerce' },
      ],
    },
    workBlock({ source: 'all', style: 'grid', dark: true }),
    auditBlock(),
  ],
  meta: { title: 'Website Design by Industry | Plen Dev', description: 'Websites for medical practices, real estate agencies, home health care, tech companies and online stores, designed and built in New York.', keywords: 'industry website design NYC', schemaType: 'CollectionPage' },
}

const industries: PageSeed[] = [
  industryPage({
    slug: 'medical-practices', title: 'Medical Practices', project: 'northbridge-medical',
    h1: 'Medical practice websites that bring in *new patients*',
    sub: 'Websites for doctors and medical offices in NYC, with online booking, insurance info and doctor profiles that answer patient questions before they call.',
    answer: 'Plen Dev designs medical practice websites in NYC for primary care, pediatrics, specialists, dental offices, urgent care and practices with more than one location. Every site includes online booking, insurance pages, doctor profiles and private intake forms. Medical websites start at $3,499.',
    metaTitle: 'Medical Practice Website Design NYC | Doctor Websites | Plen Dev', metaDesc: 'Medical practice website design in NYC. Online booking, insurance info, doctor profiles and location pages that bring in new patients.',
    keywords: 'medical practice website design NYC, doctor website design, healthcare website design, clinic website, dental website design',
    features: [
      { icon: 'cpu', title: 'Online booking and video visits', text: 'Connect the scheduling and telehealth tools you already use, or get appointment requests by email.' },
      { icon: 'heart', title: 'A page for every service', text: 'Primary care, pediatrics, cardiology, dental and more, each written to answer what patients actually ask.' },
      { icon: 'shield', title: 'Insurance info and private forms', text: 'A clear list of the insurance you accept, and patient health details kept out of regular website forms.' },
      { icon: 'map', title: 'Found on Google Maps', text: 'A page for each office with hours and directions, linked to your Google Business Profile.' },
    ],
    statement: 'Patients pick a doctor they *trust*. Your website should earn that trust before the first visit.',
    faqs: [
      ['What should a medical practice website have?', 'Online booking, the insurance you accept, a page for each service, doctor profiles with photos and languages spoken, office hours and directions, patient portal links, reviews and tap-to-call on phones.'],
      ['Can patients book appointments online?', 'Yes. We connect your website to popular medical scheduling and telehealth tools, or send booking requests to your inbox.'],
      ['Is the website HIPAA compliant?', 'We keep private health information out of regular website forms, and connect secure, HIPAA-compliant intake and patient portal tools when you need them.'],
      ['Do you build websites for dentists and specialists too?', 'Yes. We build websites for dental offices, physical therapy, dermatology, urgent care and multi-specialty groups.'],
    ],
  }),
  industryPage({
    slug: 'real-estate', title: 'Real Estate', project: 'kestrel-row-realty',
    h1: 'Real estate websites with *live listings*',
    sub: 'Websites for brokerages and agents, with MLS listings, neighborhood guides and forms that send leads straight to your CRM.',
    answer: 'Plen Dev builds real estate websites in NYC and Long Island with MLS listing search, agent profiles, neighborhood guides and lead forms connected to your CRM.',
    metaTitle: 'Real Estate Website Design NYC & Long Island | Plen Dev', metaDesc: 'Real estate website design in NYC and Long Island. MLS listings, agent pages, neighborhood guides and lead forms connected to your CRM.',
    keywords: 'real estate website design NYC, IDX website, realtor website',
    features: [
      { icon: 'home', title: 'Live MLS listings', text: 'Buyers search homes on your site with a map, save searches and get email alerts. No need to send them to Zillow.' },
      { icon: 'map', title: 'Neighborhood guides', text: 'Local pages that show up when people search "homes for sale in" your towns.' },
      { icon: 'database', title: 'More seller and buyer leads', text: 'Showing requests and "What is my home worth?" forms go straight to your CRM.' },
      { icon: 'layout', title: 'Agent pages', text: 'Each agent can update their own profile and listings.' },
    ],
    statement: 'Buyers scroll listings on their *phones* late at night. Your listings should look great there.',
    faqs: [
      ['What is an IDX website?', 'IDX lets your website show MLS listings automatically, so visitors can search homes on your site instead of on Zillow.'],
      ['Can agents update their own pages?', 'Yes. Each agent can have a login that only lets them change their own profile and listings.'],
      ['Do you connect to real estate CRMs?', 'Yes, including Follow Up Boss, kvCORE and HubSpot.'],
    ],
  }),
  industryPage({
    slug: 'home-healthcare', title: 'Home Healthcare', project: 'hearthside-home-care',
    h1: 'Websites for *home care* agencies',
    sub: 'Home health care websites that reassure families, explain your services clearly and help you hire caregivers.',
    answer: 'Plen Dev builds home health care websites for agencies in NYC and Long Island, with clear service pages, family inquiry forms, caregiver hiring and pages in more than one language.',
    metaTitle: 'Home Health Care Website Design NY | Plen Dev', metaDesc: 'Home health care website design for agencies in New York. Clear service pages, family inquiries, caregiver hiring and multiple languages.',
    keywords: 'home health care website design, home care agency marketing NY, caregiver recruiting website',
    features: [
      { icon: 'heart', title: 'Written for families', text: 'Warm, clear pages that answer the questions families have when they are worried and searching late at night.' },
      { icon: 'database', title: 'Hire caregivers', text: 'Job listings and applications that come straight to your inbox.' },
      { icon: 'map', title: 'Pages for every area you serve', text: 'Borough and county pages so families nearby can find you on Google.' },
      { icon: 'smartphone', title: 'More than one language', text: 'Publish pages in the languages your clients and caregivers speak.' },
    ],
    statement: 'Families are making one of the *hardest decisions* of their lives. Your website should make it easier.',
    faqs: [
      ['What should a home care agency website have?', 'Clear service descriptions, the areas you serve, insurance and Medicaid information, a simple contact form, caregiver job listings and phone numbers that are easy to tap.'],
      ['Can the website help us hire caregivers?', 'Yes. We add a careers page where caregivers can apply, and every application comes straight to you.'],
      ['Can the website be in more than one language?', 'Yes. You can have a separate version of every page in each language and update them yourself.'],
    ],
  }),
  industryPage({
    slug: 'tech', title: 'Tech & SaaS', project: 'relaywave',
    h1: 'Websites for *tech and software* companies',
    sub: 'Websites that make your product easy to understand, with pricing, help docs and product updates your team can change anytime.',
    answer: 'Plen Dev designs and builds websites for tech startups and software companies in NYC, with product pages, pricing, help docs and an editor for the marketing team.',
    metaTitle: 'Tech Startup & SaaS Website Design NYC | Plen Dev', metaDesc: 'Website design for NYC tech startups and SaaS companies. Clear product pages, pricing, help docs and an editor your marketing team controls.',
    keywords: 'tech startup website design NYC, SaaS website design agency',
    features: [
      { icon: 'sparkles', title: 'Show how it works', text: 'Interactive sections and animation that explain your product in seconds.' },
      { icon: 'chart', title: 'Pricing and signup', text: 'Clear pricing pages, comparison tables and a signup flow that gets people started.' },
      { icon: 'code', title: 'Help docs and updates', text: 'Help docs, product updates and your blog, all in one editor.' },
      { icon: 'gauge', title: 'Your engineers can help', text: 'Built with Next.js, so your own developers can work on it too.' },
    ],
    statement: 'Great products lose sales to competitors with *clearer* websites. Let us make yours the clear one.',
    faqs: [
      ['Do you work with early-stage startups?', 'Yes. We often launch a startup website in 2 to 3 weeks and add to it as the company grows.'],
      ['Can our engineers work on the code?', 'Yes. It is a standard Next.js and TypeScript project that lives in your own GitHub account.'],
      ['Do you design the product itself?', 'We design websites, and we can build dashboards and customer portals through our web app service.'],
    ],
  }),
  industryPage({
    slug: 'ecommerce', title: 'Ecommerce', project: 'saltgrain-ceramics',
    h1: 'Ecommerce websites for *small businesses*',
    sub: 'Beautiful, fast online stores for makers and product brands, on Shopify or fully custom.',
    answer: 'Plen Dev designs ecommerce websites for small businesses and product brands, on Shopify or fully custom, starting at $2,999.',
    metaTitle: 'Ecommerce Website Design for Small Business | Plen Dev', metaDesc: 'Ecommerce website design for small businesses. Shopify or custom online stores with fast checkout, from $2,999.',
    keywords: 'ecommerce website design for small business, Shopify store design',
    features: [
      { icon: 'cart', title: 'Fast checkout', text: 'Shop Pay, Apple Pay and a checkout with as few steps as possible.' },
      { icon: 'palette', title: 'Looks like your brand', text: 'Product pages designed around your products, not a theme everyone else uses.' },
      { icon: 'database', title: 'Easy product updates', text: 'Upload products in bulk and manage sizes, colors and collections in one place.' },
      { icon: 'chart', title: 'Tools to sell more', text: 'Reviews, bundles, email signups and reminder emails for abandoned carts.' },
    ],
    statement: 'Your products are *one of a kind*. Your store should be too.',
    faqs: [
      ['How much does an ecommerce website cost for a small business?', 'Our Storefront package is $2,999 for up to 50 products. Most growing brands choose Commerce at $5,999.'],
      ['Shopify or custom?', 'Shopify works for most stores. Custom makes sense for subscriptions, wholesale pricing or unusual products.'],
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
  { group: 'websites', order: 1, name: 'Launch', price: 1499, billing: 'one-time', tagline: 'New businesses and solo practices', scope: 'Up to 5 pages', timeline: '2-week delivery', features: ['Design based on our proven layouts', 'Easy editor with live preview', 'Contact forms that save every lead', 'Google Business Profile setup', 'Google basics: titles, descriptions, sitemap', '2 revision rounds'] },
  { group: 'websites', order: 2, name: 'Growth', price: 3499, billing: 'one-time', tagline: 'Established local businesses', scope: 'Up to 12 pages', timeline: '4-week delivery', highlighted: true, features: ['Fully custom design', 'Copywriting for 5 pages', 'Blog', 'Google business details markup', 'Extra speed tuning', 'Google Analytics 4 & Search Console', '1 location page', '3 revision rounds'] },
  { group: 'websites', order: 3, name: 'Signature', price: 6999, billing: 'one-time', tagline: 'Multi-location or competitive markets', scope: 'Up to 25 pages', timeline: '6 to 8 weeks', features: ['Custom design with animation', 'Full copywriting', 'Booking or quote system', '4 location or industry pages', 'CRM integration', 'Multilingual option', '90 days of support'] },
  { group: 'websites', order: 4, name: 'Enterprise', price: 12000, pricePrefix: 'From', billing: 'one-time', tagline: 'Larger companies, complex needs', scope: 'Unlimited pages', timeline: 'Scoped', ctaLabel: 'Book a call', features: ['Discovery workshop', 'Design system', 'Custom integrations', 'Role-based CMS', 'ADA accessibility check (WCAG 2.2 AA)', 'Dedicated project manager'] },
  { group: 'ecommerce', order: 10, name: 'Storefront', price: 2999, billing: 'one-time', tagline: 'Launch your first store', scope: 'Up to 50 products', features: ['Shopify or custom store', 'Payments, shipping & tax setup', 'Product SEO', 'Mobile-first product pages'] },
  { group: 'ecommerce', order: 11, name: 'Commerce', price: 5999, billing: 'one-time', tagline: 'Growing product brands', scope: 'Up to 500 products', highlighted: true, features: ['Custom theme', 'Reviews', 'Abandoned-cart emails', 'Bulk CSV upload', 'Google Merchant Center'] },
  { group: 'ecommerce', order: 12, name: 'Commerce Pro', price: 11999, pricePrefix: 'From', billing: 'one-time', tagline: 'Complex catalogs and B2B', scope: 'Unlimited products', ctaLabel: 'Book a call', features: ['Subscriptions', 'B2B / wholesale pricing', 'ERP or inventory integration', 'Multi-currency'] },
  { group: 'cms-apps', order: 20, name: 'CMS Upgrade', price: 2499, billing: 'one-time', tagline: 'Move your site onto our easy editor', features: ['Live-preview editing', 'Lead inbox', 'Tracking codes on any page', 'Google settings on every page', 'Content migration'] },
  { group: 'cms-apps', order: 21, name: 'Client Portal', price: 9999, pricePrefix: 'From', billing: 'one-time', tagline: 'Logins, dashboards and files', highlighted: true, ctaLabel: 'Book a call', features: ['User accounts', 'Dashboards', 'File sharing', 'Admin panel', '180 days of support'] },
  { group: 'cms-apps', order: 22, name: 'Custom Platform', price: 19999, pricePrefix: 'From', billing: 'one-time', tagline: 'Marketplaces, booking, SaaS MVPs', ctaLabel: 'Book a call', features: ['Discovery & scoping', 'Marketplace, booking platform or SaaS MVP', 'Phased releases'] },
  { group: 'care', order: 30, name: 'Essential Care', price: 79, billing: 'monthly', tagline: 'Keep it online and safe', features: ['Managed hosting', 'SSL', 'Daily backups', 'Uptime monitoring', 'Security updates'] },
  { group: 'care', order: 31, name: 'Pro Care', price: 199, billing: 'monthly', tagline: 'Most small businesses', highlighted: true, features: ['Everything in Essential', '2 hours of edits per month', 'Speed & site health checks', 'Monthly report'] },
  { group: 'care', order: 32, name: 'Partner Care', price: 449, billing: 'monthly', tagline: 'Sites that keep evolving', features: ['Everything in Pro', '6 hours of edits per month', 'Priority support', 'Quarterly design refresh', 'A/B testing'] },
  { group: 'addons', order: 40, name: 'Free website audit', price: 0, billing: 'one-time', tagline: 'Speed, phone, Google and lead review' },
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
    slug: 'northbridge-medical', title: 'Northbridge Medical Group', industry: 'Medical practice', location: 'Forest Hills, Queens', year: '2026', accent: '#2563eb', domain: 'northbridgemed.com', order: 1,
    summary: 'A modern website for a multi-specialty medical group, with online booking, telehealth, a patient portal and two Queens locations.',
    challenge: 'A growing primary and specialty care group with two offices had an outdated site that sent every booking, insurance and lab question to an overloaded phone line.',
    solution: 'A clear, trustworthy design with booking from the first screen, specialty pages written around patient questions, doctor profiles with languages spoken, location pages and portal links, all editable in the CMS.',
    services: ['Website design', 'Development', 'Easy editor', 'Online booking'],
    results: [{ value: '1 tap', label: 'to book or start a video visit' }, { value: '2', label: 'locations managed in the CMS' }],
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
    summary: 'A warm, reassuring website for a licensed home care agency, with service pages, family inquiries and caregiver recruiting.',
    challenge: 'A family-run home care agency needed to reassure worried families and recruit caregivers from the same website.',
    solution: 'Soft colors, plain-language service pages, a “Talk to a care coordinator” form, borough service areas and a careers section with applications flowing into the CMS.',
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
- **You want leads in one place.** Our CMS saves every form submission in a lead inbox with source and campaign data.

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

1. Your main content loads in under 2.5 seconds on a phone.
2. Nothing jumps around while the page loads.
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

16. A clear "Call" or "Book" button on the first screen.
17. Forms that actually send (test them!).
18. Reviews or proof near the call to action.
19. Prices or price ranges where customers expect them.
20. Analytics tracking form submissions as conversions.

Want us to run this for you? Request a [free website audit](/website-audit) and we’ll email a prioritized report, or see our [website maintenance plans](/services/website-maintenance).`,
  },
]
