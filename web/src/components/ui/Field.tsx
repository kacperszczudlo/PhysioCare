import { useId, useState, type InputHTMLAttributes } from 'react'

import './Field.css'

interface FieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  error?: string
  hint?: string
  revealable?: boolean
}

function EyeIcon({ open }: { open: boolean }) {
  if (open) {
    return (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path
          d="M3 3l18 18M10.6 10.6a2 2 0 002.8 2.8M9.9 5.1A10.4 10.4 0 0112 5c5 0 9.3 3.1 11 7.5a11.6 11.6 0 01-4 5.1M6.1 6.1A11.6 11.6 0 001 12.5C2.7 16.9 7 20 12 20c1.6 0 3.1-.3 4.5-.9"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    )
  }

  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M2 12.5C3.7 8.1 8 5 12 5s8.3 3.1 10 7.5c-1.7 4.4-6 7.5-10 7.5S3.7 16.9 2 12.5z"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinejoin="round"
      />
      <circle cx="12" cy="12.5" r="2.5" stroke="currentColor" strokeWidth="1.75" />
    </svg>
  )
}

export function Field({
  id,
  label,
  error,
  hint,
  className = '',
  type = 'text',
  revealable,
  ...rest
}: FieldProps) {
  const generatedId = useId()
  const fieldId = id ?? rest.name ?? generatedId
  const errorId = error && fieldId ? `${fieldId}-error` : undefined
  const hintId = hint && fieldId ? `${fieldId}-hint` : undefined
  const { 'aria-describedby': extraDescribedBy, ...inputProps } = rest
  const describedBy = [errorId, hintId, extraDescribedBy].filter(Boolean).join(' ') || undefined

  const [revealed, setRevealed] = useState(false)
  const canReveal = type === 'password' && (revealable ?? true)
  const inputType = canReveal && revealed ? 'text' : type

  return (
    <div className={`ui-field ${className}`.trim()}>
      <label className="ui-field__label" htmlFor={fieldId}>
        {label}
      </label>
      <div
        className={canReveal ? 'ui-field__control ui-field__control--reveal' : 'ui-field__control'}
      >
        <input
          id={fieldId}
          type={inputType}
          className={error ? 'ui-field__input ui-field__input--error' : 'ui-field__input'}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
          {...inputProps}
        />
        {canReveal ? (
          <button
            type="button"
            className="ui-field__reveal"
            onClick={() => setRevealed((prev) => !prev)}
            aria-label={revealed ? 'Ukryj hasło' : 'Pokaż hasło'}
            aria-pressed={revealed}
          >
            <EyeIcon open={revealed} />
          </button>
        ) : null}
      </div>
      {hint ? (
        <span id={hintId} className="ui-field__hint">
          {hint}
        </span>
      ) : null}
      {error ? (
        <span id={errorId} className="ui-field__error" role="alert">
          {error}
        </span>
      ) : null}
    </div>
  )
}
