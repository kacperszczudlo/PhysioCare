import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { therapistApi } from '@/api/auth'
import { ApiError } from '@/api/client'
import type { DashboardStats } from '@/api/types'
import { useAuth } from '@/auth/AuthContext'
import { PageHeader } from '@/components/PageHeader'
import './DashboardPage.css'

export function DashboardPage() {
  const { user } = useAuth()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

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
          setError(err instanceof ApiError ? err.message : 'Nie udało się pobrać statystyk.')
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
  }, [])

  const greeting = user?.first_name ? `Dzień dobry, ${user.first_name}` : 'Pulpit'

  return (
    <section>
      <PageHeader
        title={greeting}
        description="Szybki przegląd dnia i skróty do najważniejszych czynności."
      />

      {loading ? (
        <div className="dash-grid" aria-busy="true" aria-live="polite">
          <div className="dash-stat dash-stat--skeleton" />
          <div className="dash-stat dash-stat--skeleton" />
        </div>
      ) : null}

      {error ? (
        <p className="dash-error" role="alert">
          {error}
        </p>
      ) : null}

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
    </section>
  )
}
