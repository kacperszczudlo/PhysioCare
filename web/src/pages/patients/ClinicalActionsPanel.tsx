import { useCallback, useEffect, useId, useState, type FormEvent, type ReactNode } from 'react'

import { treatmentApi } from '@/api/treatment'
import { getErrorMessage } from '@/api/client'
import type {
  BodySide,
  DiagnosticRecommendation,
  FundingHint,
  MedicalDeviceCatalogItem,
  MedicalDeviceOrder,
  PhysicianOrderRefusal,
  ReceptaNaRuchReferral,
  RecommendationType,
} from '@/api/types'
import { EmptyState, ErrorBanner } from '@/components/AsyncState'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import './ClinicalActionsPanel.css'

const RECOMMENDATION_LABELS: Record<RecommendationType, string> = {
  SPECIALIST_CONSULTATION: 'Konsultacja specjalisty',
  IMAGING_MRI: 'Sugestia MRI',
  IMAGING_CT: 'Sugestia TK',
  IMAGING_RTG: 'Sugestia RTG (wymaga lekarza)',
  IMAGING_USG: 'Sugestia USG',
  OTHER: 'Inne',
}

const SIDE_LABELS: Record<BodySide, string> = {
  LEFT: 'Lewa',
  RIGHT: 'Prawa',
  BOTH: 'Obustronnie',
  NA: 'Nie dotyczy',
}

type ClinicalTab = 'recommend' | 'device' | 'refusal' | 'recepta'

interface ClinicalActionsPanelProps {
  patientId: string
  episodeId: string
  onEpisodePossiblyUpdated?: () => void
}

