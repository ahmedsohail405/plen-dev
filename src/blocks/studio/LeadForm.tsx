'use client'
import React, { useEffect, useState } from 'react'

type Props = {
  formType: 'website_audit' | 'contact' | 'quote'
  submitLabel: string
  successMessage: string
  packages?: string[]
}

const INDUSTRIES = ['Dental / medical', 'Home healthcare', 'Real estate', 'Legal', 'Restaurant / hospitality', 'Retail / ecommerce', 'Tech / SaaS', 'Contractor / home services', 'Other']

export const LeadFormClient: React.FC<Props> = ({ formType, submitLabel, successMessage, packages = [] }) => {
  const [state, setState] = useState<'idle' | 'sending' | 'done'>('idle')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [preset, setPreset] = useState('')

  useEffect(() => {
    const q = new URLSearchParams(window.location.search)
    setPreset(q.get('package') || '')
  }, [])

  const onSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setState('sending')
    setErrors({})
    const fd = new FormData(e.currentTarget)
    const q = new URLSearchParams(window.location.search)
    const body: Record<string, unknown> = Object.fromEntries(fd.entries())
    body.type = formType
    body.consent_marketing = fd.get('consent_marketing') === 'on'
    body.source_page = window.location.pathname
    body.referrer = document.referrer
    body.utm = { source: q.get('utm_source') || '', medium: q.get('utm_medium') || '', campaign: q.get('utm_campaign') || '' }
    try {
      const res = await fetch('/forms/lead', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) })
      const json = await res.json()
      if (json.ok) {
        setState('done')
        // Hook for GA4 / GTM / Meta snippets added in Site Settings.
        const w = window as unknown as { dataLayer?: unknown[] }
        w.dataLayer?.push({ event: 'generate_lead', lead_type: formType })
        return
      }
      setErrors(json.errors || { form: json.error || 'Something went wrong. Please try again.' })
    } catch {
      setErrors({ form: 'Network error. Please try again.' })
    }
    setState('idle')
  }

  if (state === 'done')
    return (
      <div className="form-card form-done" role="status">
        <div className="tick">✓</div>
        <h3 className="h3">{formType === 'website_audit' ? 'Audit requested' : 'Message received'}</h3>
        <p style={{ color: 'var(--muted)', marginTop: 10 }}>{successMessage}</p>
      </div>
    )

  const Err = ({ k }: { k: string }) => (errors[k] ? <div className="err">{errors[k]}</div> : null)

  return (
    <form className="form-card" onSubmit={onSubmit} noValidate>
      <div className="form-grid">
        <div className="field">
          <label htmlFor={`${formType}-name`}>Your name *</label>
          <input id={`${formType}-name`} name="name" autoComplete="name" required />
          <Err k="name" />
        </div>
        <div className="field">
          <label htmlFor={`${formType}-email`}>Email *</label>
          <input id={`${formType}-email`} name="email" type="email" autoComplete="email" required />
          <Err k="email" />
        </div>
        {formType === 'website_audit' ? (
          <div className="field full">
            <label htmlFor="audit-url">Website address *</label>
            <input id="audit-url" name="website_url" inputMode="url" placeholder="yourbusiness.com" required />
            <Err k="website_url" />
          </div>
        ) : (
          <div className="field">
            <label htmlFor={`${formType}-company`}>Company</label>
            <input id={`${formType}-company`} name="company" autoComplete="organization" />
          </div>
        )}
        <div className="field">
          <label htmlFor={`${formType}-phone`}>Phone</label>
          <input id={`${formType}-phone`} name="phone" type="tel" autoComplete="tel" />
        </div>
        <div className="field">
          <label htmlFor={`${formType}-industry`}>Business type</label>
          <select id={`${formType}-industry`} name="industry" defaultValue="">
            <option value="" disabled>
              Choose…
            </option>
            {INDUSTRIES.map((i) => (
              <option key={i}>{i}</option>
            ))}
          </select>
        </div>
        {formType !== 'website_audit' && (
          <>
            <div className="field">
              <label htmlFor={`${formType}-site`}>Current website (if any)</label>
              <input id={`${formType}-site`} name="website_url" inputMode="url" placeholder="yourbusiness.com" />
            </div>
            {packages.length > 0 && (
              <div className="field">
                <label htmlFor={`${formType}-pkg`}>Package</label>
                <select id={`${formType}-pkg`} name="package" key={preset} defaultValue={preset}>
                  <option value="">Not sure yet</option>
                  {packages.map((p) => (
                    <option key={p}>{p}</option>
                  ))}
                </select>
              </div>
            )}
            <div className="field full">
              <label htmlFor={`${formType}-msg`}>Tell us about the project</label>
              <textarea id={`${formType}-msg`} name="message" />
            </div>
          </>
        )}
        <div className="hp" aria-hidden>
          <label>
            Leave empty <input name="company_site" tabIndex={-1} autoComplete="off" />
          </label>
        </div>
        <div className="full">
          <label className="check">
            <input type="checkbox" name="consent_marketing" required={formType === 'website_audit'} />
            <span>
              {formType === 'website_audit'
                ? 'Email me the audit report. Plen Dev may follow up about it. *'
                : 'Plen Dev can email me about my project.'}
            </span>
          </label>
          <Err k="consent_marketing" />
        </div>
      </div>
      {errors.form && <p className="err" style={{ color: '#c2361b' }}>{errors.form}</p>}
      <button className="btn" type="submit" disabled={state === 'sending'}>
        {state === 'sending' ? 'Sending…' : submitLabel}
      </button>
    </form>
  )
}
