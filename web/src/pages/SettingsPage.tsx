import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'

import { authApi } from '@/api/auth'
import { getErrorMessage } from '@/api/client'
import { useAuth } from '@/auth/AuthContext'
import { ErrorBanner, SuccessBanner } from '@/components/AsyncState'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import { PasswordRequirements } from '@/components/ui/PasswordRequirements'
import { AuthMediaImg } from '@/components/AuthMedia'
import {
  getPasswordError,
  getPasswordRequirements,
  PASSWORD_MESSAGES,
  passwordsMatch,
} from '@/lib/passwordPolicy'
import './SettingsPage.css'

function initials(first?: string, last?: string): string {
  const value = `${first?.charAt(0) ?? ''}${last?.charAt(0) ?? ''}`.toUpperCase()
  return value || '?'
}

export function SettingsPage() {
  const { user, logout } = useAuth()

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordBusy, setPasswordBusy] = useState(false)
  const [passwordError, setPasswordError] = useState<string | null>(null)
  const [passwordMessage, setPasswordMessage] = useState<string | null>(null)
  const [passwordTouched, setPasswordTouched] = useState(false)

  const passwordRequirements = getPasswordRequirements(newPassword)
  const displayName =
    [user?.first_name, user?.last_name].filter(Boolean).join(' ') || user?.email || 'Konto'

  async function onChangePassword(event: FormEvent) {
    event.preventDefault()
    setPasswordError(null)
    setPasswordMessage(null)

    if (!currentPassword.trim()) {
      setPasswordError('Podaj obecne hasło.')
      return
    }
    const newPasswordError = getPasswordError(newPassword)
    if (newPasswordError) {
      setPasswordError(newPasswordError)
      return
    }
    if (!passwordsMatch(newPassword, confirmPassword)) {
      setPasswordError(PASSWORD_MESSAGES.mismatch)
      return
    }

    setPasswordBusy(true)
    try {
      const { detail } = await authApi.changePassword(currentPassword, newPassword)
      setPasswordMessage(detail)
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      setPasswordTouched(false)
      await logout()
    } catch (err) {
      setPasswordError(getErrorMessage(err, 'Nie udało się zmienić hasła.'))
    } finally {
      setPasswordBusy(false)
    }
  }

  return (
    <section className="settings-page">
      <PageHeader
        title="Ustawienia"
        description="Bezpieczeństwo konta, dokumenty i sesja panelu."
      />

      <div className="settings-grid">
        <div className="settings-main">
          <section
            className="settings-card settings-card--account"
            aria-labelledby="account-heading"
          >
            <header className="settings-card__head">
              <h2 id="account-heading">Konto</h2>
              <p className="settings-muted">Aktywna sesja w panelu fizjoterapeuty.</p>
            </header>

            <div className="settings-identity">
              {user?.avatar_url ? (
                <AuthMediaImg path={user.avatar_url} className="settings-identity__avatar" />
              ) : (
                <span
                  className="settings-identity__avatar settings-identity__avatar--fallback"
                  aria-hidden="true"
                >
                  {initials(user?.first_name, user?.last_name)}
                </span>
              )}
              <div className="settings-identity__text">
                <p className="settings-identity__name">{displayName}</p>
                {user?.email ? <p className="settings-identity__email">{user.email}</p> : null}
                <Link to="/profile" className="settings-identity__link">
                  Edytuj profil
                </Link>
              </div>
            </div>
          </section>

          <form
            className="settings-card"
            aria-labelledby="security-heading"
            onSubmit={(e) => void onChangePassword(e)}
          >
            <header className="settings-card__head">
              <h2 id="security-heading">Bezpieczeństwo</h2>
              <p className="settings-muted">
                Znasz obecne hasło - zmień je poniżej. Nie pamiętasz - wyślemy link na e-mail.
              </p>
            </header>

            <div className="settings-fields">
              <Field
                label="Obecne hasło"
                name="current_password"
                type="password"
                autoComplete="current-password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
              />
              <div className="settings-fields__pair">
                <Field
                  label="Nowe hasło"
                  name="new_password"
                  type="password"
                  autoComplete="new-password"
                  value={newPassword}
                  onChange={(e) => {
                    setNewPassword(e.target.value)
                    setPasswordTouched(true)
                  }}
                  onBlur={() => setPasswordTouched(true)}
                  required
                />
                <Field
                  label="Powtórz nowe hasło"
                  name="confirm_password"
                  type="password"
                  autoComplete="new-password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />
              </div>
              <PasswordRequirements
                requirements={passwordRequirements}
                showErrors={passwordTouched}
              />
            </div>

            <div className="settings-actions">
              <Button type="submit" loading={passwordBusy}>
                Zmień hasło
              </Button>
              <Link to="/password-reset" className="settings-identity__link">
                Nie pamiętam hasła
              </Link>
              {passwordError ? <ErrorBanner message={passwordError} /> : null}
              {passwordMessage ? <SuccessBanner message={passwordMessage} /> : null}
            </div>
          </form>
        </div>

        <aside className="settings-aside">
          <section className="settings-card" aria-labelledby="legal-heading">
            <header className="settings-card__head">
              <h2 id="legal-heading">Prywatność</h2>
              <p className="settings-muted">Dokumenty i wnioski związane z kontem.</p>
            </header>

            <nav className="settings-rows" aria-label="Dokumenty prawne">
              <Link to="/privacy" className="settings-row">
                <span className="settings-row__copy">
                  <span className="settings-row__label">Polityka prywatności</span>
                  <span className="settings-row__desc">Jak przetwarzamy dane</span>
                </span>
                <span className="settings-row__chevron" aria-hidden="true" />
              </Link>
              <Link to="/cookies" className="settings-row">
                <span className="settings-row__copy">
                  <span className="settings-row__label">Polityka cookies</span>
                  <span className="settings-row__desc">Pliki cookie w serwisie</span>
                </span>
                <span className="settings-row__chevron" aria-hidden="true" />
              </Link>
              <Link to="/account-deletion" className="settings-row">
                <span className="settings-row__copy">
                  <span className="settings-row__label">Usuwanie konta</span>
                  <span className="settings-row__desc">Wniosek o usunięcie danych</span>
                </span>
                <span className="settings-row__chevron" aria-hidden="true" />
              </Link>
            </nav>
          </section>

          <section
            className="settings-card settings-card--session"
            aria-labelledby="session-heading"
          >
            <header className="settings-card__head">
              <h2 id="session-heading">Sesja</h2>
              <p className="settings-muted">Kończy dostęp na tym urządzeniu.</p>
            </header>
            <Button
              type="button"
              variant="secondary"
              className="settings-logout"
              onClick={() => void logout()}
            >
              Wyloguj
            </Button>
          </section>
        </aside>
      </div>
    </section>
  )
}
