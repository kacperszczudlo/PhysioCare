import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'

import { authApi, type MFAStatusResponse } from '@/api/auth'
import { getErrorMessage } from '@/api/client'
import { useAuth } from '@/auth/AuthContext'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import { useToast } from '@/components/ui/ToastContext'
import {
  IconKey,
  IconSettings,
  IconShield,
} from '@/pages/admin/AdminIcons'
import './AdminProfilePage.css'
/**
 * Widok profilu osobistego administratora.
 * Umożliwia edycję danych osobowych (imię, nazwisko) oraz podgląd stanu zabezpieczeń 2FA.
 */
export function AdminProfilePage() {
  const { user, refreshSession } = useAuth()
  const { toast } = useToast()

  const [firstName, setFirstName] = useState(user?.first_name ?? '')
  const [lastName, setLastName] = useState(user?.last_name ?? '')
  const [busy, setBusy] = useState(false)
  const [mfaStatus, setMfaStatus] = useState<MFAStatusResponse | null>(null)
  const [loadingMfa, setLoadingMfa] = useState(true)

  useEffect(() => {
    if (user) {
      setFirstName(user.first_name ?? '')
      setLastName(user.last_name ?? '')
    }
  }, [user?.id])

  useEffect(() => {
    let cancelled = false
    async function loadMfa() {
      try {
        const data = await authApi.getMFAStatus()
        if (!cancelled) {
          setMfaStatus(data)
        }
      } catch (err) {
        console.error('Nie udało się pobrać statusu 2FA', err)
      } finally {
        if (!cancelled) {
          setLoadingMfa(false)
        }
      }
    }
    void loadMfa()
    return () => {
      cancelled = true
    }
  }, [])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    try {
      await authApi.updateMe({
        first_name: firstName.trim(),
        last_name: lastName.trim(),
      })
      await refreshSession()
      toast.success('Dane administratora zostały zaktualizowane.', {
        title: 'Profil zapisany',
      })
    } catch (err) {
      const errMsg = getErrorMessage(err, 'Nie udało się zaktualizować profilu.')
      toast.error(errMsg, { title: 'Błąd zapisu' })
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="admin-profile-page">
      <PageHeader
        title="Mój profil"
        description="Tożsamość administratora, dane personalne i uprawnienia systemowe."
      />

      <div className="admin-profile-grid">
        <main className="admin-profile-main">
          <section className="admin-profile-card" aria-labelledby="admin-personal-heading">
            <header className="admin-profile-card__head">
              <h2 id="admin-personal-heading">Dane personalne</h2>
              <p className="admin-profile-card__desc">
                Informacje wyświetlane w nagłówku sesji oraz w audycie działań administratora.
              </p>
            </header>

            <form className="admin-profile-form" onSubmit={(e) => void handleSubmit(e)}>
              <div className="admin-profile-form__grid">
                <Field
                  label="Imię"
                  name="first_name"
                  type="text"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  placeholder="Imię administratora"
                  required
                />
                <Field
                  label="Nazwisko"
                  name="last_name"
                  type="text"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  placeholder="Nazwisko administratora"
                  required
                />
              </div>

              <div className="admin-profile-form__readonly">
                <span className="admin-profile-form__label">Adres e-mail konta</span>
                <div className="admin-profile-form__static" title="Główny identyfikator logowania">
                  {user?.email ?? '—'}
                </div>
              </div>

              <div className="admin-profile-form__readonly">
                <span className="admin-profile-form__label">Rola w systemie</span>
                <div className="admin-profile-form__static">
                  <span className="admin-badge--role">Administrator systemu (ADMIN)</span>
                </div>
              </div>

              <div className="admin-profile-actions">
                <Button type="submit" loading={busy}>
                  Zapisz zmiany
                </Button>
              </div>
            </form>
          </section>
        </main>

        <aside className="admin-profile-aside">
          <section className="admin-profile-card" aria-labelledby="admin-security-heading">
            <header className="admin-profile-card__head">
              <h2 id="admin-security-heading">Bezpieczeństwo i 2FA</h2>
              <p className="admin-profile-card__desc">
                Ochrona konta z najwyższymi uprawnieniami w systemie PhysioCare.
              </p>
            </header>

            <div className="admin-profile-security">
              <div>
                <span className="admin-profile-form__label" style={{ display: 'block', marginBottom: '0.5rem' }}>
                  Stan dwuskładnikowej weryfikacji (2FA)
                </span>
                {loadingMfa ? (
                  <span className="admin-profile-status-badge">Sprawdzanie…</span>
                ) : mfaStatus?.is_enabled ? (
                  <span className="admin-profile-status-badge admin-profile-status-badge--active">
                    <IconShield className="admin-profile-status-badge__icon" />
                    <span>2FA Aktywne (TOTP)</span>
                  </span>
                ) : (
                  <span className="admin-profile-status-badge admin-profile-status-badge--warn">
                    <IconShield className="admin-profile-status-badge__icon" />
                    <span>2FA Wyłączone (Zalecane)</span>
                  </span>
                )}
              </div>

              <Link
                to="/admin/settings"
                className="admin-profile-security__btn"
                title="Przejdź do ustawień zabezpieczeń"
              >
                <IconSettings style={{ width: '1.1rem', height: '1.1rem' }} />
                <span>Zarządzaj 2FA i hasłem</span>
              </Link>
            </div>
          </section>

          <section className="admin-profile-card" aria-labelledby="admin-scope-heading">
            <header className="admin-profile-card__head">
              <h2 id="admin-scope-heading">Zakres uprawnień</h2>
              <p className="admin-profile-card__desc">
                Uprawnienia nadane Twojej tożsamości administracyjnej.
              </p>
            </header>

            <ul className="admin-profile-scope-list">
              <li className="admin-profile-scope-item">
                <IconShield className="admin-profile-scope-item__icon" />
                <span>Zarządzanie kontami użytkowników (personel medyczny, pacjenci).</span>
              </li>
              <li className="admin-profile-scope-item">
                <IconKey className="admin-profile-scope-item__icon" />
                <span>Inicjowanie bezpiecznego resetowania haseł oraz blokowanie dostępów.</span>
              </li>
              <li className="admin-profile-scope-item">
                <IconShield className="admin-profile-scope-item__icon" />
                <span>Wgląd w grafiki pracy i harmonogramy wizyt fizjoterapeutów.</span>
              </li>
              <li className="admin-profile-scope-item">
                <IconShield className="admin-profile-scope-item__icon" />
                <span>Moderacja opinii pacjentów oraz ochrona reputacji placówki.</span>
              </li>
            </ul>
          </section>
        </aside>
      </div>
    </div>
  )
}
