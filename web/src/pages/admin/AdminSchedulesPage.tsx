import { useCallback, useEffect, useState } from 'react'

import { adminApi } from '@/api/admin'
import type { AdminSchedulingOverview } from '@/api/types'
import { LoadingBlock } from '@/components/AsyncState'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/Button'
import { Select } from '@/components/ui/Select'
import { useToast } from '@/components/ui/ToastContext'
import './AdminSchedulesPage.css'
/**
 * Zbiorczy widok harmonogramów wizyt i slotów dostępności personelu medycznego.
 * Umożliwia monitorowanie obłożenia gabinetów i grafików fizjoterapeutów w wybranym oknie czasowym.
 */
export function AdminSchedulesPage() {
  const { toast } = useToast()
  const [data, setData] = useState<AdminSchedulingOverview | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [selectedTherapistId, setSelectedTherapistId] = useState<string>('')

  // Zakres dat - domyślnie 7 dni od dzisiaj
  const [dateOffsetDays, setDateOffsetDays] = useState(0)

  const fetchOverview = useCallback(async () => {
    setIsLoading(true)
    try {
      const now = new Date()
      const start = new Date(now.getTime() + dateOffsetDays * 86400000)
      const end = new Date(start.getTime() + 7 * 86400000)

      const res = await adminApi.getSchedulingOverview({
        date_from: start.toISOString(),
        date_to: end.toISOString(),
        therapist_id: selectedTherapistId || undefined,
      })
      setData(res)
    } catch {
      toast.error('Nie udało się pobrać grafiku wizyt.')
    } finally {
      setIsLoading(false)
    }
  }, [dateOffsetDays, selectedTherapistId, toast])

  useEffect(() => {
    void fetchOverview()
  }, [fetchOverview])

  const visitStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return { label: 'Zakończona', className: 'admin-status-pill admin-status-pill--active' }
      case 'SCHEDULED':
        return { label: 'Zaplanowana', className: 'admin-badge admin-badge--therapist' }
      case 'CANCELLED':
        return { label: 'Odwołana', className: 'admin-status-pill admin-status-pill--blocked' }
      case 'NO_SHOW':
        return { label: 'Nieobecność', className: 'admin-badge admin-badge--admin' }
      case 'PENDING_APPROVAL':
        return { label: 'Oczekuje', className: 'admin-badge' }
      default:
        return { label: status, className: 'admin-badge' }
    }
  }

  return (
    <div className="admin-schedules-page">
      <PageHeader
        title="Harmonogramy & Kalendarz Kliniki"
        description="Zbiorczy podgląd obłożenia fizjoterapeutów, slotów przyjęć oraz statusów wizyt."
        actions={
          <div className="admin-schedule-nav">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setDateOffsetDays((prev) => prev - 7)}
            >
              ← Poprzedni tydzień
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setDateOffsetDays(0)}
            >
              Bieżący tydzień
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setDateOffsetDays((prev) => prev + 7)}
            >
              Następny tydzień →
            </Button>
          </div>
        }
      />

      {/* Pasek filtrów */}
      <div className="admin-schedules-filters">
        <label className="admin-filter-label" htmlFor="therapist-filter">
          Filtruj po fizjoterapeucie:
        </label>
        <Select
          id="therapist-filter"
          className="admin-filter-control"
          value={selectedTherapistId}
          onChange={(val) => setSelectedTherapistId(val)}
          options={[
            { value: '', label: 'Wszyscy fizjoterapeuci' },
            ...(data?.therapists.map((t) => ({
              value: t.id,
              label: `${t.name} (${t.qualification_level})`,
            })) ?? []),
          ]}
          ariaLabel="Filtruj po fizjoterapeucie"
        />
      </div>

      {isLoading || !data ? (
        <LoadingBlock label="Ładowanie harmonogramu…" />
      ) : (
        <div className="admin-schedules-content">
          {/* Podsumowanie wizyt w wybranym oknie czasowym */}
          <div className="admin-schedules-kpi">
            <div className="admin-schedule-kpi-card">
              <span className="admin-schedule-kpi-card__label">Wizyt w oknie</span>
              <span className="admin-schedule-kpi-card__val">{data.visits.length}</span>
            </div>
            <div className="admin-schedule-kpi-card">
              <span className="admin-schedule-kpi-card__label">Zaplanowane</span>
              <span className="admin-schedule-kpi-card__val admin-schedule-kpi-card__val--info">
                {data.visits.filter((v) => v.status === 'SCHEDULED').length}
              </span>
            </div>
            <div className="admin-schedule-kpi-card">
              <span className="admin-schedule-kpi-card__label">Zakończone</span>
              <span className="admin-schedule-kpi-card__val admin-schedule-kpi-card__val--success">
                {data.visits.filter((v) => v.status === 'COMPLETED').length}
              </span>
            </div>
            <div className="admin-schedule-kpi-card">
              <span className="admin-schedule-kpi-card__label">Odwołane / No-Show</span>
              <span className="admin-schedule-kpi-card__val admin-schedule-kpi-card__val--danger">
                {
                  data.visits.filter(
                    (v) => v.status === 'CANCELLED' || v.status === 'NO_SHOW',
                  ).length
                }
              </span>
            </div>
          </div>

          {/* Lista wizyt w oknie czasowym */}
          <div className="admin-table-container">
            <div className="admin-table-scroll">
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>Data i godzina</th>
                    <th>Pacjent</th>
                    <th>Fizjoterapeuta</th>
                    <th>Usługa</th>
                    <th className="admin-th-actions">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.visits.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="admin-td-empty">
                        Brak zaplanowanych wizyt w wybranym przedziale czasowym.
                      </td>
                    </tr>
                  ) : (
                    data.visits.map((v) => {
                      const badge = visitStatusBadge(v.status)
                      return (
                        <tr key={v.id}>
                          <td className="admin-date-cell">
                            <strong>{new Date(v.start_at).toLocaleDateString('pl-PL')}</strong>{' '}
                            {new Date(v.start_at).toLocaleTimeString('pl-PL', {
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                            {' - '}
                            {new Date(v.end_at).toLocaleTimeString('pl-PL', {
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </td>
                          <td>
                            <strong>{v.patient_name}</strong>
                          </td>
                          <td>{v.therapist_name}</td>
                          <td className="admin-service-cell">
                            <div>{v.therapy_type_name}</div>
                            {v.location_address && (
                              <div style={{ fontSize: '0.75rem', color: 'var(--color-muted)' }}>
                                {v.location_address}
                              </div>
                            )}
                          </td>
                          <td className="admin-td-actions">
                            <span className={badge.className}>{badge.label}</span>
                          </td>
                        </tr>
                      )
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
