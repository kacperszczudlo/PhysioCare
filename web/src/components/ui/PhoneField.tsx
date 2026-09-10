import { useId } from 'react'

import {
  COUNTRIES,
  DEFAULT_COUNTRY_CODE,
  formatCountryOption,
  getCountryByCode,
} from '@/lib/countries'

import './Field.css'
import './PhoneField.css'

interface PhoneFieldProps {
  label?: string
  countryCode: string
  nationalNumber: string
  onCountryChange: (countryCode: string) => void
  onNationalNumberChange: (nationalNumber: string) => void
  error?: string
  hint?: string
  required?: boolean
  disabled?: boolean
  name?: string
  id?: string
}

export function PhoneField({
  label = 'Telefon',
  countryCode,
  nationalNumber,
  onCountryChange,
  onNationalNumberChange,
  error,
  hint,
  required,
  disabled,
  name = 'phone',
  id,
}: PhoneFieldProps) {
  const generatedId = useId()
  const fieldId = id ?? name ?? generatedId
  const countryId = `${fieldId}-country`
  const numberId = `${fieldId}-number`
  const errorId = error ? `${fieldId}-error` : undefined
  const hintId = hint ? `${fieldId}-hint` : undefined
  const describedBy = [errorId, hintId].filter(Boolean).join(' ') || undefined

  const country = getCountryByCode(countryCode) ?? getCountryByCode(DEFAULT_COUNTRY_CODE)!

  return (
    <div className={`ui-field ui-phone-field ${error ? 'ui-phone-field--error' : ''}`.trim()}>
      <label className="ui-field__label" htmlFor={numberId}>
        {label}
        {required ? ' *' : null}
      </label>

      <div className="ui-phone-field__row">
        <div className="ui-phone-field__country">
          <label className="ui-phone-field__sr" htmlFor={countryId}>
            Kraj
          </label>
          <select
            id={countryId}
            className={error ? 'ui-field__input ui-field__input--error' : 'ui-field__input'}
            value={country.code}
            disabled={disabled}
            onChange={(e) => onCountryChange(e.target.value)}
            aria-invalid={error ? true : undefined}
          >
            {COUNTRIES.map((item) => (
              <option key={item.code} value={item.code}>
                {formatCountryOption(item)}
              </option>
            ))}
          </select>
        </div>

        <div className="ui-phone-field__number">
          <span className="ui-phone-field__prefix" aria-hidden="true">
            +{country.dial}
          </span>
          <input
            id={numberId}
            name={name}
            type="tel"
            inputMode="tel"
            autoComplete="tel-national"
            className={
              error
                ? 'ui-field__input ui-field__input--error ui-phone-field__input'
                : 'ui-field__input ui-phone-field__input'
            }
            value={nationalNumber}
            disabled={disabled}
            required={required}
            aria-invalid={error ? true : undefined}
            aria-describedby={describedBy}
            onChange={(e) => onNationalNumberChange(e.target.value)}
          />
        </div>
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
