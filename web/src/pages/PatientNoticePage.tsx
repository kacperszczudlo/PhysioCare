import { useState } from 'react'
import { Link } from 'react-router-dom'
import { QRCodeSVG } from 'qrcode.react'

import { useAuth } from '@/auth/AuthContext'
import { Button } from '@/components/ui/Button'
import { useToast } from '@/components/ui/ToastContext'
import './PatientNoticePage.css'

/**
 * Dedykowany widok portalu pacjenta w aplikacji webowej PhysioCare.
 * Prezentuje status konta, korzyści aplikacji mobilnej oraz kod QR i bezpośrednie
 * łącze do instalacji pakietu Android APK konfigurowane przez zmienną środowiskową VITE_EXPO_MOBILE_BUILD_URL.
 */
export function PatientNoticePage() {
  const { user, logout } = useAuth()
  const { toast } = useToast()
  const [copied, setCopied] = useState(false)

  const buildUrl =
    (import.meta.env.VITE_EXPO_MOBILE_BUILD_URL as string | undefined)?.trim() || ''

  const handleCopyLink = async () => {
    if (!buildUrl) return

    try {
      await navigator.clipboard.writeText(buildUrl)
      setCopied(true)
      toast.success('Skopiowano link instalacyjny aplikacji do schowka.')
      setTimeout(() => setCopied(false), 2500)
    } catch {
      toast.error('Nie udało się skopiować linku. Możesz otworzyć go przyciskiem pobierania.')
    }
  }

  return (
    <div className="patient-notice">
      {/* Pasek nawigacyjny */}
      <header className="patient-notice__header">
        <Link to="/patient-portal" className="patient-notice__brand" aria-label="PhysioCare">
          <img
            className="patient-notice__logo"
            src="/brand/logo.png"
            alt="PhysioCare"
            width={160}
            height={88}
          />
        </Link>
        <div className="patient-notice__user-bar">
          <span className="patient-notice__role-badge">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M22 21v-2a4 4 0 0 0-3-3.87" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
            Pacjent
          </span>
          <span className="patient-notice__user-email" title={user?.email}>
            {user?.email}
          </span>
          <Button variant="secondary" size="sm" onClick={() => void logout()}>
            Wyloguj się
          </Button>
        </div>
      </header>

      {/* Główna sekcja informacyjna */}
      <main className="patient-notice__main">
        <div className="patient-notice__grid">
          {/* Kolumna lewa: Powitanie, cele i możliwości aplikacji mobilnej */}
          <section className="patient-notice__intro" aria-labelledby="patient-welcome-heading">
            <div className="patient-notice__pill">
              <svg
                className="patient-notice__pill-icon"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                aria-hidden="true"
              >
                <rect x="5" y="2" width="14" height="20" rx="3" ry="3" />
                <line x1="12" y1="18" x2="12.01" y2="18" strokeWidth="2.5" />
              </svg>
              <span>Aplikacja mobilna PhysioCare</span>
            </div>

            <h1 id="patient-welcome-heading" className="patient-notice__title">
              Witaj, {user?.first_name || 'Pacjencie'}!
            </h1>

            <p className="patient-notice__desc">
              Twoja fizjoterapia, harmonogram spotkań i dedykowane ćwiczenia są zintegrowane
              z aplikacją mobilną PhysioCare. Pobierz aplikację na telefon, aby mieć stały wgląd w
              postępy leczenia i bezpośredni kontakt ze swoim fizjoterapeutą.
            </p>

            <div className="patient-notice__features">
              <article className="patient-notice__feature-item">
                <div className="patient-notice__feature-icon-wrap" aria-hidden="true">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                    <line x1="16" y1="2" x2="16" y2="6" />
                    <line x1="8" y1="2" x2="8" y2="6" />
                    <line x1="3" y1="10" x2="21" y2="10" />
                  </svg>
                </div>
                <div className="patient-notice__feature-content">
                  <h3>Harmonogram i rezerwacja wizyt</h3>
                  <p>Sprawdzaj zbliżające się terminy rehabilitacji, potwierdzaj obecność i planuj kolejne spotkania w gabinecie.</p>
                </div>
              </article>

              <article className="patient-notice__feature-item">
                <div className="patient-notice__feature-icon-wrap" aria-hidden="true">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polygon points="5 3 19 12 5 21 5 3" />
                  </svg>
                </div>
                <div className="patient-notice__feature-content">
                  <h3>Spersonalizowane ćwiczenia wideo</h3>
                  <p>Oglądaj instrukcje wideo zadane przez fizjoterapeutę, sprawdzaj serie i poprawną technikę wykonywania ruchu.</p>
                </div>
              </article>

              <article className="patient-notice__feature-item">
                <div className="patient-notice__feature-icon-wrap" aria-hidden="true">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h24s-3-2-3-9" />
                    <path d="M13.73 21a2 2 0 0 1-3.46 0" />
                  </svg>
                </div>
                <div className="patient-notice__feature-content">
                  <h3>Powiadomienia i przypomnienia</h3>
                  <p>Otrzymuj alerty o nadchodzących wizytach oraz codzienne przypomnienia o realizacji zaplanowanych serii.</p>
                </div>
              </article>

              <article className="patient-notice__feature-item">
                <div className="patient-notice__feature-icon-wrap" aria-hidden="true">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                  </svg>
                </div>
                <div className="patient-notice__feature-content">
                  <h3>Bezpieczna dokumentacja medyczna</h3>
                  <p>Wszystkie zalecenia i karty rehabilitacji są chronione i natychmiast dostępne na Twoim smartfonie.</p>
                </div>
              </article>
            </div>
          </section>

          {/* Kolumna prawa: Kod QR i instalacja */}
          <aside className="patient-notice__card" aria-label="Instalacja aplikacji mobilnej">
            <div className="patient-notice__card-head">
              <div>
                <h2 className="patient-notice__card-title">Zainstaluj na telefonie</h2>
                <p className="patient-notice__card-subtitle">
                  {buildUrl
                    ? 'Zeskanuj aparat telefonu lub pobierz pakiet APK'
                    : 'Aplikacja mobilna dla pacjentów'}
                </p>
              </div>
              <span className="patient-notice__version-chip" title="Status dystrybucji mobilnej">
                <span className="patient-notice__version-dot" aria-hidden="true" />
                {buildUrl ? 'APK v0.1.0' : 'Wkrótce'}
              </span>
            </div>

            {buildUrl ? (
              <>
                {/* Kontener kodu QR */}
                <div className="patient-notice__qr-wrapper">
                  <div className="patient-notice__qr-frame">
                    <QRCodeSVG
                      value={buildUrl}
                      size={190}
                      level="M"
                      bgColor="#ffffff"
                      fgColor="#1b231d"
                      title="Kod QR do pobrania aplikacji mobilnej PhysioCare"
                    />
                  </div>
                  <div className="patient-notice__qr-caption">
                    Zeskanuj aparatem w telefonie
                  </div>
                  <p className="patient-notice__qr-subcaption">
                    Skieruj obiektyw smartfona na powyższy kod, aby bezpośrednio otworzyć stronę instalacji aplikacji.
                  </p>
                </div>

                {/* Kroki instalacji */}
                <ol className="patient-notice__steps">
                  <li className="patient-notice__step">
                    <span className="patient-notice__step-num">1</span>
                    <span>Zeskanuj kod QR aparatem lub kliknij przycisk pobierania.</span>
                  </li>
                  <li className="patient-notice__step">
                    <span className="patient-notice__step-num">2</span>
                    <span>Otwórz oficjalną stronę kompilacji i wybierz opcję <strong>Install / APK</strong>.</span>
                  </li>
                  <li className="patient-notice__step">
                    <span className="patient-notice__step-num">3</span>
                    <span>Po zainstalowaniu zaloguj się kontem <strong>{user?.email}</strong>.</span>
                  </li>
                </ol>

                {/* Akcje instalacyjne */}
                <div className="patient-notice__actions">
                  <a
                    href={buildUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="patient-notice__btn-download"
                  >
                    <span>Pobierz aplikację (Expo / APK)</span>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                      <polyline points="15 3 21 3 21 9" />
                      <line x1="10" y1="14" x2="21" y2="3" />
                    </svg>
                  </a>

                  <div className="patient-notice__actions-row">
                    <button
                      type="button"
                      className="patient-notice__btn-copy"
                      onClick={() => void handleCopyLink()}
                      aria-label="Kopiuj link instalacyjny do schowka"
                    >
                      {copied ? (
                        <>
                          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
                            <polyline points="20 6 9 17 4 12" />
                          </svg>
                          <span>Skopiowano link!</span>
                        </>
                      ) : (
                        <>
                          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                          </svg>
                          <span>Kopiuj link do instalacji</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>

                <p className="patient-notice__card-note">
                  Aplikacja w wersji dystrybucji wewnętrznej (Internal Preview). System Android może wyświetlić standardowy komunikat z prośbą o potwierdzenie instalacji pakietu APK pobranego z przeglądarki.
                </p>
              </>
            ) : (
              <div className="patient-notice__qr-wrapper">
                <div className="patient-notice__feature-icon-wrap" style={{ margin: '0.5rem auto' }} aria-hidden="true">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="5" y="2" width="14" height="20" rx="3" ry="3" />
                    <line x1="12" y1="18" x2="12.01" y2="18" strokeWidth="2.5" />
                  </svg>
                </div>
                <div className="patient-notice__qr-caption">
                  Wydanie mobilne w przygotowaniu
                </div>
                <p className="patient-notice__qr-subcaption">
                  Pakiet instalacyjny aplikacji mobilnej dla pacjentów zostanie wkrótce udostępniony.
                  Skontaktuj się ze swoim fizjoterapeutą lub administratorem gabinetu, aby uzyskać dostęp.
                </p>
              </div>
            )}
          </aside>
        </div>
      </main>

      {/* Stopka */}
      <footer className="patient-notice__footer">
        <span>© {new Date().getFullYear()} PhysioCare. Wszelkie prawa zastrzeżone.</span>
        <nav className="patient-notice__footer-links" aria-label="Nawigacja prawna stopki">
          <Link to="/privacy">Polityka prywatności</Link>
          <Link to="/cookies">Pliki cookies</Link>
          <Link to="/account-deletion">Usuwanie konta</Link>
        </nav>
      </footer>
    </div>
  )
}