export function ClinicalActionsPanel({
  patientId,
  episodeId,
  onEpisodePossiblyUpdated,
}: ClinicalActionsPanelProps) {
  const baseId = useId()
  const [tab, setTab] = useState<ClinicalTab>('recommend')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [catalog, setCatalog] = useState<MedicalDeviceCatalogItem[]>([])
  const [disclaimer, setDisclaimer] = useState('')

  const [recommendations, setRecommendations] = useState<DiagnosticRecommendation[]>([])
  const [deviceOrders, setDeviceOrders] = useState<MedicalDeviceOrder[]>([])
  const [refusals, setRefusals] = useState<PhysicianOrderRefusal[]>([])
  const [receptaList, setReceptaList] = useState<ReceptaNaRuchReferral[]>([])

  const [recType, setRecType] = useState<RecommendationType>('SPECIALIST_CONSULTATION')
  const [recSpecialty, setRecSpecialty] = useState('')
  const [recArea, setRecArea] = useState('')
  const [recJustification, setRecJustification] = useState('')
  const [recRedFlags, setRecRedFlags] = useState(false)
  const [recFunding, setRecFunding] = useState<FundingHint>('NFZ_VIA_DOCTOR')

  const [deviceCode, setDeviceCode] = useState('')
  const [deviceSide, setDeviceSide] = useState<BodySide>('NA')
  const [deviceIcd10, setDeviceIcd10] = useState('')
  const [deviceNotes, setDeviceNotes] = useState('')

  const [orderDesc, setOrderDesc] = useState('')
  const [refusalReason, setRefusalReason] = useState('')
  const [physicianNotified, setPhysicianNotified] = useState(false)

  const [receptaNotes, setReceptaNotes] = useState('')
  const [receptaReady, setReceptaReady] = useState(false)

  const load = useCallback(async () => {
    setError(null)
    try {
      const [recs, orders, refs, recepta, cat] = await Promise.all([
        treatmentApi.listDiagnosticRecommendations(episodeId),
        treatmentApi.listDeviceOrders(episodeId),
        treatmentApi.listOrderRefusals(episodeId),
        treatmentApi.listReceptaNaRuch(patientId),
        treatmentApi.getMedicalDeviceCatalog(),
      ])
      setRecommendations(recs)
      setDeviceOrders(orders)
      setRefusals(refs)
      setReceptaList(recepta)
      setCatalog(cat.items)
      setDisclaimer(cat.disclaimer)
      setDeviceCode((prev) => {
        if (prev && cat.items.some((item) => item.code === prev && item.allowed_for_therapist)) {
          return prev
        }
        return cat.items.find((item) => item.allowed_for_therapist)?.code ?? ''
      })
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się pobrać kompetencji klinicznych.'))
    }
  }, [episodeId, patientId])

  useEffect(() => {
    void load()
  }, [load])

  async function submitRecommendation(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await treatmentApi.createDiagnosticRecommendation(episodeId, {
        recommendation_type: recType,
        target_specialty: recSpecialty.trim(),
        body_area: recArea.trim(),
        justification: recJustification.trim(),
        red_flags_noted: recRedFlags,
        funding_hint: recFunding,
      })
      setRecJustification('')
      setRecSpecialty('')
      setRecArea('')
      setRecRedFlags(false)
      await load()
      onEpisodePossiblyUpdated?.()
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się zapisać rekomendacji.'))
    } finally {
      setBusy(false)
    }
  }

  async function submitDeviceOrder(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await treatmentApi.createDeviceOrder(episodeId, {
        device_code: deviceCode,
        side: deviceSide,
        icd10_code: deviceIcd10.trim().toUpperCase(),
        notes: deviceNotes.trim(),
      })
      setDeviceNotes('')
      await load()
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się wystawić zlecenia na wyrób.'))
    } finally {
      setBusy(false)
    }
  }

  async function submitRefusal(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await treatmentApi.createOrderRefusal(episodeId, {
        physician_order_description: orderDesc.trim(),
        refusal_reason: refusalReason.trim(),
        physician_notified: physicianNotified,
      })
      setOrderDesc('')
      setRefusalReason('')
      setPhysicianNotified(false)
      await load()
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się zapisać odmowy.'))
    } finally {
      setBusy(false)
    }
  }

  async function submitRecepta(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await treatmentApi.createReceptaNaRuch(patientId, {
        readiness_confirmed: receptaReady,
        activity_notes: receptaNotes.trim(),
        episode: episodeId,
      })
      setReceptaNotes('')
      setReceptaReady(false)
      await load()
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się wystawić skierowania Recepta na Ruch.'))
    } finally {
      setBusy(false)
    }
  }

  const allowedDevices = catalog.filter((item) => item.allowed_for_therapist)

  const tabs: { id: ClinicalTab; label: string; count: number }[] = [
    { id: 'recommend', label: 'Kierowanie', count: recommendations.length },
    { id: 'device', label: 'Wyroby', count: deviceOrders.length },
    { id: 'refusal', label: 'Odmowa', count: refusals.length },
    { id: 'recepta', label: 'Recepta na Ruch', count: receptaList.length },
  ]

  const panelId = `${baseId}-panel-${tab}`

  return (
    <section className="clinical-actions" aria-label="Kompetencje kliniczne">
      <header className="clinical-actions__header">
        <div>
          <h2>Kompetencje kliniczne</h2>
          <p className="clinical-actions__lead">
            Kierowanie pośrednie, wyroby (e-ZWM), odmowa zlecenia i Recepta na Ruch — bez ordynacji leków.
          </p>
        </div>
      </header>

      {disclaimer ? <p className="clinical-actions__disclaimer">{disclaimer}</p> : null}
      {error ? <ErrorBanner message={error} /> : null}

      <div className="clinical-actions__tabs" role="tablist" aria-label="Rodzaj kompetencji">
        {tabs.map((item) => {
          const selected = tab === item.id
          return (
            <button
              key={item.id}
              type="button"
              role="tab"
              id={`${baseId}-tab-${item.id}`}
              aria-selected={selected}
              aria-controls={`${baseId}-panel-${item.id}`}
              tabIndex={selected ? 0 : -1}
              className={
                selected ? 'clinical-actions__tab clinical-actions__tab--active' : 'clinical-actions__tab'
              }
              onClick={() => setTab(item.id)}
            >
              <span>{item.label}</span>
              {item.count > 0 ? (
                <span className="clinical-actions__tab-count" aria-label={`${item.count} w historii`}>
                  {item.count}
                </span>
              ) : null}
            </button>
          )
        })}
      </div>

      <div
        className="clinical-actions__workspace"
        role="tabpanel"
        id={panelId}
        aria-labelledby={`${baseId}-tab-${tab}`}
      >
        {tab === 'recommend' ? (
          <>
            <form className="clinical-actions__compose" onSubmit={(e) => void submitRecommendation(e)}>
              <div className="clinical-actions__compose-head">
                <h3>Nowa rekomendacja</h3>
                <p className="clinical-actions__hint">
                  Opinia dla lekarza — nie jest formalnym e-skierowaniem NFZ na MRI/RTG/TK.
                </p>
              </div>
              <label className="ui-field">
                <span className="ui-field__label">Typ</span>
                <select
                  className="patient-select"
                  value={recType}
                  onChange={(e) => setRecType(e.target.value as RecommendationType)}
                >
                  {(Object.keys(RECOMMENDATION_LABELS) as RecommendationType[]).map((key) => (
                    <option key={key} value={key}>
                      {RECOMMENDATION_LABELS[key]}
                    </option>
                  ))}
                </select>
              </label>
              <div className="clinical-actions__row">
                <Field
                  label="Specjalizacja / cel"
                  name="rec_specialty"
                  value={recSpecialty}
                  onChange={(e) => setRecSpecialty(e.target.value)}
                  placeholder="np. Ortopeda, Neurolog"
                />
                <Field
                  label="Obszar ciała"
                  name="rec_area"
                  value={recArea}
                  onChange={(e) => setRecArea(e.target.value)}
                />
              </div>
              <label className="ui-field">
                <span className="ui-field__label">Uzasadnienie</span>
                <textarea
                  className="patient-textarea"
                  value={recJustification}
                  onChange={(e) => setRecJustification(e.target.value)}
                  rows={3}
                  required
                />
              </label>
              <label className="ui-field">
                <span className="ui-field__label">Finansowanie</span>
                <select
                  className="patient-select"
                  value={recFunding}
                  onChange={(e) => setRecFunding(e.target.value as FundingHint)}
                >
                  <option value="NFZ_VIA_DOCTOR">NFZ — skierowanie wystawia lekarz</option>
                  <option value="PRIVATE">Ścieżka prywatna</option>
                  <option value="NOT_APPLICABLE">Nie dotyczy</option>
                </select>
              </label>
              <label className="clinical-actions__check">
                <input
                  type="checkbox"
                  checked={recRedFlags}
                  onChange={(e) => setRecRedFlags(e.target.checked)}
                />
                Czerwone flagi — wstrzymaj terapię i skieruj do lekarza
              </label>
              <Button type="submit" size="sm" loading={busy}>
                Zapisz rekomendację
              </Button>
            </form>
            <HistoryPane
              title="Historia rekomendacji"
              emptyTitle="Brak rekomendacji"
              emptyDescription="Zapisane kierowania pośrednie pojawią się tutaj."
              isEmpty={recommendations.length === 0}
            >
              {recommendations.map((item) => (
                <li key={item.id} className="clinical-actions__item">
                  <div className="clinical-actions__item-head">
                    <strong>{RECOMMENDATION_LABELS[item.recommendation_type]}</strong>
                    {item.red_flags_noted ? (
                      <span className="clinical-actions__badge clinical-actions__badge--warn">
                        Czerwone flagi
                      </span>
                    ) : null}
                  </div>
                  {(item.target_specialty || item.body_area) && (
                    <p className="clinical-actions__meta">
                      {[item.target_specialty, item.body_area].filter(Boolean).join(' · ')}
                    </p>
                  )}
                  <p>{item.justification}</p>
                </li>
              ))}
            </HistoryPane>
          </>
        ) : null}

        {tab === 'device' ? (
          <>
            <form className="clinical-actions__compose" onSubmit={(e) => void submitDeviceOrder(e)}>
              <div className="clinical-actions__compose-head">
                <h3>Nowe zlecenie</h3>
                <p className="clinical-actions__hint">
                  Model e-ZWM. Katalog filtrowany wg kwalifikacji (magister / FIZJO SPEC).
                </p>
              </div>
              <label className="ui-field">
                <span className="ui-field__label">Wyrób</span>
                <select
                  className="patient-select"
                  value={deviceCode}
                  onChange={(e) => setDeviceCode(e.target.value)}
                  required
                >
                  {allowedDevices.length === 0 ? (
                    <option value="">Brak wyrobów w Twoich kompetencjach</option>
                  ) : (
                    allowedDevices.map((item) => (
                      <option key={item.code} value={item.code}>
                        [{item.group}] {item.name}
                      </option>
                    ))
                  )}
                </select>
              </label>
              <div className="clinical-actions__row">
                <label className="ui-field">
                  <span className="ui-field__label">Strona</span>
                  <select
                    className="patient-select"
                    value={deviceSide}
                    onChange={(e) => setDeviceSide(e.target.value as BodySide)}
                  >
                    {(Object.keys(SIDE_LABELS) as BodySide[]).map((key) => (
                      <option key={key} value={key}>
                        {SIDE_LABELS[key]}
                      </option>
                    ))}
                  </select>
                </label>
                <Field
                  label="ICD-10 (wymagany do zlecenia)"
                  name="device_icd10"
                  value={deviceIcd10}
                  onChange={(e) => setDeviceIcd10(e.target.value)}
                  placeholder="np. M25.5"
                  required
                />
              </div>
              <label className="ui-field">
                <span className="ui-field__label">Notatka</span>
                <textarea
                  className="patient-textarea"
                  value={deviceNotes}
                  onChange={(e) => setDeviceNotes(e.target.value)}
                  rows={2}
                />
              </label>
              <Button type="submit" size="sm" loading={busy} disabled={allowedDevices.length === 0}>
                Wystaw zlecenie
              </Button>
            </form>
            <HistoryPane
              title="Historia zleceń"
              emptyTitle="Brak zleceń"
              emptyDescription="Wystawione zlecenia na wyroby medyczne pojawią się tutaj."
              isEmpty={deviceOrders.length === 0}
            >
              {deviceOrders.map((item) => (
                <li key={item.id} className="clinical-actions__item">
                  <div className="clinical-actions__item-head">
                    <strong>
                      [{item.device_group}] {item.device_name}
                    </strong>
                    <span className="clinical-actions__badge">{item.status}</span>
                  </div>
                  <p className="clinical-actions__meta">
                    {item.icd10_code} · {SIDE_LABELS[item.side]}
                  </p>
                  {item.notes ? <p>{item.notes}</p> : null}
                </li>
              ))}
            </HistoryPane>
          </>
        ) : null}

        {tab === 'refusal' ? (
          <>
            <form className="clinical-actions__compose" onSubmit={(e) => void submitRefusal(e)}>
              <div className="clinical-actions__compose-head">
                <h3>Nowa odmowa</h3>
                <p className="clinical-actions__hint">
                  Art. 6 ust. 2 — uzasadnienie w dokumentacji + informacja dla lekarza.
                </p>
              </div>
              <label className="ui-field">
                <span className="ui-field__label">Zlecenie lekarskie</span>
                <textarea
                  className="patient-textarea"
                  value={orderDesc}
                  onChange={(e) => setOrderDesc(e.target.value)}
                  rows={2}
                  required
                />
              </label>
              <label className="ui-field">
                <span className="ui-field__label">Uzasadnienie odmowy</span>
                <textarea
                  className="patient-textarea"
                  value={refusalReason}
                  onChange={(e) => setRefusalReason(e.target.value)}
                  rows={3}
                  required
                />
              </label>
              <label className="clinical-actions__check">
                <input
                  type="checkbox"
                  checked={physicianNotified}
                  onChange={(e) => setPhysicianNotified(e.target.checked)}
                />
                Poinformowano lekarza zlecającego
              </label>
              <Button type="submit" size="sm" loading={busy}>
                Zapisz odmowę
              </Button>
            </form>
            <HistoryPane
              title="Historia odmów"
              emptyTitle="Brak odmów"
              emptyDescription="Zapisane odmowy zleceń lekarskich pojawią się tutaj."
              isEmpty={refusals.length === 0}
            >
              {refusals.map((item) => (
                <li key={item.id} className="clinical-actions__item">
                  <div className="clinical-actions__item-head">
                    <strong>{item.physician_order_description}</strong>
                    <span
                      className={
                        item.physician_notified
                          ? 'clinical-actions__badge clinical-actions__badge--ok'
                          : 'clinical-actions__badge clinical-actions__badge--warn'
                      }
                    >
                      {item.physician_notified ? 'Lekarz powiadomiony' : 'Do powiadomienia'}
                    </span>
                  </div>
                  <p>{item.refusal_reason}</p>
                </li>
              ))}
            </HistoryPane>
          </>
        ) : null}

        {tab === 'recepta' ? (
          <>
            <form className="clinical-actions__compose" onSubmit={(e) => void submitRecepta(e)}>
              <div className="clinical-actions__compose-head">
                <h3>Nowe skierowanie</h3>
                <p className="clinical-actions__hint">
                  Program profilaktyczny (mojeIKP) — fizjoterapeuta jest uprawniony.
                </p>
              </div>
              <label className="ui-field">
                <span className="ui-field__label">Notatka z oceny aktywności</span>
                <textarea
                  className="patient-textarea"
                  value={receptaNotes}
                  onChange={(e) => setReceptaNotes(e.target.value)}
                  rows={2}
                />
              </label>
              <label className="clinical-actions__check">
                <input
                  type="checkbox"
                  checked={receptaReady}
                  onChange={(e) => setReceptaReady(e.target.checked)}
                  required
                />
                Potwierdzam weryfikację gotowości do wysiłku
              </label>
              <Button type="submit" size="sm" loading={busy}>
                Wystaw skierowanie
              </Button>
            </form>
            <HistoryPane
              title="Historia skierowań"
              emptyTitle="Brak skierowań"
              emptyDescription="Skierowania Recepta na Ruch pojawią się tutaj."
              isEmpty={receptaList.length === 0}
            >
              {receptaList.map((item) => (
                <li key={item.id} className="clinical-actions__item">
                  <div className="clinical-actions__item-head">
                    <strong>Recepta na Ruch</strong>
                    <span className="clinical-actions__badge">{item.status}</span>
                  </div>
                  <p>{item.activity_notes || 'Bez notatki'}</p>
                </li>
              ))}
            </HistoryPane>
          </>
        ) : null}
      </div>
    </section>
  )
}

function HistoryPane({
  title,
  emptyTitle,
  emptyDescription,
  isEmpty,
  children,
}: {
  title: string
  emptyTitle: string
  emptyDescription: string
  isEmpty: boolean
  children: ReactNode
}) {
  return (
    <div className="clinical-actions__history">
      <h3>{title}</h3>
      {isEmpty ? (
        <EmptyState title={emptyTitle} description={emptyDescription} />
      ) : (
        <ul className="clinical-actions__list">{children}</ul>
      )}
    </div>
  )
}
