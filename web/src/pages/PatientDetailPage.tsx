import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'

import { patientsApi, treatmentApi } from '@/api/treatment'
import { getErrorMessage } from '@/api/client'
import type { EpisodeStatus, PatientDetail, TreatmentEpisode, VisitNote } from '@/api/types'
import { EmptyState, ErrorBanner, LoadingBlock } from '@/components/AsyncState'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import { EPISODE_STATUS_LABELS } from '@/lib/bodyMap'
import { FIELD_MESSAGES, getIcd10Error } from '@/lib/fieldPolicy'
import { DiagnosticMapper } from '@/pages/patients/DiagnosticMapper'
import { ClinicalActionsPanel } from '@/pages/patients/ClinicalActionsPanel'
import { PatientAssignments } from '@/pages/patients/PatientAssignments'
import './PatientDetailPage.css'

const STATUS_OPTIONS: EpisodeStatus[] = [
  'IN_PROGRESS',
  'COMPLETED_SUCCESS',
  'REFERRED',
  'INTERRUPTED',
]

export function PatientDetailPage() {
  const { patientId = '' } = useParams()
  const [patient, setPatient] = useState<PatientDetail | null>(null)
  const [episodes, setEpisodes] = useState<TreatmentEpisode[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [notes, setNotes] = useState<VisitNote[]>([])
  const [loading, setLoading] = useState(true)
  const [notesLoading, setNotesLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const [icd10, setIcd10] = useState('')
  const [functionalDiagnosis, setFunctionalDiagnosis] = useState('')
  const [summary, setSummary] = useState('')
  const [status, setStatus] = useState<EpisodeStatus>('IN_PROGRESS')
  const [noteContent, setNoteContent] = useState('')
  const [newIcd10, setNewIcd10] = useState('')
  const [newSummary, setNewSummary] = useState('')
  const [icd10Error, setIcd10Error] = useState<string | null>(null)
  const [newIcd10Error, setNewIcd10Error] = useState<string | null>(null)
  const [noteError, setNoteError] = useState<string | null>(null)
  const [pdfTitle, setPdfTitle] = useState('')
  const [pdfFile, setPdfFile] = useState<File | null>(null)
  const [pdfBusy, setPdfBusy] = useState(false)
  const [pdfMessage, setPdfMessage] = useState<string | null>(null)

  const selected = episodes.find((episode) => episode.id === selectedId) ?? null

  const loadPatient = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [profile, episodeList] = await Promise.all([
        patientsApi.get(patientId),
        treatmentApi.listEpisodes(patientId),
      ])
      setPatient(profile)
      setEpisodes(episodeList)
      setSelectedId((prev) => {
        if (prev && episodeList.some((item) => item.id === prev)) {
          return prev
        }
        return episodeList[0]?.id ?? null
      })
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się otworzyć karty pacjenta.'))
      setPatient(null)
      setEpisodes([])
    } finally {
      setLoading(false)
    }
  }, [patientId])

  useEffect(() => {
    void loadPatient()
  }, [loadPatient])

  useEffect(() => {
    if (!selected) {
      setIcd10('')
      setFunctionalDiagnosis('')
      setSummary('')
      setStatus('IN_PROGRESS')
      setNotes([])
      return
    }
    setIcd10(selected.icd10_code ?? '')
    setFunctionalDiagnosis(selected.functional_diagnosis ?? '')
    setSummary(selected.summary_note ?? '')
    setStatus(selected.status)

    let cancelled = false
    async function loadNotes() {
      setNotesLoading(true)
      try {
        const data = await treatmentApi.listNotes(selected!.id)
        if (!cancelled) {
          setNotes(data)
        }
      } catch (err) {
        if (!cancelled) {
          setError(getErrorMessage(err, 'Nie udało się pobrać notatek.'))
        }
      } finally {
        if (!cancelled) {
          setNotesLoading(false)
        }
      }
    }
    void loadNotes()
    return () => {
      cancelled = true
    }
  }, [selected])

  async function createEpisode(event: FormEvent) {
    event.preventDefault()
    const icdError = getIcd10Error(newIcd10)
    if (icdError) {
      setNewIcd10Error(icdError)
      return
    }
    setNewIcd10Error(null)
    setBusy(true)
    setError(null)
    try {
      const created = await treatmentApi.createEpisode(patientId, {
        icd10_code: newIcd10.trim().toUpperCase(),
        summary_note: newSummary.trim(),
        status: 'IN_PROGRESS',
      })
      setEpisodes((prev) => [created, ...prev])
      setSelectedId(created.id)
      setNewIcd10('')
      setNewSummary('')
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się utworzyć epizodu.'))
    } finally {
      setBusy(false)
    }
  }

  async function saveEpisode(event: FormEvent) {
    event.preventDefault()
    if (!selected) {
      return
    }
    const icdError = getIcd10Error(icd10)
    if (icdError) {
      setIcd10Error(icdError)
      return
    }
    setIcd10Error(null)
    setBusy(true)
    setError(null)
    try {
      const updated = await treatmentApi.updateEpisode(selected.id, {
        icd10_code: icd10.trim().toUpperCase(),
        functional_diagnosis: functionalDiagnosis.trim(),
        summary_note: summary.trim(),
        status,
        ended_at:
          status === 'IN_PROGRESS'
            ? null
            : (selected.ended_at ?? new Date().toISOString().slice(0, 10)),
      })
      setEpisodes((prev) => prev.map((item) => (item.id === updated.id ? updated : item)))
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się zapisać epizodu.'))
    } finally {
      setBusy(false)
    }
  }

  async function addNote(event: FormEvent) {
    event.preventDefault()
    if (!selected) {
      return
    }
    if (!noteContent.trim()) {
      setNoteError(FIELD_MESSAGES.noteRequired)
      return
    }
    setNoteError(null)
    setBusy(true)
    setError(null)
    try {
      const created = await treatmentApi.createNote(selected.id, noteContent.trim())
      setNotes((prev) => [created, ...prev])
      setNoteContent('')
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się dodać notatki.'))
    } finally {
      setBusy(false)
    }
  }

  async function uploadPdf(event: FormEvent) {
    event.preventDefault()
    if (!pdfFile) {
      setPdfMessage('Wybierz plik PDF.')
      return
    }
    const title = pdfTitle.trim() || pdfFile.name.replace(/\.pdf$/i, '')
    setPdfBusy(true)
    setPdfMessage(null)
    setError(null)
    try {
      await treatmentApi.uploadDocument({
        patientId,
        title,
        file: pdfFile,
        episodeId: selectedId,
      })
      setPdfTitle('')
      setPdfFile(null)
      setPdfMessage('PDF udostępniony pacjentowi w skrzynce dokumentacji.')
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się wgrać dokumentu PDF.'))
    } finally {
      setPdfBusy(false)
    }
  }

  if (loading) {
    return (
      <section>
        <LoadingBlock label="Ładowanie karty…" variant="panel" />
      </section>
    )
  }

  if (!patient) {
    return (
      <section>
        <PageHeader title="Pacjent" description="Nie znaleziono karty." />
        {error ? <ErrorBanner message={error} onRetry={() => void loadPatient()} /> : null}
        <Link to="/patients">Wróć do listy</Link>
      </section>
    )
  }

  return (
    <section className="patient-detail">
      <PageHeader
        title={`${patient.first_name} ${patient.last_name}`}
        description={`${patient.email}${patient.phone ? ` · ${patient.phone}` : ''}`}
        actions={
          <Button type="button" variant="secondary" onClick={() => void loadPatient()}>
            Odśwież
          </Button>
        }
      />

      <p className="patient-back">
        <Link to="/patients">← Pacjenci</Link>
      </p>

      {error ? <ErrorBanner message={error} /> : null}

      <PatientAssignments patientId={patient.id} />

      <section className="patient-pdf-upload" aria-label="Udostępnij PDF pacjentowi">
        <h2>Dokument PDF dla pacjenta</h2>
        <p className="patient-notes__lead">
          Plik trafia od razu do skrzynki dokumentacji w aplikacji pacjenta.
        </p>
        <form className="patient-pdf-upload__form" onSubmit={(e) => void uploadPdf(e)}>
          <Field
            label="Tytuł"
            name="pdf_title"
            value={pdfTitle}
            onChange={(e) => setPdfTitle(e.target.value)}
            placeholder="np. Karta oceny funkcjonalnej"
          />
          <label className="ui-field">
            <span className="ui-field__label">Plik PDF</span>
            <input
              type="file"
              accept="application/pdf,.pdf"
              onChange={(e) => setPdfFile(e.target.files?.[0] ?? null)}
            />
          </label>
          <Button type="submit" size="sm" loading={pdfBusy} disabled={!pdfFile}>
            Udostępnij PDF
          </Button>
          {pdfMessage ? (
            <p className="patient-muted" role="status">
              {pdfMessage}
            </p>
          ) : null}
        </form>
      </section>

      <div className="patient-layout">
        <aside className="patient-rail" aria-label="Epizody i notatki">
          <section className="patient-episodes">
            <h2>Epizody</h2>
            <ul className="patient-episodes__list">
              {episodes.map((episode) => (
                <li key={episode.id}>
                  <button
                    type="button"
                    className={
                      episode.id === selectedId
                        ? 'patient-episodes__item patient-episodes__item--active'
                        : 'patient-episodes__item'
                    }
                    onClick={() => setSelectedId(episode.id)}
                  >
                    <span className="patient-episodes__code">
                      {episode.icd10_code || 'Bez ICD-10'}
                    </span>
                    <span className="patient-episodes__status">
                      {EPISODE_STATUS_LABELS[episode.status] ?? episode.status}
                    </span>
                  </button>
                </li>
              ))}
            </ul>

            {episodes.length === 0 ? (
              <EmptyState
                title="Brak epizodów"
                description="Utwórz pierwszy epizod leczenia, aby prowadzić dokumentację i mapę ciała."
              />
            ) : null}

            <form className="patient-episodes__create" onSubmit={(e) => void createEpisode(e)}>
              <h3>Nowy epizod</h3>
              <Field
                label="ICD-10"
                name="new_icd10"
                value={newIcd10}
                onChange={(e) => {
                  setNewIcd10(e.target.value)
                  if (newIcd10Error) {
                    setNewIcd10Error(null)
                  }
                }}
                error={newIcd10Error ?? undefined}
                placeholder="np. M54.5"
                hint="Opcjonalnie - format litery + 2 cyfry, np. M54.5"
              />
              <label className="ui-field">
                <span className="ui-field__label">Opis wstępny</span>
                <textarea
                  className="patient-textarea"
                  value={newSummary}
                  onChange={(e) => setNewSummary(e.target.value)}
                  rows={2}
                />
              </label>
              <Button type="submit" size="sm" loading={busy}>
                + Nowy epizod
              </Button>
            </form>
          </section>

          {selected ? (
            <section className="patient-notes" aria-label="Notatki z wizyt">
              <header className="patient-notes__header">
                <div>
                  <h2>Notatki kliniczne</h2>
                  <p className="patient-notes__lead">
                    Tylko dla Ciebie. Podsumowanie dla pacjenta wpisz w edycji wizyty w kalendarzu.
                  </p>
                </div>
                {!notesLoading && notes.length > 0 ? (
                  <span className="patient-notes__count" aria-label={`${notes.length} notatek`}>
                    {notes.length}
                  </span>
                ) : null}
              </header>

              <form className="patient-notes__compose" onSubmit={(e) => void addNote(e)}>
                <label className="ui-field">
                  <span className="ui-field__label">Nowa notatka</span>
                  <textarea
                    className="patient-textarea"
                    value={noteContent}
                    onChange={(e) => {
                      setNoteContent(e.target.value)
                      if (noteError) {
                        setNoteError(null)
                      }
                    }}
                    rows={3}
                    required
                    placeholder="Obserwacje, reakcja na terapię…"
                    aria-invalid={noteError ? true : undefined}
                  />
                  {noteError ? (
                    <span className="ui-field__error" role="alert">
                      {noteError}
                    </span>
                  ) : null}
                </label>
                <Button type="submit" size="sm" loading={busy}>
                  Dodaj notatkę
                </Button>
              </form>

              <div className="patient-notes__timeline">
                {notesLoading ? <p className="patient-muted">Ładowanie notatek…</p> : null}
                {!notesLoading && notes.length === 0 ? (
                  <EmptyState title="Brak notatek" description="Dodaj pierwszą notatkę z wizyty." />
                ) : null}
                {!notesLoading && notes.length > 0 ? (
                  <ol className="patient-notes__list">
                    {notes.map((note) => (
                      <li key={note.id} className="patient-notes__item">
                        <time dateTime={note.created_at}>
                          {new Intl.DateTimeFormat('pl-PL', {
                            dateStyle: 'medium',
                            timeStyle: 'short',
                          }).format(new Date(note.created_at))}
                        </time>
                        <p>{note.content}</p>
                      </li>
                    ))}
                  </ol>
                ) : null}
              </div>
            </section>
          ) : null}
        </aside>

        <div className="patient-main">
          {!selected ? (
            <p className="patient-muted">Wybierz lub utwórz epizod, aby prowadzić dokumentację.</p>
          ) : (
            <>
              <form className="patient-episode-form" onSubmit={(e) => void saveEpisode(e)}>
                <h2>Dokumentacja epizodu</h2>
                <div className="patient-episode-form__row">
                  <Field
                    label="ICD-10 (z dokumentacji / roboczy)"
                    name="icd10"
                    value={icd10}
                    onChange={(e) => {
                      setIcd10(e.target.value)
                      if (icd10Error) {
                        setIcd10Error(null)
                      }
                    }}
                    error={icd10Error ?? undefined}
                    hint="Kod z skierowania/dokumentacji lekarskiej — nie zastępuje diagnozy nozologicznej lekarza"
                  />
                  <label className="ui-field">
                    <span className="ui-field__label">Status</span>
                    <select
                      className="patient-select"
                      value={status}
                      onChange={(e) => setStatus(e.target.value as EpisodeStatus)}
                    >
                      {STATUS_OPTIONS.map((value) => (
                        <option key={value} value={value}>
                          {EPISODE_STATUS_LABELS[value]}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <label className="ui-field">
                  <span className="ui-field__label">Diagnoza funkcjonalna</span>
                  <textarea
                    className="patient-textarea"
                    value={functionalDiagnosis}
                    onChange={(e) => setFunctionalDiagnosis(e.target.value)}
                    rows={3}
                    placeholder="Deficyty ruchowe, biomechanika, zakresy, siła, stabilność…"
                  />
                  <span className="ui-field__hint">Widoczna dla pacjenta w aplikacji mobilnej.</span>
                </label>
                <label className="ui-field">
                  <span className="ui-field__label">Podsumowanie planu (dla pacjenta)</span>
                  <textarea
                    className="patient-textarea"
                    value={summary}
                    onChange={(e) => setSummary(e.target.value)}
                    rows={4}
                    placeholder="Krótko i zrozumiale: cele terapii, na czym się skupiacie…"
                  />
                </label>
                <Button type="submit" loading={busy}>
                  Zapisz epizod
                </Button>
              </form>

              <DiagnosticMapper episodeId={selected.id} />

              <ClinicalActionsPanel
                patientId={patient.id}
                episodeId={selected.id}
                onEpisodePossiblyUpdated={() => void loadPatient()}
              />
            </>
          )}
        </div>
      </div>
    </section>
  )
}
