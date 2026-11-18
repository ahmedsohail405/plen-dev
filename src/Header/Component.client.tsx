'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import React, { useEffect, useState } from 'react'

import type { Header } from '@/payload-types'
import { docHref } from '@/utilities/docHref'
import { Arrow } from '@/components/studio/Icon'

export const Logo = () => (
  <Link href="/" className="logo" aria-label="Plen Dev home">
    {/* eslint-disable-next-line @next/next/no-img-element */}
    <img src="/brand/plendev-wordmark-dark.svg" alt="Plen Dev" width={118} height={28} />
  </Link>
)

const hrefOf = (link: NonNullable<Header['navItems']>[number]['link']) =>
  link.type === 'reference' && link.reference && typeof link.reference.value === 'object'
    ? docHref(link.reference.relationTo, link.reference.value as { slug?: string; path?: string })
    : link.url

export const HeaderClient: React.FC<{ data: Header }> = ({ data }) => {
  const pathname = usePathname()
  const [open, setOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => setOpen(false), [pathname])
  useEffect(() => {
    const on = () => setScrolled(window.scrollY > 20)
    on()
    window.addEventListener('scroll', on, { passive: true })
    return () => window.removeEventListener('scroll', on)
  }, [])
  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : ''
  }, [open])

  const items = (data?.navItems || []).map(({ link }) => ({ label: link.label, href: hrefOf(link) || '#' }))
  const cta = data?.cta?.href ? data.cta : { label: 'Free website audit', href: '/website-audit' }

  return (
    <>
      <header className={`site-header ${scrolled ? 'is-scrolled' : ''}`}>
        <div className="wrap">
          <div className="bar">
            <Logo />
            <nav className="nav" aria-label="Main">
              {items.map((it) => (
                <Link key={it.href} href={it.href} aria-current={pathname === it.href || (it.href !== '/' && pathname.startsWith(it.href + '/')) ? 'page' : undefined}>
                  {it.label}
                </Link>
              ))}
              <Link href={cta.href || '/website-audit'} className="btn btn--lime nav-cta">
                {cta.label} <Arrow />
              </Link>
            </nav>
            <button className="menu-toggle" aria-expanded={open} aria-controls="mobile-menu" onClick={() => setOpen(!open)}>
              {open ? 'Close' : 'Menu'}
            </button>
          </div>
        </div>
      </header>
      <div id="mobile-menu" className={`mobile-menu ${open ? 'open' : ''}`} aria-hidden={!open}>
        {items.map((it) => (
          <Link key={it.href} href={it.href} tabIndex={open ? 0 : -1}>
            {it.label}
          </Link>
        ))}
        <Link href={cta.href || '/website-audit'} className="btn btn--lime" tabIndex={open ? 0 : -1}>
          {cta.label} <Arrow />
        </Link>
      </div>
    </>
  )
}
