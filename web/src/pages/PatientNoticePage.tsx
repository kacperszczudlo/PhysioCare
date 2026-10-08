import { useAuth } from '@/auth/AuthContext'
import { Button } from '@/components/ui/Button'
import './auth-forms.css'

/**
 * Widok informacyjny dla pacjentów logujących się przez przeglądarkę internetową.
 * Kieruje użytkownika do dedykowanej aplikacji mobilnej PhysioCare.
 */
export function PatientNoticePage() {
  const { user, logout } = useAuth()

  return (
    <div
      style={{
        display: 'grid',
        placeItems: 'center',
        minHeight: '80vh',
        padding: '2rem 1rem',
      }}
    >
      <div
        style={{
          maxWidth: '540px',
          width: '100%',
          textAlign: 'center',
          padding: '2.5rem 2rem',
          background: 'var(--color-surface, #ffffff)',
          borderRadius: 'var(--radius-lg, 12px)',
          border: '1px solid var(--color-border, #e2e8f0)',
          boxShadow: 'var(--shadow-lg, 0 10px 25px -5px rgba(0,0,0,0.1))',
        }}
      >
        <div
          style={{
            width: '64px',
            height: '64px',
            borderRadius: '50%',
            background: 'var(--color-primary-light, #e0f2fe)',
            color: 'var(--color-primary, #0284c7)',
            display: 'grid',
            placeItems: 'center',
            margin: '0 auto 1.5rem',
            fontSize: '2rem',
          }}
        >
          📱
        </div>

        <h1 style={{ fontSize: '1.5rem', marginBottom: '0.75rem', fontWeight: 700 }}>
          Witaj, {user?.first_name || 'Pacjencie'}!
        </h1>

        <p
          style={{
            color: 'var(--color-text-muted, #64748b)',
            lineHeight: 1.6,
            marginBottom: '1.75rem',
          }}
        >
          Twój profil pacjenta jest w pełni zintegrowany z{' '}
          <strong>aplikacją mobilną PhysioCare</strong>. Aby przeglądać harmonogram wizyt, wykonywać
          zadane ćwiczenia wideo oraz otrzymywać przypomnienia, skorzystaj z aplikacji na telefonie.
        </p>

        <div
          style={{
            padding: '1rem',
            background: 'var(--color-bg-secondary, #f8fafc)',
            borderRadius: 'var(--radius-md, 8px)',
            marginBottom: '1.75rem',
            fontSize: '0.9rem',
            color: 'var(--color-text-secondary, #475569)',
          }}
        >
          Zalogowano jako: <strong>{user?.email}</strong> (Rola: Pacjent)
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem' }}>
          <Button variant="secondary" onClick={() => void logout()}>
            Wyloguj się
          </Button>
        </div>
      </div>
    </div>
  )
}
