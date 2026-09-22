import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { patientsApi } from '@/api/treatment'
import { getErrorMessage } from '@/api/client'
import type { PatientSummary } from '@/api/types'
import { EmptyState, ErrorBanner, LoadingBlock } from '@/components/AsyncState'
import { PatientsSkeleton } from '@/components/skeletons/WebSkeletons'
import { PageHeader } from '@/components/PageHeader'
import { Field } from '@/components/ui/Field'
import { AuthMediaImg } from '@/components/AuthMedia'
import './PatientsPage.css'

/**
 * Widok Kartoteki Pacjentów z podglądem kartotek, wyszukiwarką po imieniu/nazwisku i nawigacją do detali.
 */
export function PatientsPage() {
  const [patients, setPatients] = useState<PatientSummary[]>([])
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
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
        const data = await patientsApi.list()
        if (!cancelled) {
          setPatients(data)
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
    return () => {
      cancelled = true
    }
  }, [reloadToken])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) {
      return patients
    }
    return patients.filter((patient) => {
      const hay =
        `${patient.first_name} ${patient.last_name} ${patient.email} ${patient.phone ?? ''}`.toLowerCase()
      return hay.includes(q)
    })
  }, [patients, query])

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
          placeholder="Imię, nazwisko, e-mail…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      {error ? <ErrorBanner message={error} onRetry={reload} /> : null}

      {loading ? <LoadingBlock label="Ładowanie listy…" skeleton={<PatientsSkeleton />} /> : null}

      {!loading && !error && filtered.length === 0 ? (
        <EmptyState
          title={patients.length === 0 ? 'Brak pacjentów w gabinecie' : 'Brak wyników'}
          description={
            patients.length === 0
              ? 'Będą tu widoczni pacjenci, którzy dołączą do Twojego gabinetu lub umówią u Ciebie wizytę.'
              : 'Zmień frazę wyszukiwania albo wyczyść filtr.'
          }
        />
      ) : null}

      {!loading && !error && filtered.length > 0 ? (
        <ul className="patients-list">
          {filtered.map((patient) => (
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
      ) : null}
    </section>
  )
}
