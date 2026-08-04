import type { InputHTMLAttributes } from 'react'

import './Field.css'

interface FieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  error?: string
  hint?: string
}

export function Field({ id, label, error, hint, className = '', ...rest }: FieldProps) {
  const fieldId = id ?? rest.name
  const errorId = error && fieldId ? `${fieldId}-error` : undefined
  const hintId = hint && fieldId ? `${fieldId}-hint` : undefined

  return (
    <label className={`ui-field ${className}`.trim()} htmlFor={fieldId}>
      <span className="ui-field__label">{label}</span>
      <input
        id={fieldId}
        className={error ? 'ui-field__input ui-field__input--error' : 'ui-field__input'}
        aria-invalid={error ? true : undefined}
        aria-describedby={[errorId, hintId].filter(Boolean).join(' ') || undefined}
        {...rest}
      />
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
    </label>
  )
}
