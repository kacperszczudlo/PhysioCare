import { useCallback, useEffect, useState, type FormEvent } from 'react'

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
import { ErrorBanner } from '@/components/AsyncState'
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

  return (
    <section className="clinical-actions" aria-label="Kompetencje kliniczne">
      <h2>Kompetencje kliniczne</h2>
      <p className="clinical-actions__lead">
        Diagnoza funkcjonalna, kierowanie pośrednie, wyroby medyczne (e-ZWM) i art. 6 u.o.z.f.
        Fizjoterapeuta nie ordynuje leków ani maści farmaceutycznych.
      </p>
      {disclaimer ? <p className="clinical-actions__disclaimer">{disclaimer}</p> : null}
      {error ? <ErrorBanner message={error} /> : null}

      <div className="clinical-actions__grid">
        <form className="clinical-actions__card" onSubmit={(e) => void submitRecommendation(e)}>
          <h3>Kierowanie pośrednie</h3>
          <p className="clinical-actions__hint">
            Opinia dla lekarza — nie jest formalnym e-skierowaniem NFZ na MRI/RTG/TK.
          </p>
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
          <ul className="clinical-actions__list">
            {recommendations.map((item) => (
              <li key={item.id}>
                <strong>{RECOMMENDATION_LABELS[item.recommendation_type]}</strong>
                {item.red_flags_noted ? ' · czerwone flagi' : ''}
                <p>{item.justification}</p>
              </li>
            ))}
          </ul>
        </form>

        <form className="clinical-actions__card" onSubmit={(e) => void submitDeviceOrder(e)}>
          <h3>Zlecenie na wyrób medyczny</h3>
          <p className="clinical-actions__hint">
            Model e-ZWM w aplikacji. Katalog filtrowany wg kwalifikacji (magister / FIZJO SPEC).
          </p>
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
          <ul className="clinical-actions__list">
            {deviceOrders.map((item) => (
              <li key={item.id}>
                <strong>
                  [{item.device_group}] {item.device_name}
                </strong>
                <p>
                  {item.icd10_code} · {SIDE_LABELS[item.side]} · {item.status}
                </p>
              </li>
            ))}
          </ul>
        </form>

        <form className="clinical-actions__card" onSubmit={(e) => void submitRefusal(e)}>
          <h3>Odmowa zlecenia lekarskiego</h3>
          <p className="clinical-actions__hint">Art. 6 ust. 2 — uzasadnienie w dokumentacji + informacja dla lekarza.</p>
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
          <ul className="clinical-actions__list">
            {refusals.map((item) => (
              <li key={item.id}>
                <strong>{item.physician_notified ? 'Lekarz powiadomiony' : 'Do powiadomienia'}</strong>
                <p>{item.refusal_reason}</p>
              </li>
            ))}
          </ul>
        </form>

        <form className="clinical-actions__card" onSubmit={(e) => void submitRecepta(e)}>
          <h3>Recepta na Ruch</h3>
          <p className="clinical-actions__hint">
            Skierowanie do programu profilaktycznego (mojeIKP) — fizjoterapeuta jest uprawniony.
          </p>
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
          <ul className="clinical-actions__list">
            {receptaList.map((item) => (
              <li key={item.id}>
                <strong>{item.status}</strong>
                <p>{item.activity_notes || 'Bez notatki'}</p>
              </li>
            ))}
          </ul>
        </form>
      </div>
    </section>
  )
}
