import { useCallback, useEffect, useState } from 'react'

import { adminApi } from '@/api/admin'
import type { AdminTherapistStats } from '@/api/types'
import { LoadingBlock } from '@/components/AsyncState'
import { PageHeader } from '@/components/PageHeader'
import { useToast } from '@/components/ui/ToastContext'
import { IconStar } from './AdminIcons'
import './AdminTherapistsPage.css'

function initials(first?: string, last?: string): string {
  const value = `${first?.charAt(0) ?? ''}${last?.charAt(0) ?? ''}`.toUpperCase()
  return value || 'F'
}

/**
 * Widok zestawienia personelu medycznego i efektywności fizjoterapeutów.
 * Prezentuje kwalifikacje, numer PWZFz, wskaźniki wizyt oraz oceny pacjentów.
 */
export function AdminTherapistsPage() {
  const { toast } = useToast()
  const [therapists, setTherapists] = useState<AdminTherapistStats[]>([])
  const [isLoading, setIsLoading] = useState(true)

  const fetchStats = useCallback(async () => {
    setIsLoading(true)
    try {
      const data = await adminApi.getTherapistStats()
      setTherapists(data)
    } catch {
      toast.error('Nie udało się pobrać statystyk personelu.')
    } finally {
      setIsLoading(false)
    }
  }, [toast])

  useEffect(() => {
    void fetchStats()
  }, [fetchStats])

  return (
    <div className="admin-therapists-page">
      <PageHeader
        title="Zespół Fizjoterapeutów"
        description="Weryfikacja uprawnień PWZFz, poziomów kwalifikacji, statystyk zrealizowanych wizyt i ocen pacjentów."
      />

      {isLoading ? (
        <LoadingBlock label="Ładowanie profilów personelu…" />
      ) : therapists.length === 0 ? (
        <div className="admin-therapists-empty">
          <p>Brak zarejestrowanych profili fizjoterapeutów w systemie.</p>
        </div>
      ) : (
        <div className="admin-therapists-grid">
          {therapists.map((t) => (
            <div key={t.therapist_id} className="admin-therapist-card">
              <div className="admin-therapist-card__top">
                <div className="admin-therapist-card__identity">
                  <span className="admin-user-avatar admin-user-avatar--lg">
                    {initials(t.first_name, t.last_name)}
                  </span>
                  <div>
                    <h2 className="admin-therapist-card__name">
                      {t.first_name} {t.last_name}
                    </h2>
                    <span className="admin-therapist-card__email">{t.email}</span>
                  </div>
                </div>

                <div className="admin-therapist-card__rating">
                  <div className="admin-rating-badge">
                    <IconStar className="admin-rating-star" />
                    <span>{t.rating_avg.toFixed(2)}</span>
                  </div>
                  <span className="admin-rating-count">
                    {t.rating_count === 1 ? '1 opinia' : `${t.rating_count} opinii`}
                  </span>
                </div>
              </div>

              {/* Dane zawodowe */}
              <div className="admin-therapist-card__credentials">
                <div className="admin-credential-row">
                  <span className="admin-credential-label">Numer PWZFz:</span>
                  <strong className="admin-credential-value">{t.pwzf_number}</strong>
                </div>
                <div className="admin-credential-row">
                  <span className="admin-credential-label">Kwalifikacja:</span>
                  <strong className="admin-credential-value">{t.qualification_level}</strong>
                </div>
                <div className="admin-credential-row">
                  <span className="admin-credential-label">Doświadczenie:</span>
                  <strong className="admin-credential-value">{t.experience_years} lat</strong>
                </div>
              </div>

              {/* Metryki wizyt fizjoterapeuty */}
              <div className="admin-therapist-metrics">
                <div className="admin-therapist-metric admin-therapist-metric--completed">
                  <div className="admin-therapist-metric__num">{t.completed_visits}</div>
                  <div className="admin-therapist-metric__label">Zakończone</div>
                </div>

                <div className="admin-therapist-metric admin-therapist-metric--cancelled">
                  <div className="admin-therapist-metric__num">{t.cancelled_visits}</div>
                  <div className="admin-therapist-metric__label">Odwołane</div>
                </div>

                <div className="admin-therapist-metric admin-therapist-metric--noshow">
                  <div className="admin-therapist-metric__num">{t.no_show_visits}</div>
                  <div className="admin-therapist-metric__label">No-Show</div>
                </div>
              </div>

              <div className="admin-therapist-card__footer">
                <span className="admin-therapist-footer-text">
                  Łącznie wizyt w historii: <strong>{t.total_visits}</strong>
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
