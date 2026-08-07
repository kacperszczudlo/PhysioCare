import type { PasswordRequirement } from '@/lib/passwordPolicy'

import './PasswordRequirements.css'

interface PasswordRequirementsProps {
  requirements: PasswordRequirement[]
  showErrors?: boolean
}

export function PasswordRequirements({
  requirements,
  showErrors = false,
}: PasswordRequirementsProps) {
  return (
    <ul className="password-reqs" aria-label="Wymagania hasła">
      {requirements.map((req) => {
        const state = req.met ? 'met' : showErrors ? 'fail' : 'pending'
        return (
          <li
            key={req.id}
            className={`password-reqs__item password-reqs__item--${state}`}
          >
            <span className="password-reqs__mark" aria-hidden="true">
              {req.met ? '✓' : '○'}
            </span>
            <span>
              {req.label}
              <span className="sr-only">
                {req.met ? ' — spełnione' : ' — niespełnione'}
              </span>
            </span>
          </li>
        )
      })}
    </ul>
  )
}
