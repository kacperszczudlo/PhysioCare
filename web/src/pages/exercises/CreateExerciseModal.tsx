import { useEffect, useId, useRef, useState, type DragEvent, type FormEvent } from 'react'

import { exercisesApi } from '@/api/exercises'
import { getErrorMessage } from '@/api/client'
import type { ExerciseCategory, MediaType } from '@/api/types'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import { Modal } from '@/components/ui/Modal'
import './CreateExerciseModal.css'

interface CreateExerciseModalProps {
  open: boolean
  categories: ExerciseCategory[]
  onClose: () => void
  onCreated: () => void
}

const ACCEPT = 'video/mp4,application/pdf,.mp4,.pdf'
const MAX_FILE_BYTES = 80 * 1024 * 1024

function guessMediaType(file: File): MediaType | null {
  const name = file.name.toLowerCase()
  if (file.type === 'application/pdf' || name.endsWith('.pdf')) {
    return 'PDF'
  }
  if (file.type === 'video/mp4' || name.endsWith('.mp4')) {
    return 'VIDEO'
  }
  return null
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function mediaLabel(type: MediaType): string {
  return type === 'VIDEO' ? 'Wideo MP4' : 'Dokument PDF'
}

export function CreateExerciseModal({
  open,
  categories,
  onClose,
  onCreated,
}: CreateExerciseModalProps) {
  const fileInputId = useId()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [title, setTitle] = useState('')
  const [instruction, setInstruction] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [mediaType, setMediaType] = useState<MediaType | null>(null)
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])
  const [dragActive, setDragActive] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [fileError, setFileError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) {
      return
    }
    setTitle('')
    setInstruction('')
    setFile(null)
    setMediaType(null)
    setSelectedCategories([])
    setDragActive(false)
    setBusy(false)
    setError(null)
    setFileError(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }, [open])

  function applyFile(next: File | null) {
    setFileError(null)
    if (!next) {
      setFile(null)
      setMediaType(null)
      return
    }
    const type = guessMediaType(next)
    if (!type) {
      setFile(null)
      setMediaType(null)
      setFileError('Obsługiwane są tylko pliki MP4 i PDF.')
      return
    }
    if (next.size > MAX_FILE_BYTES) {
      setFile(null)
      setMediaType(null)
      setFileError('Plik jest za duży — maksymalnie 80 MB.')
      return
    }
    setFile(next)
    setMediaType(type)
  }

  function toggleCategory(id: string) {
    setSelectedCategories((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id],
    )
  }

  function onDragOver(event: DragEvent) {
    event.preventDefault()
    event.stopPropagation()
    setDragActive(true)
  }

  function onDragLeave(event: DragEvent) {
    event.preventDefault()
    event.stopPropagation()
    setDragActive(false)
  }

  function onDrop(event: DragEvent) {
    event.preventDefault()
    event.stopPropagation()
    setDragActive(false)
    const dropped = event.dataTransfer.files?.[0] ?? null
    applyFile(dropped)
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (!file || !mediaType) {
      setFileError('Dodaj plik MP4 lub PDF z instrukcją dla pacjenta.')
      return
    }
    if (!title.trim()) {
      setError('Podaj tytuł ćwiczenia.')
      return
    }

    setBusy(true)
    setError(null)
    try {
      const form = new FormData()
      form.append('title', title.trim())
      form.append('instruction', instruction.trim())
      form.append('media_type', mediaType)
      form.append('file', file)
      for (const categoryId of selectedCategories) {
        form.append('categories', categoryId)
      }
      await exercisesApi.create(form)
      onCreated()
      onClose()
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się dodać ćwiczenia.'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal
      open={open}
      size="lg"
      title="Nowe ćwiczenie"
      description="Opisz ruch jasnym językiem i dołącz wideo lub PDF — pacjent zobaczy to w aplikacji."
      onClose={onClose}
    >
      <form className="ex-create" onSubmit={(e) => void onSubmit(e)}>
        <section className="ex-create__section" aria-labelledby="ex-create-desc">
          <div className="ex-create__section-head">
            <h3 id="ex-create-desc">Opis</h3>
            <p>Tytuł i instrukcja, które pacjent przeczyta przed wykonaniem.</p>
          </div>

          <Field
            label="Tytuł"
            name="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="np. Mostek biodrowy — wersja podstawowa"
            required
            autoFocus
          />

          <label className="ui-field" htmlFor="ex-instruction">
            <span className="ui-field__label">Instrukcja dla pacjenta</span>
            <textarea
              id="ex-instruction"
              className="ex-create__textarea"
              value={instruction}
              onChange={(e) => setInstruction(e.target.value)}
              rows={5}
              placeholder={
                'Krok po kroku: pozycja wyjściowa, ruch, tempo, oddech, na co uważać…'
              }
            />
            <span className="ui-field__hint">
              Krótko i konkretnie — pacjent czyta to na telefonie przed ćwiczeniem.
            </span>
          </label>
        </section>

        <section className="ex-create__section" aria-labelledby="ex-create-media">
          <div className="ex-create__section-head">
            <h3 id="ex-create-media">Materiał</h3>
            <p>Wideo demonstracyjne (MP4) albo karta PDF.</p>
          </div>

          <input
            ref={fileInputRef}
            id={fileInputId}
            className="sr-only"
            type="file"
            accept={ACCEPT}
            onChange={(e) => applyFile(e.target.files?.[0] ?? null)}
          />

          {!file ? (
            <label
              htmlFor={fileInputId}
              className={`ex-create__drop${dragActive ? ' ex-create__drop--active' : ''}${fileError ? ' ex-create__drop--error' : ''}`}
              onDragOver={onDragOver}
              onDragLeave={onDragLeave}
              onDrop={onDrop}
            >
              <span className="ex-create__drop-icon" aria-hidden="true">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                  <path
                    d="M12 16V4m0 0 4 4m-4-4-4 4"
                    stroke="currentColor"
                    strokeWidth="1.75"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M4 14v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4"
                    stroke="currentColor"
                    strokeWidth="1.75"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </span>
              <span className="ex-create__drop-title">Upuść plik tutaj albo wybierz z dysku</span>
              <span className="ex-create__drop-meta">MP4 lub PDF · do 80 MB</span>
            </label>
          ) : (
            <div className="ex-create__file">
              <div className={`ex-create__file-badge ex-create__file-badge--${mediaType?.toLowerCase()}`}>
                {mediaType ? mediaLabel(mediaType) : 'Plik'}
              </div>
              <div className="ex-create__file-meta">
                <p className="ex-create__file-name" title={file.name}>
                  {file.name}
                </p>
                <p className="ex-create__file-size">{formatBytes(file.size)}</p>
              </div>
              <div className="ex-create__file-actions">
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  onClick={() => fileInputRef.current?.click()}
                >
                  Zmień
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  onClick={() => {
                    applyFile(null)
                    if (fileInputRef.current) {
                      fileInputRef.current.value = ''
                    }
                  }}
                >
                  Usuń
                </Button>
              </div>
            </div>
          )}

          {fileError ? (
            <p className="ex-create__field-error" role="alert">
              {fileError}
            </p>
          ) : null}
        </section>

        {categories.length > 0 ? (
          <section className="ex-create__section" aria-labelledby="ex-create-cats">
            <div className="ex-create__section-head">
              <h3 id="ex-create-cats">Kategorie</h3>
              <p>Opcjonalnie — ułatwia filtrowanie w katalogu.</p>
            </div>
            <div className="ex-create__chips" role="group" aria-label="Kategorie ćwiczenia">
              {categories.map((category) => {
                const selected = selectedCategories.includes(category.id)
                return (
                  <button
                    key={category.id}
                    type="button"
                    className={`ex-create__chip${selected ? ' ex-create__chip--selected' : ''}`}
                    aria-pressed={selected}
                    onClick={() => toggleCategory(category.id)}
                  >
                    {category.name}
                  </button>
                )
              })}
            </div>
          </section>
        ) : null}

        {error ? (
          <p className="ui-modal__error" role="alert">
            {error}
          </p>
        ) : null}

        <div className="ui-modal__actions ex-create__actions">
          <Button type="button" variant="secondary" onClick={onClose} disabled={busy}>
            Anuluj
          </Button>
          <Button type="submit" loading={busy}>
            Zapisz ćwiczenie
          </Button>
        </div>
      </form>
    </Modal>
  )
}
