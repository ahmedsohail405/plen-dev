import React from 'react'

/** Renders "Websites that *win* customers" with the *word* in the serif highlight style. */
export const Hl: React.FC<{ text?: string | null }> = ({ text }) => {
  if (!text) return null
  const parts = text.split(/(\*[^*]+\*)/g)
  return (
    <>
      {parts.map((p, i) =>
        p.startsWith('*') && p.endsWith('*') && p.length > 2 ? (
          <span className="hl" key={i}>
            {p.slice(1, -1)}
          </span>
        ) : (
          <React.Fragment key={i}>{p}</React.Fragment>
        ),
      )}
    </>
  )
}

export const plain = (text?: string | null) => (text || '').replace(/\*/g, '')
