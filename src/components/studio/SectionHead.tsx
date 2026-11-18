import React from 'react'
import { Hl } from './Hl'

export const SectionHead: React.FC<{ eyebrow?: string | null; heading?: string | null; intro?: string | null; children?: React.ReactNode }> = ({ eyebrow, heading, intro, children }) => {
  if (!eyebrow && !heading && !intro) return null
  return (
    <div className="section-head">
      <div data-reveal>
        {eyebrow && <span className="eyebrow">{eyebrow}</span>}
        {heading && (
          <h2 className="h2">
            <Hl text={heading} />
          </h2>
        )}
      </div>
      <div data-reveal style={{ ['--d' as string]: '120ms' }}>
        {intro && <p className="lead">{intro}</p>}
        {children}
      </div>
    </div>
  )
}
