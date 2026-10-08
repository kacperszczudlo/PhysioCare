import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { patientsApi } from '@/api/treatment'
import { getErrorMessage } from '@/api/client'
import type { PatientSummary } from '@/api/types'
import { EmptyState, ErrorBanner, LoadingBlock } from '@/components/AsyncState'
import { PatientsSkeleton } from '@/components/skeletons/WebSkeletons'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import { AuthMediaImg } from '@/components/AuthMedia'
import './PatientsPage.css'

const PAGE_SIZE = 20

/**
 * Widok Kartoteki Pacjentów z podglądem kartotek, serwerową paginacją oraz wyszukiwarką.
 */
export function PatientsPage() {
  const [patients, setPatients] = useState<PatientSummary[]>([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reloadToken, setReloadToken] = useState(0)

  const reload = useCallback(() => {
    setReloadToken((value) => value + 1)
  }, [])

  useEffect(() => {
    let cancelled = false
    const timer = setTimeout(() => {
      async function load() {
        setLoading(true)
        setError(null)
        try {
          const res = await patientsApi.getPaginated({
            page,
            search: query.trim() || undefined,
          })
          if (!cancelled) {
            setPatients(res.results)
            setCount(res.count)
          }
        } catch (err) {
          if (!cancelled) {
            setError(getErrorMessage(err, 'Nie udało się pobrać pacjentów.'))
          }
        } finally {
          if (!cancelled) {
            setLoading(false)
          }
        }
      }
      void load()
    }, 200)

    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [page, query, reloadToken])

  return (
    <section className="patients-page">
      <PageHeader
        title="Pacjenci"
        description="Wyszukaj pacjenta i otwórz kartę z epizodami leczenia oraz mapą ciała."
      />

      <div className="patients-toolbar">
        <Field
          label="Szukaj"
          name="q"
          placeholder="Imię, nazwisko, e-mail, telefon…"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            setPage(1)
          }}
        />
      </div>

      {error ? <ErrorBanner message={error} onRetry={reload} /> : null}

      {loading ? <LoadingBlock label="Ładowanie listy…" skeleton={<PatientsSkeleton />} /> : null}

      {!loading && !error && patients.length === 0 ? (
        <EmptyState
          title={query.trim() ? 'Brak wyników wyszukiwania' : 'Brak pacjentów w gabinecie'}
          description={
            query.trim()
              ? 'Nie znaleziono pacjentów pasujących do podanej frazy. Zmień frazę lub wyczyść pole.'
              : 'Będą tu widoczni pacjenci, którzy dołączą do Twojego gabinetu lub umówią u Ciebie wizytę.'
          }
        />
      ) : null}

      {!loading && !error && patients.length > 0 ? (
        <div className="patients-card">
          <ul className="patients-list">
            {patients.map((patient) => (
              <li key={patient.id}>
                <Link className="patients-row" to={`/patients/${patient.id}`}>
                  <span className="patients-row__identity">
                    {patient.avatar_url ? (
                      <AuthMediaImg path={patient.avatar_url} className="patients-row__avatar" />
                    ) : (
                      <span
                        className="patients-row__avatar patients-row__avatar--placeholder"
                        aria-hidden
                      >
                        {(patient.first_name?.[0] ?? '') + (patient.last_name?.[0] ?? '')}
                      </span>
                    )}
                    <span className="patients-row__name">
                      {patient.first_name} {patient.last_name}
                    </span>
                  </span>
                  <span className="patients-row__meta">{patient.email}</span>
                  <span className="patients-row__meta">{patient.phone || '-'}</span>
                </Link>
              </li>
            ))}
          </ul>

          {/* Paginacja */}
          <div className="patients-pagination">
            <span className="patients-pagination__info">
              Strona {page} z {Math.max(1, Math.ceil(count / PAGE_SIZE))} (łącznie {count}{' '}
              {count === 1 ? 'pacjent' : 'pacjentów'})
            </span>
            <div className="patients-pagination__controls">
              <Button
                type="button"
                variant="secondary"
                size="sm"
                disabled={page <= 1 || loading}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Poprzednia
              </Button>
              <Button
                type="button"
                variant="secondary"
                size="sm"
                disabled={page * PAGE_SIZE >= count || loading}
                onClick={() => setPage((p) => p + 1)}
              >
                Następna
              </Button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  )
}
