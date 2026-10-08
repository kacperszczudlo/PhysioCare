import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { adminApi } from '@/api/admin'
import type { AdminDashboardStats } from '@/api/types'
import { LoadingBlock } from '@/components/AsyncState'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/Button'
import {
  IconActivity,
  IconCalendar,
  IconStar,
  IconStethoscope,
  IconUsers,
} from './AdminIcons'
import './AdminDashboardPage.css'

export function AdminDashboardPage() {
  const [stats, setStats] = useState<AdminDashboardStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchStats = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await adminApi.getDashboardStats()
      setStats(data)
    } catch {
      setError('Nie udało się pobrać statystyk systemu. Spróbuj ponownie.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void fetchStats()
  }, [])

  if (isLoading) {
    return <LoadingBlock label="Ładowanie wskaźników analitycznych…" />
  }

  if (error || !stats) {
    return (
      <div className="admin-error-block">
        <p className="admin-error-msg">{error || 'Wystąpił błąd podczas ładowania pulpitu.'}</p>
        <Button onClick={() => void fetchStats()}>Spróbuj ponownie</Button>
      </div>
    )
  }

  const ratingAvg = stats.quality?.rating_avg ?? 0
  const ratingCount = stats.quality?.rating_count ?? 0
  const totalExercises = stats.exercises?.total_exercises ?? 0
  const totalAssignments = stats.exercises?.total_assignments ?? 0
  const scheduledVisits = stats.visits?.scheduled ?? 0
  const completedVisits = stats.visits?.completed ?? 0
  const cancelledVisits = stats.visits?.cancelled ?? 0
  const noShowVisits = stats.visits?.no_show ?? 0
  const showUpRate = stats.visits?.show_up_rate_percent ?? 100

  return (
    <div className="admin-dashboard">
      <PageHeader
        title="Pulpit Administracyjny"
        description="Główne wskaźniki efektywności, statystyki bazy użytkowników i jakość kliniki PhysioCare."
      />

      {/* Siatka głównych kart metryk (KPI) */}
      <div className="admin-metrics-grid">
        {/* Karta Użytkowników */}
        <div className="admin-metric-card admin-metric-card--users">
          <div className="admin-metric-card__header">
            <span className="admin-metric-card__label">Użytkownicy</span>
            <div className="admin-metric-card__icon">
              <IconUsers />
            </div>
          </div>
          <div className="admin-metric-card__value">{stats.users.total}</div>
          <div className="admin-metric-card__breakdown">
            <div className="admin-breakdown-row">
              <span className="admin-breakdown-row__dot admin-breakdown-row__dot--patient" />
              <span>Pacjenci (Aplikacja):</span>
              <strong>{stats.users.patients_count}</strong>
            </div>
            <div className="admin-breakdown-row">
              <span className="admin-breakdown-row__dot admin-breakdown-row__dot--therapist" />
              <span>Fizjoterapeuci (Web):</span>
              <strong>{stats.users.therapists_count}</strong>
            </div>
            <div className="admin-breakdown-row">
              <span className="admin-breakdown-row__dot admin-breakdown-row__dot--admin" />
              <span>Administratorzy:</span>
              <strong>{stats.users.admins_count}</strong>
            </div>
          </div>
          <div className="admin-metric-card__footer">
            <span className="admin-trend-badge">
              +{stats.users.new_last_30_days} nowych w ost. 30 dniach
            </span>
          </div>
        </div>

        {/* Karta Wizyt i Grafiku */}
        <div className="admin-metric-card admin-metric-card--visits">
          <div className="admin-metric-card__header">
            <span className="admin-metric-card__label">Wizyty i Grafik</span>
            <div className="admin-metric-card__icon">
              <IconCalendar />
            </div>
          </div>
          <div className="admin-metric-card__value">{stats.visits.total}</div>
          <div className="admin-metric-card__breakdown">
            <div className="admin-breakdown-row">
              <span>Zaplanowane:</span>
              <strong>{scheduledVisits}</strong>
            </div>
            <div className="admin-breakdown-row">
              <span>Zakończone:</span>
              <strong>{completedVisits}</strong>
            </div>
            <div className="admin-breakdown-row">
              <span>Odwołane / No-Show:</span>
              <strong>{cancelledVisits + noShowVisits}</strong>
            </div>
          </div>
          <div className="admin-metric-card__footer">
            <span className="admin-metric-card__subtext">
              Frekwencja: {showUpRate.toFixed(1)}%
            </span>
          </div>
        </div>

        {/* Karta Jakości i Recenzji */}
        <div className="admin-metric-card admin-metric-card--reviews">
          <div className="admin-metric-card__header">
            <span className="admin-metric-card__label">Jakość i Opinie</span>
            <div className="admin-metric-card__icon">
              <IconStar />
            </div>
          </div>
          <div className="admin-metric-card__value">
            {ratingAvg.toFixed(2)}
            <span className="admin-metric-card__unit"> / 5.0</span>
          </div>
          <div className="admin-metric-card__breakdown">
            <div className="admin-breakdown-row">
              <span>Liczba opinii:</span>
              <strong>{ratingCount}</strong>
            </div>
            <div className="admin-breakdown-row">
              <span>Zadowolenie pacjentów:</span>
              <strong>
                {ratingAvg >= 4.5
                  ? 'Bardzo wysokie'
                  : ratingAvg >= 3.5
                    ? 'Dobre'
                    : 'Wymaga uwagi'}
              </strong>
            </div>
          </div>
          <div className="admin-metric-card__footer">
            <Link to="/admin/reviews" className="admin-inline-link">
              Przejdź do moderacji →
            </Link>
          </div>
        </div>

        {/* Karta Rehabilitacji i Treningów */}
        <div className="admin-metric-card admin-metric-card--activity">
          <div className="admin-metric-card__header">
            <span className="admin-metric-card__label">Rehabilitacja i Plany</span>
            <div className="admin-metric-card__icon">
              <IconActivity />
            </div>
          </div>
          <div className="admin-metric-card__value">{totalAssignments}</div>
          <div className="admin-metric-card__breakdown">
            <div className="admin-breakdown-row">
              <span>Ćwiczenia w bazie:</span>
              <strong>{totalExercises}</strong>
            </div>
            <div className="admin-breakdown-row">
              <span>Zadane programy:</span>
              <strong>{totalAssignments}</strong>
            </div>
          </div>
          <div className="admin-metric-card__footer">
            <span className="admin-metric-card__subtext">Aktywne plany treningowe HEP</span>
          </div>
        </div>
      </div>

      {/* Panele nawigacyjne i szybkie linki */}
      <div className="admin-actions-grid">
        <div className="admin-action-card">
          <div className="admin-action-card__icon">
            <IconUsers />
          </div>
          <div className="admin-action-card__content">
            <h2 className="admin-action-card__title">Baza Użytkowników</h2>
            <p className="admin-action-card__desc">
              Przeglądaj bazę kont, kontroluj statusy pacjentów i fizjoterapeutów, blokuj naruszenia
              oraz realizuj procedury RODO.
            </p>
          </div>
          <Link to="/admin/users" className="admin-action-card__btn">
            <Button variant="primary">Otwórz listę użytkowników</Button>
          </Link>
        </div>

        <div className="admin-action-card">
          <div className="admin-action-card__icon">
            <IconStethoscope />
          </div>
          <div className="admin-action-card__content">
            <h2 className="admin-action-card__title">Zespół i Harmonogramy</h2>
            <p className="admin-action-card__desc">
              Weryfikuj uprawnienia zawodowe PWZFz, obłożenie gabinetów, dostępność czasową personelu
              oraz statystyki zrealizowanych terapii.
            </p>
          </div>
          <div className="admin-action-card__btn-group">
            <Link to="/admin/schedules">
              <Button variant="secondary">Zbiorczy grafik</Button>
            </Link>
            <Link to="/admin/therapists">
              <Button variant="primary">Zespół personelu</Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
