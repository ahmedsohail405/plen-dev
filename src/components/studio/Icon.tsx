import {
  Accessibility, Bot, Code2, Headset, KeyRound, Lock, TrendingUp, Zap, Cpu, Database, Gauge, HeartPulse, Home, LayoutTemplate, LineChart, MapPin, Palette, Search, ShieldCheck, ShoppingCart, Smartphone, Sparkles, Smile, Wrench,
} from 'lucide-react'
import React from 'react'

const map = {
  code: Code2, palette: Palette, database: Database, cart: ShoppingCart, search: Search, sparkles: Sparkles, shield: ShieldCheck, gauge: Gauge,
  layout: LayoutTemplate, smartphone: Smartphone, map: MapPin, bot: Bot, chart: LineChart, wrench: Wrench, tooth: Smile, home: Home, heart: HeartPulse, cpu: Cpu,
  zap: Zap, trending: TrendingUp, lock: Lock, accessibility: Accessibility, key: KeyRound, headset: Headset,
}

export const Icon: React.FC<{ name?: string | null; size?: number }> = ({ name, size = 24 }) => {
  const C = map[(name || 'code') as keyof typeof map] || Code2
  return <C size={size} strokeWidth={1.6} aria-hidden />
}

export const Arrow = () => (
  <svg className="arrow" width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden>
    <path d="M3 11L11 3M11 3H4.5M11 3V9.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
  </svg>
)
