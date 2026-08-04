import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { therapistApi } from '@/api/auth'
import { getErrorMessage } from '@/api/client'
import type { DashboardStats } from '@/api/types'
import { useAuth } from '@/auth/AuthContext'
import { EmptyState, ErrorBanner, LoadingBlock } from '@/components/AsyncState'
import { PageHeader } from '@/components/PageHeader'
import './DashboardPage.css'

export function DashboardPage() {
  const { user } = useAuth()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [reloadToken, setReloadToken] = useState(0)

  const reload = useCallback(() => {
    setReloadToken((value) => value + 1)
  }, [])

  useEffect(() => {
    let cancelled = false

    async function load() {
      setLoading(true)
      setError(null)
      try {
        const data = await therapistApi.getDashboardStats()
        if (!cancelled) {
          setStats(data)
        }
      } catch (err) {
        if (!cancelled) {
          setStats(null)
          setError(getErrorMessage(err, 'Nie udało się pobrać statystyk.'))
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [reloadToken])

  const greeting = user?.first_name ? `Dzień dobry, ${user.first_name}` : 'Pulpit'

  return (
    <section className="dashboard">
      <PageHeader
        title={greeting}
        description="Szybki przegląd dnia i skróty do najważniejszych czynności."
      />

      {loading ? <LoadingBlock label="Ładowanie pulpitu…" variant="panel" /> : null}

      {error ? <ErrorBanner message={error} onRetry={reload} /> : null}

      {!loading && !error && stats ? (
        <div className="dash-grid">
          <article className="dash-stat">
            <p className="dash-stat__label">Wizyty dziś</p>
            <p className="dash-stat__value">{stats.visits_today}</p>
          </article>
          <article className="dash-stat">
            <p className="dash-stat__label">Pacjenci</p>
            <p className="dash-stat__value">{stats.patients_total}</p>
          </article>
        </div>
      ) : null}

      {!loading && !error && stats && stats.visits_today === 0 ? (
        <EmptyState
          title="Brak wizyt na dziś"
          description="Dodaj termin w harmonogramie albo wróć tu jutro."
        />
      ) : null}

      {!loading ? (
        <div className="dash-actions">
          <Link className="dash-action" to="/schedule">
            Otwórz harmonogram
          </Link>
          <Link className="dash-action" to="/patients">
            Lista pacjentów
          </Link>
          <Link className="dash-action" to="/exercises">
            Baza ćwiczeń
          </Link>
        </div>
      ) : null}
    </section>
  )
}
