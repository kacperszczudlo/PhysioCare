import { useEffect, useState, type FormEvent } from 'react'

import { authApi, type MFASetupResponse } from '@/api/auth'
import { getErrorMessage } from '@/api/client'
import { useAuth } from '@/auth/AuthContext'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import { useOptionalToast } from '@/components/ui/ToastContext'
import './MFAEnforcementModal.css'

function qrSvgDataUri(svg: string): string {
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`
}

/**
 * Modal wymuszający konfigurację 2FA dla personelu (terapeuci, administratorzy).
 *
 * Zgodnie ze standardami bezpieczeństwa medycznego RODO oraz ochroną danych pacjentów,
 * użytkownicy z rolami medycznymi/administracyjnymi nie mogą korzystać z systemu
 * bez aktywnej weryfikacji dwuskładnikowej TOTP. Modal jest nieodrzucalny do momentu
 * pomyślnej aktywacji 2FA lub wylogowania się z sesji.
 */
export function MFAEnforcementModal() {
  const { user, updateUser, logout } = useAuth()
  const toastCtx = useOptionalToast()
  const toast = toastCtx?.toast

  const [setupData, setSetupData] = useState<MFASetupResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [code, setCode] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [backupCodes, setBackupCodes] = useState<string[] | null>(null)
  const [copiedKey, setCopiedKey] = useState(false)
  const [copiedCodes, setCopiedCodes] = useState(false)

  const isRequired = Boolean(user?.mfa_required) && !user?.has_mfa

  useEffect(() => {
    if (!isRequired) {
      return
    }

    let active = true
    async function initSetup() {
      setLoading(true)
      setError(null)
      try {
        const data = await authApi.setupMFA()
        if (active) {
          setSetupData(data)
        }
      } catch (err) {
        if (active) {
          const msg = getErrorMessage(err, 'Nie udało się zainicjalizować konfiguracji 2FA.')
          setError(msg)
        }
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    void initSetup()
    return () => {
      active = false
    }
  }, [isRequired])

  if (!isRequired) {
    return null
  }

  async function handleCopyKey() {
    if (!setupData?.secret_key) return
    try {
      await navigator.clipboard.writeText(setupData.secret_key)
      setCopiedKey(true)
      setTimeout(() => setCopiedKey(false), 2000)
    } catch {
      toast?.info(`Klucz: ${setupData.secret_key}`)
    }
  }

  async function handleCopyCodes() {
    if (!backupCodes) return
    try {
      await navigator.clipboard.writeText(backupCodes.join('\n'))
      setCopiedCodes(true)
      setTimeout(() => setCopiedCodes(false), 2000)
      toast?.success('Kody zapasowe zostały skopiowane do schowka.')
    } catch {
      toast?.info('Nie udało się skopiować automatycznie. Zapisz kody ręcznie.')
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const trimmed = code.trim()
    if (!trimmed) return

    setBusy(true)
    setError(null)
    try {
      const res = await authApi.enableMFA(trimmed)
      setBackupCodes(res.backup_codes)
      toast?.success('2FA zostało pomyślnie aktywowane!')
    } catch (err) {
      const msg = getErrorMessage(err, 'Nieprawidłowy 6-cyfrowy kod TOTP.')
      setError(msg)
      toast?.error(msg)
    } finally {
      setBusy(false)
    }
  }

  function handleComplete() {
    updateUser({ has_mfa: true })
  }

  return (
    <div
      className="mfa-enforce-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="mfa-enforce-title"
    >
      <div className="mfa-enforce-card">
        {backupCodes ? (
          <div className="mfa-enforce-step">
            <div className="mfa-enforce-badge mfa-enforce-badge--success">
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <polyline points="20 6 9 17 4 12" />
              </svg>
              <span>Aktywacja ukończona</span>
            </div>

            <h2 id="mfa-enforce-title" className="mfa-enforce-title">
              Kody zapasowe
            </h2>

            <p className="mfa-enforce-desc">
              Poniżej znajduje się lista jednorazowych kodów ratunkowych. Jeśli utracisz dostęp do
              aplikacji TOTP w telefonie, każdy z tych kodów umożliwi jednorazowe zalogowanie.
              Zapisz je w bezpiecznym miejscu (np. w menedżerze haseł).
            </p>

            <div className="mfa-enforce-codes-grid">
              {backupCodes.map((c, i) => (
                <code key={i} className="mfa-enforce-code-item">
                  {c}
                </code>
              ))}
            </div>

            <div className="mfa-enforce-actions">
              <Button type="button" variant="secondary" onClick={handleCopyCodes}>
                {copiedCodes ? '✓ Skopiowano' : 'Kopiuj kody'}
              </Button>
              <Button type="button" variant="primary" onClick={handleComplete}>
                Przejdź do systemu
              </Button>
            </div>
          </div>
        ) : (
          <div className="mfa-enforce-step">
            <div className="mfa-enforce-badge">
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              </svg>
              <span>Wymagane zabezpieczenie konta</span>
            </div>

            <h2 id="mfa-enforce-title" className="mfa-enforce-title">
              Skonfiguruj uwierzytelnianie dwuskładnikowe (2FA)
            </h2>

            <p className="mfa-enforce-desc">
              Dostęp do kartotek medycznych i harmonogramu w PhysioCare wymaga aktywnego
              uwierzytelniania dwuetapowego. Zabezpiecza to wrażliwe dane pacjentów i Twoje konto.
            </p>

            {loading ? (
              <div className="mfa-enforce-loading">
                <div className="mfa-enforce-spinner" aria-hidden="true" />
                <p>Przygotowywanie klucza 2FA...</p>
              </div>
            ) : error && !setupData ? (
              <div className="mfa-enforce-error-box">
                <p className="mfa-enforce-error-text">{error}</p>
                <Button type="button" variant="secondary" onClick={() => window.location.reload()}>
                  Odśwież stronę
                </Button>
              </div>
            ) : setupData ? (
              <>
                <div className="mfa-enforce-qr-section">
                  <div className="mfa-enforce-qr-frame">
                    <img
                      src={qrSvgDataUri(setupData.qr_code_svg)}
                      alt="Kod QR do konfiguracji aplikacji 2FA"
                      className="mfa-enforce-qr-img"
                    />
                  </div>
                  <div className="mfa-enforce-qr-info">
                    <ol className="mfa-enforce-instructions">
                      <li>
                        Otwórz aplikację uwierzytelniającą (np. Google Authenticator, Microsoft
                        Authenticator, 1Password).
                      </li>
                      <li>Zeskanuj powyższy kod QR aparatem w telefonie.</li>
                      <li>
                        Jeśli nie możesz zeskanować kodu, wprowadź poniższy klucz ręcznie:
                        <div className="mfa-enforce-secret-row">
                          <code className="mfa-enforce-secret">{setupData.secret_key}</code>
                          <button
                            type="button"
                            className="mfa-enforce-copy-btn"
                            onClick={handleCopyKey}
                            aria-label="Kopiuj klucz sekretny"
                          >
                            {copiedKey ? '✓ Skopiowano' : 'Kopiuj'}
                          </button>
                        </div>
                      </li>
                    </ol>
                  </div>
                </div>

                <form onSubmit={handleSubmit} className="mfa-enforce-form">
                  <Field
                    label="Wpisz 6-cyfrowy kod z aplikacji"
                    name="totp-code"
                    id="totp-code"
                    required
                    error={error ?? undefined}
                    hint="Wprowadź aktualny 6-cyfrowy kod z aplikacji w telefonie."
                    type="text"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    maxLength={6}
                    value={code}
                    onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                    placeholder="123456"
                    autoFocus
                    autoComplete="one-time-code"
                    className="mfa-enforce-code-input"
                  />

                  <div className="mfa-enforce-actions">
                    <Button type="button" variant="ghost" onClick={() => void logout()}>
                      Wyloguj się
                    </Button>
                    <Button
                      type="submit"
                      variant="primary"
                      loading={busy}
                      disabled={code.trim().length !== 6 || busy}
                    >
                      Aktywuj i przejdź dalej
                    </Button>
                  </div>
                </form>
              </>
            ) : null}
          </div>
        )}
      </div>
    </div>
  )
}
