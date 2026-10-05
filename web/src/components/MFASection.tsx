import { useEffect, useState, type FormEvent } from 'react'

import { authApi, type MFAStatusResponse, type MFASetupResponse } from '@/api/auth'
import { getErrorMessage } from '@/api/client'
import { ErrorBanner } from '@/components/AsyncState'
import { MFASectionSkeleton } from '@/components/skeletons/WebSkeletons'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import { useToast } from '@/components/ui/ToastContext'

function qrSvgDataUri(svg: string): string {
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`
}

/**
 * Komponent sekcji ustawień dwuskładnikowej weryfikacji tożsamości (MFA / TOTP) z obsługą kodów zapasowych.
 */
export function MFASection() {
  const [status, setStatus] = useState<MFAStatusResponse | null>(null)
  const [loadingStatus, setLoadingStatus] = useState(true)
  const [setupData, setSetupData] = useState<MFASetupResponse | null>(null)
  const [enableCode, setEnableCode] = useState('')
  const [disablePassword, setDisablePassword] = useState('')
  const [backupCodes, setBackupCodes] = useState<string[] | null>(null)
  const [showDisableForm, setShowDisableForm] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function loadStatus() {
      try {
        const res = await authApi.getMFAStatus()
        setStatus(res)
      } catch (err) {
        console.error('Failed to load 2FA status', err)
      } finally {
        setLoadingStatus(false)
      }
    }
    void loadStatus()
  }, [])

  const { toast } = useToast()

  async function handleStartSetup() {
    setError(null)
    setBusy(true)
    try {
      const data = await authApi.setupMFA()
      setSetupData(data)
    } catch (err) {
      const errMsg = getErrorMessage(err, 'Nie udało się rozpocząć konfiguracji 2FA.')
      setError(errMsg)
      toast.error(errMsg)
    } finally {
      setBusy(false)
    }
  }

  async function handleEnable(e: FormEvent) {
    e.preventDefault()
    if (!enableCode.trim()) return
    setError(null)
    setBusy(true)
    try {
      const res = await authApi.enableMFA(enableCode.trim())
      setBackupCodes(res.backup_codes)
      toast.success(res.message, { title: 'Dwuetapowa weryfikacja (2FA)' })
      setSetupData(null)
      setEnableCode('')
      setStatus((prev) => (prev ? { ...prev, is_enabled: true } : null))
    } catch (err) {
      const errMsg = getErrorMessage(err, 'Nieprawidłowy kod 2FA.')
      setError(errMsg)
      toast.error(errMsg)
    } finally {
      setBusy(false)
    }
  }

  async function handleDisable(e: FormEvent) {
    e.preventDefault()
    if (!disablePassword.trim()) return
    setError(null)
    setBusy(true)
    try {
      const res = await authApi.disableMFA(disablePassword.trim())
      toast.info(res.message, { title: 'Dwuetapowa weryfikacja (2FA)' })
      setShowDisableForm(false)
      setDisablePassword('')
      setStatus((prev) => (prev ? { ...prev, is_enabled: false } : null))
    } catch (err) {
      const errMsg = getErrorMessage(err, 'Nie udało się wyłączyć 2FA. Sprawdź hasło.')
      setError(errMsg)
      toast.error(errMsg)
    } finally {
      setBusy(false)
    }
  }

  if (loadingStatus) {
    return (
      <section className="settings-card">
        <MFASectionSkeleton />
      </section>
    )
  }

  return (
    <section className="settings-card" aria-labelledby="mfa-heading">
      <header className="settings-card__head">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 id="mfa-heading">Dwuskładnikowa autentykacja (2FA)</h2>
          <span
            className={`mfa-badge ${status?.is_enabled ? 'mfa-badge--active' : 'mfa-badge--inactive'}`}
          >
            {status?.is_enabled ? '✓ Aktywna' : 'Wyłączona'}
          </span>
        </div>
        <p className="settings-muted">
          Dodatkowa ochrona konta kodem z aplikacji weryfikującej (Google Authenticator, Microsoft
          Authenticator, 1Password).
          {status?.mfa_required_for_role && !status?.is_enabled
            ? ' (Zalecane dla kont z dostępem do dokumentacji medycznej pacjentów).'
            : ''}
        </p>
      </header>

      {error ? <ErrorBanner message={error} /> : null}

      {/* Backup codes modal/view after enabling 2FA */}
      {backupCodes ? (
        <div className="mfa-backup-codes">
          <h3>Zapisz kody zapasowe!</h3>
          <p className="settings-muted">
            Kody zapasowe pozwolą Ci zalogować się do systemu w przypadku utraty dostępu do telefonu
            lub aplikacji. Każdy z kodów jest jednorazowy.
          </p>
          <div className="mfa-codes-grid">
            {backupCodes.map((code, i) => (
              <code key={i} className="mfa-code-item">
                {code}
              </code>
            ))}
          </div>
          <Button type="button" onClick={() => setBackupCodes(null)}>
            Zapisano kody / Zamknij
          </Button>
        </div>
      ) : null}

      {/* 2FA Disabled view */}
      {!status?.is_enabled && !setupData && !backupCodes ? (
        <div className="mfa-actions">
          <Button type="button" loading={busy} onClick={() => void handleStartSetup()}>
            Włącz 2FA (Google Authenticator)
          </Button>
        </div>
      ) : null}

      {/* Setup Step View */}
      {setupData ? (
        <form className="mfa-setup-box" onSubmit={(e) => void handleEnable(e)}>
          <h3>Konfiguracja Google Authenticator</h3>
          <ol className="mfa-setup-steps">
            <li>
              Pobierz aplikację <strong>Google Authenticator</strong> lub{' '}
              <strong>Microsoft Authenticator</strong> na telefon.
            </li>
            <li>Zeskanuj poniższy kod QR w aplikacji lub wpisz klucz konfiguracji ręcznie:</li>
          </ol>

          <div className="mfa-qr-container">
            <img
              className="mfa-qr-svg"
              src={qrSvgDataUri(setupData.qr_code_svg)}
              alt="Kod QR do konfiguracji aplikacji uwierzytelniającej"
            />
            <div className="mfa-secret-box">
              <span className="mfa-secret-label">Klucz konfiguracji Base32:</span>
              <code className="mfa-secret-value">{setupData.secret_key}</code>
            </div>
          </div>

          <Field
            label="Wpisz 6-cyfrowy kod z aplikacji, aby zatwierdzić:"
            name="enableCode"
            type="text"
            placeholder="123456"
            autoComplete="one-time-code"
            required
            value={enableCode}
            onChange={(e) => setEnableCode(e.target.value)}
          />

          <div className="settings-actions" style={{ marginTop: '1rem' }}>
            <Button type="submit" loading={busy}>
              Potwierdź i aktywuj 2FA
            </Button>
            <Button type="button" variant="secondary" onClick={() => setSetupData(null)}>
              Anuluj
            </Button>
          </div>
        </form>
      ) : null}

      {/* 2FA Enabled view */}
      {status?.is_enabled && !backupCodes ? (
        <div className="mfa-enabled-box">
          {!showDisableForm ? (
            <div className="settings-actions">
              <p className="settings-muted" style={{ width: '100%' }}>
                Twoje konto jest w pełni zabezpieczone dwuskładnikową autentykacją TOTP.
              </p>
              <Button type="button" variant="secondary" onClick={() => setShowDisableForm(true)}>
                Wyłącz 2FA
              </Button>
            </div>
          ) : (
            <form onSubmit={(e) => void handleDisable(e)} className="mfa-disable-form">
              <h3>Wyłączanie autentykacji 2FA</h3>
              <p className="settings-muted">Podaj hasło do swojego konta, aby wyłączyć 2FA:</p>
              <Field
                label="Hasło konta"
                name="disablePassword"
                type="password"
                required
                value={disablePassword}
                onChange={(e) => setDisablePassword(e.target.value)}
              />
              <div className="settings-actions" style={{ marginTop: '0.75rem' }}>
                <Button type="submit" loading={busy}>
                  Potwierdź wyłączenie 2FA
                </Button>
                <Button type="button" variant="secondary" onClick={() => setShowDisableForm(false)}>
                  Anuluj
                </Button>
              </div>
            </form>
          )}
        </div>
      ) : null}
    </section>
  )
}
