import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { patientsApi } from '@/api/treatment'
import { ApiError } from '@/api/client'
import type { PatientSummary } from '@/api/types'
import { PageHeader } from '@/components/PageHeader'
import { Field } from '@/components/ui/Field'
import './PatientsPage.css'

export function PatientsPage() {
  const [patients, setPatients] = useState<PatientSummary[]>([])
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

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
          setError(err instanceof ApiError ? err.message : 'Nie udało się pobrać pacjentów.')
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

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) {
      return patients
    }
    return patients.filter((patient) => {
      const hay = `${patient.first_name} ${patient.last_name} ${patient.email} ${patient.phone ?? ''}`.toLowerCase()
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

      {error ? (
        <p className="patients-banner patients-banner--error" role="alert">
          {error}
        </p>
      ) : null}

      {loading ? (
        <p className="patients-muted" aria-busy="true">
          Ładowanie listy…
        </p>
      ) : null}

      {!loading && filtered.length === 0 ? (
        <p className="patients-empty" role="status">
          {patients.length === 0
            ? 'Brak pacjentów w gabinecie. Pojawią się po rejestracji w aplikacji mobilnej z Twoim therapist_id.'
            : 'Brak wyników dla podanego filtra.'}
        </p>
      ) : null}

      {!loading && filtered.length > 0 ? (
        <ul className="patients-list">
          {filtered.map((patient) => (
            <li key={patient.id}>
              <Link className="patients-row" to={`/patients/${patient.id}`}>
                <span className="patients-row__name">
                  {patient.first_name} {patient.last_name}
                </span>
                <span className="patients-row__meta">{patient.email}</span>
                <span className="patients-row__meta">{patient.phone || '—'}</span>
              </Link>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  )
}
