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
import { Modal } from '@/components/ui/Modal'
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

type DeleteTarget =
  | { kind: 'recommendation'; id: string; label: string }
  | { kind: 'device'; id: string; label: string }
  | { kind: 'refusal'; id: string; label: string }
  | { kind: 'recepta'; id: string; label: string }

type EditTarget =
  | { kind: 'recommendation'; item: DiagnosticRecommendation }
  | { kind: 'device'; item: MedicalDeviceOrder }
  | { kind: 'refusal'; item: PhysicianOrderRefusal }
  | { kind: 'recepta'; item: ReceptaNaRuchReferral }

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
  const [deleteTarget, setDeleteTarget] = useState<DeleteTarget | null>(null)
  const [editTarget, setEditTarget] = useState<EditTarget | null>(null)
  const [editFormError, setEditFormError] = useState<string | null>(null)

  const [editRecType, setEditRecType] = useState<RecommendationType>('SPECIALIST_CONSULTATION')
  const [editRecSpecialty, setEditRecSpecialty] = useState('')
  const [editRecArea, setEditRecArea] = useState('')
  const [editRecJustification, setEditRecJustification] = useState('')
  const [editRecRedFlags, setEditRecRedFlags] = useState(false)
  const [editRecFunding, setEditRecFunding] = useState<FundingHint>('NFZ_VIA_DOCTOR')

  const [editDeviceCode, setEditDeviceCode] = useState('')
  const [editDeviceSide, setEditDeviceSide] = useState<BodySide>('NA')
  const [editDeviceIcd10, setEditDeviceIcd10] = useState('')
  const [editDeviceNotes, setEditDeviceNotes] = useState('')

  const [editOrderDesc, setEditOrderDesc] = useState('')
  const [editRefusalReason, setEditRefusalReason] = useState('')
  const [editPhysicianNotified, setEditPhysicianNotified] = useState(false)

  const [editReceptaNotes, setEditReceptaNotes] = useState('')
  const [editReceptaReady, setEditReceptaReady] = useState(true)

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

  function openEdit(target: EditTarget) {
    setEditFormError(null)
    setEditTarget(target)
    if (target.kind === 'recommendation') {
      setEditRecType(target.item.recommendation_type)
      setEditRecSpecialty(target.item.target_specialty)
      setEditRecArea(target.item.body_area)
      setEditRecJustification(target.item.justification)
      setEditRecRedFlags(target.item.red_flags_noted)
      setEditRecFunding(target.item.funding_hint)
    } else if (target.kind === 'device') {
      setEditDeviceCode(target.item.device_code)
      setEditDeviceSide(target.item.side)
      setEditDeviceIcd10(target.item.icd10_code)
      setEditDeviceNotes(target.item.notes)
    } else if (target.kind === 'refusal') {
      setEditOrderDesc(target.item.physician_order_description)
      setEditRefusalReason(target.item.refusal_reason)
      setEditPhysicianNotified(target.item.physician_notified)
    } else {
      setEditReceptaNotes(target.item.activity_notes)
      setEditReceptaReady(target.item.readiness_confirmed)
    }
  }

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

  async function confirmDelete() {
    if (!deleteTarget) {
      return
    }
    setBusy(true)
    setError(null)
    try {
      if (deleteTarget.kind === 'recommendation') {
        await treatmentApi.deleteDiagnosticRecommendation(episodeId, deleteTarget.id)
      } else if (deleteTarget.kind === 'device') {
        await treatmentApi.deleteDeviceOrder(episodeId, deleteTarget.id)
      } else if (deleteTarget.kind === 'refusal') {
        await treatmentApi.deleteOrderRefusal(episodeId, deleteTarget.id)
      } else {
        await treatmentApi.deleteReceptaNaRuch(patientId, deleteTarget.id)
      }
      setDeleteTarget(null)
      await load()
      onEpisodePossiblyUpdated?.()
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się usunąć dokumentu.'))
    } finally {
      setBusy(false)
    }
  }

  async function saveEdit(event: FormEvent) {
    event.preventDefault()
    if (!editTarget) {
      return
    }
    setBusy(true)
    setEditFormError(null)
    try {
      if (editTarget.kind === 'recommendation') {
        await treatmentApi.updateDiagnosticRecommendation(episodeId, editTarget.item.id, {
          recommendation_type: editRecType,
          target_specialty: editRecSpecialty.trim(),
          body_area: editRecArea.trim(),
          justification: editRecJustification.trim(),
          red_flags_noted: editRecRedFlags,
          funding_hint: editRecFunding,
        })
      } else if (editTarget.kind === 'device') {
        await treatmentApi.updateDeviceOrder(episodeId, editTarget.item.id, {
          device_code: editDeviceCode,
          side: editDeviceSide,
          icd10_code: editDeviceIcd10.trim().toUpperCase(),
          notes: editDeviceNotes.trim(),
        })
      } else if (editTarget.kind === 'refusal') {
        await treatmentApi.updateOrderRefusal(episodeId, editTarget.item.id, {
          physician_order_description: editOrderDesc.trim(),
          refusal_reason: editRefusalReason.trim(),
          physician_notified: editPhysicianNotified,
        })
      } else {
        await treatmentApi.updateReceptaNaRuch(patientId, editTarget.item.id, {
          readiness_confirmed: editReceptaReady,
          activity_notes: editReceptaNotes.trim(),
          episode: episodeId,
        })
      }
      setEditTarget(null)
      await load()
      onEpisodePossiblyUpdated?.()
    } catch (err) {
      setEditFormError(getErrorMessage(err, 'Nie udało się zapisać zmian.'))
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
  const editTitle =
    editTarget?.kind === 'recommendation'
      ? 'Edytuj rekomendację'
      : editTarget?.kind === 'device'
        ? 'Edytuj zlecenie'
        : editTarget?.kind === 'refusal'
          ? 'Edytuj odmowę'
          : 'Edytuj Receptę na Ruch'

  return (
    <section className="clinical-actions" aria-label="Kompetencje kliniczne">
      <header className="clinical-actions__header">
        <div>
          <h2>Kompetencje kliniczne</h2>
          <p className="clinical-actions__lead">
            Kierowanie pośrednie, wyroby (e-ZWM), odmowa zlecenia i Recepta na Ruch — bez ordynacji leków.
            Wystawione wpisy są od razu widoczne pacjentowi w aplikacji (zakładka Dokumentacja).
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
                    <div className="clinical-actions__item-actions">
                      {item.red_flags_noted ? (
                        <span className="clinical-actions__badge clinical-actions__badge--warn">
                          Czerwone flagi
                        </span>
                      ) : null}
                      <div className="clinical-actions__item-toolbar">
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          disabled={busy}
                          onClick={() => openEdit({ kind: 'recommendation', item })}
                        >
                          Edytuj
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          disabled={busy}
                          onClick={() =>
                            setDeleteTarget({
                              kind: 'recommendation',
                              id: item.id,
                              label: RECOMMENDATION_LABELS[item.recommendation_type],
                            })
                          }
                        >
                          Usuń
                        </Button>
                      </div>
                    </div>
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
                  label="ICD-10"
                  name="device_icd10"
                  value={deviceIcd10}
                  onChange={(e) => setDeviceIcd10(e.target.value)}
                  placeholder="np. M25.5"
                  hint="Wymagany do zlecenia"
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
                    <div className="clinical-actions__item-actions">
                      <span className="clinical-actions__badge">{item.status}</span>
                      <div className="clinical-actions__item-toolbar">
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          disabled={busy}
                          onClick={() => openEdit({ kind: 'device', item })}
                        >
                          Edytuj
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          disabled={busy}
                          onClick={() =>
                            setDeleteTarget({
                              kind: 'device',
                              id: item.id,
                              label: item.device_name,
                            })
                          }
                        >
                          Usuń
                        </Button>
                      </div>
                    </div>
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
                    <div className="clinical-actions__item-actions">
                      <span
                        className={
                          item.physician_notified
                            ? 'clinical-actions__badge clinical-actions__badge--ok'
                            : 'clinical-actions__badge clinical-actions__badge--warn'
                        }
                      >
                        {item.physician_notified ? 'Lekarz powiadomiony' : 'Do powiadomienia'}
                      </span>
                      <div className="clinical-actions__item-toolbar">
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          disabled={busy}
                          onClick={() => openEdit({ kind: 'refusal', item })}
                        >
                          Edytuj
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          disabled={busy}
                          onClick={() =>
                            setDeleteTarget({
                              kind: 'refusal',
                              id: item.id,
                              label: item.physician_order_description.slice(0, 80),
                            })
                          }
                        >
                          Usuń
                        </Button>
                      </div>
                    </div>
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
                    <div className="clinical-actions__item-actions">
                      <span className="clinical-actions__badge">{item.status}</span>
                      <div className="clinical-actions__item-toolbar">
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          disabled={busy}
                          onClick={() => openEdit({ kind: 'recepta', item })}
                        >
                          Edytuj
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          disabled={busy}
                          onClick={() =>
                            setDeleteTarget({
                              kind: 'recepta',
                              id: item.id,
                              label: 'Recepta na Ruch',
                            })
                          }
                        >
                          Usuń
                        </Button>
                      </div>
                    </div>
                  </div>
                  <p>{item.activity_notes || 'Bez notatki'}</p>
                </li>
              ))}
            </HistoryPane>
          </>
        ) : null}
      </div>

      <Modal
        open={editTarget !== null}
        title={editTitle}
        description="Zmiany będą od razu widoczne w Dokumentacji pacjenta."
        onClose={() => setEditTarget(null)}
      >
        <form className="ui-modal__form" onSubmit={(e) => void saveEdit(e)}>
          {editTarget?.kind === 'recommendation' ? (
            <>
              <label className="ui-field">
                <span className="ui-field__label">Typ</span>
                <select
                  className="patient-select"
                  value={editRecType}
                  onChange={(e) => setEditRecType(e.target.value as RecommendationType)}
                >
                  {(Object.keys(RECOMMENDATION_LABELS) as RecommendationType[]).map((key) => (
                    <option key={key} value={key}>
                      {RECOMMENDATION_LABELS[key]}
                    </option>
                  ))}
                </select>
              </label>
              <Field
                label="Specjalizacja / cel"
                name="edit_rec_specialty"
                value={editRecSpecialty}
                onChange={(e) => setEditRecSpecialty(e.target.value)}
              />
              <Field
                label="Obszar ciała"
                name="edit_rec_area"
                value={editRecArea}
                onChange={(e) => setEditRecArea(e.target.value)}
              />
              <label className="ui-field">
                <span className="ui-field__label">Uzasadnienie</span>
                <textarea
                  className="patient-textarea"
                  value={editRecJustification}
                  onChange={(e) => setEditRecJustification(e.target.value)}
                  rows={3}
                  required
                />
              </label>
              <label className="ui-field">
                <span className="ui-field__label">Finansowanie</span>
                <select
                  className="patient-select"
                  value={editRecFunding}
                  onChange={(e) => setEditRecFunding(e.target.value as FundingHint)}
                >
                  <option value="NFZ_VIA_DOCTOR">NFZ — skierowanie wystawia lekarz</option>
                  <option value="PRIVATE">Ścieżka prywatna</option>
                  <option value="NOT_APPLICABLE">Nie dotyczy</option>
                </select>
              </label>
              <label className="clinical-actions__check">
                <input
                  type="checkbox"
                  checked={editRecRedFlags}
                  onChange={(e) => setEditRecRedFlags(e.target.checked)}
                />
                Czerwone flagi
              </label>
            </>
          ) : null}

          {editTarget?.kind === 'device' ? (
            <>
              <label className="ui-field">
                <span className="ui-field__label">Wyrób</span>
                <select
                  className="patient-select"
                  value={editDeviceCode}
                  onChange={(e) => setEditDeviceCode(e.target.value)}
                  required
                >
                  {allowedDevices.map((item) => (
                    <option key={item.code} value={item.code}>
                      [{item.group}] {item.name}
                    </option>
                  ))}
                  {!allowedDevices.some((item) => item.code === editDeviceCode) && editDeviceCode ? (
                    <option value={editDeviceCode}>{editDeviceCode} (obecny)</option>
                  ) : null}
                </select>
              </label>
              <label className="ui-field">
                <span className="ui-field__label">Strona</span>
                <select
                  className="patient-select"
                  value={editDeviceSide}
                  onChange={(e) => setEditDeviceSide(e.target.value as BodySide)}
                >
                  {(Object.keys(SIDE_LABELS) as BodySide[]).map((key) => (
                    <option key={key} value={key}>
                      {SIDE_LABELS[key]}
                    </option>
                  ))}
                </select>
              </label>
              <Field
                label="ICD-10"
                name="edit_device_icd10"
                value={editDeviceIcd10}
                onChange={(e) => setEditDeviceIcd10(e.target.value)}
                required
              />
              <label className="ui-field">
                <span className="ui-field__label">Notatka</span>
                <textarea
                  className="patient-textarea"
                  value={editDeviceNotes}
                  onChange={(e) => setEditDeviceNotes(e.target.value)}
                  rows={2}
                />
              </label>
            </>
          ) : null}

          {editTarget?.kind === 'refusal' ? (
            <>
              <label className="ui-field">
                <span className="ui-field__label">Zlecenie lekarskie</span>
                <textarea
                  className="patient-textarea"
                  value={editOrderDesc}
                  onChange={(e) => setEditOrderDesc(e.target.value)}
                  rows={2}
                  required
                />
              </label>
              <label className="ui-field">
                <span className="ui-field__label">Uzasadnienie odmowy</span>
                <textarea
                  className="patient-textarea"
                  value={editRefusalReason}
                  onChange={(e) => setEditRefusalReason(e.target.value)}
                  rows={3}
                  required
                />
              </label>
              <label className="clinical-actions__check">
                <input
                  type="checkbox"
                  checked={editPhysicianNotified}
                  onChange={(e) => setEditPhysicianNotified(e.target.checked)}
                />
                Poinformowano lekarza zlecającego
              </label>
            </>
          ) : null}

          {editTarget?.kind === 'recepta' ? (
            <>
              <label className="ui-field">
                <span className="ui-field__label">Notatka z oceny aktywności</span>
                <textarea
                  className="patient-textarea"
                  value={editReceptaNotes}
                  onChange={(e) => setEditReceptaNotes(e.target.value)}
                  rows={2}
                />
              </label>
              <label className="clinical-actions__check">
                <input
                  type="checkbox"
                  checked={editReceptaReady}
                  onChange={(e) => setEditReceptaReady(e.target.checked)}
                  required
                />
                Potwierdzam weryfikację gotowości do wysiłku
              </label>
            </>
          ) : null}

          {editFormError ? (
            <p className="ui-modal__error" role="alert">
              {editFormError}
            </p>
          ) : null}
          <div className="ui-modal__actions">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setEditTarget(null)}
              disabled={busy}
            >
              Anuluj
            </Button>
            <Button type="submit" loading={busy}>
              Zapisz zmiany
            </Button>
          </div>
        </form>
      </Modal>

      <Modal
        open={deleteTarget !== null}
        title="Usuń dokument"
        description={
          deleteTarget
            ? `„${deleteTarget.label}” zniknie z karty pacjenta i z zakładki Dokumentacja w aplikacji pacjenta.`
            : undefined
        }
        onClose={() => setDeleteTarget(null)}
      >
        <div className="ui-modal__form">
          <div className="ui-modal__actions">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setDeleteTarget(null)}
              disabled={busy}
            >
              Anuluj
            </Button>
            <Button type="button" onClick={() => void confirmDelete()} loading={busy}>
              Usuń
            </Button>
          </div>
        </div>
      </Modal>
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
