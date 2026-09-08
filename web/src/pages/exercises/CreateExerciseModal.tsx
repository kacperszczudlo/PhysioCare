import { useEffect, useId, useMemo, useRef, useState, type DragEvent, type FormEvent } from 'react'

import { exercisesApi } from '@/api/exercises'
import { getErrorMessage } from '@/api/client'
import type { CategoryKind, Exercise, ExerciseCategory, MediaType } from '@/api/types'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import { Modal } from '@/components/ui/Modal'
import { getExerciseTitleError } from '@/lib/fieldPolicy'
import './CreateExerciseModal.css'

interface CreateExerciseModalProps {
  open: boolean
  categories: ExerciseCategory[]
  exercise?: Exercise | null
  onClose: () => void
  onSaved: () => void
}

const ACCEPT = 'video/mp4,application/pdf,.mp4,.pdf'
const MAX_FILE_BYTES = 80 * 1024 * 1024

const KIND_ORDER: CategoryKind[] = ['TYPE', 'REGION', 'MUSCLE', 'INJURY']

const KIND_SECTION_LABELS: Record<CategoryKind, { title: string; hint: string }> = {
  TYPE: {
    title: 'Typ ćwiczenia',
    hint: 'Cel interwencji - np. wzmacnianie, mobilizacja, edukacja.',
  },
  REGION: {
    title: 'Okolica ciała',
    hint: 'Główny region anatomiczny.',
  },
  MUSCLE: {
    title: 'Mięsień / grupa',
    hint: 'Docelowa grupa mięśniowa (opcjonalnie).',
  },
  INJURY: {
    title: 'Kontuzja / wskazanie',
    hint: 'Typowe wskazanie kliniczne (opcjonalnie).',
  },
}

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

function fileNameFromUrl(url: string): string {
  const cleaned = url.split('?')[0] ?? url
  const parts = cleaned.split('/')
  return parts[parts.length - 1] || 'obecny-plik'
}

export function CreateExerciseModal({
  open,
  categories,
  exercise = null,
  onClose,
  onSaved,
}: CreateExerciseModalProps) {
  const isEdit = exercise !== null
  const fileInputId = useId()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [title, setTitle] = useState('')
  const [instruction, setInstruction] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [mediaType, setMediaType] = useState<MediaType | null>(null)
  const [keepExistingFile, setKeepExistingFile] = useState(false)
  const [existingFileName, setExistingFileName] = useState('')
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])
  const [dragActive, setDragActive] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [fileError, setFileError] = useState<string | null>(null)

  const groupedCategories = useMemo(() => {
    const groups: Record<CategoryKind, ExerciseCategory[]> = {
      TYPE: [],
      REGION: [],
      MUSCLE: [],
      INJURY: [],
    }
    for (const category of categories) {
      groups[category.kind]?.push(category)
    }
    return groups
  }, [categories])

  useEffect(() => {
    if (!open) {
      return
    }
    setDragActive(false)
    setBusy(false)
    setError(null)
    setFileError(null)
    setFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }

    if (exercise) {
      setTitle(exercise.title)
      setInstruction(exercise.instruction ?? '')
      setMediaType(exercise.media_type)
      setKeepExistingFile(true)
      setExistingFileName(fileNameFromUrl(exercise.file_url))
      setSelectedCategories(exercise.categories.map((item) => item.id))
    } else {
      setTitle('')
      setInstruction('')
      setMediaType(null)
      setKeepExistingFile(false)
      setExistingFileName('')
      setSelectedCategories([])
    }
  }, [open, exercise])

  function applyFile(next: File | null) {
    setFileError(null)
    if (!next) {
      setFile(null)
      if (isEdit && exercise) {
        setKeepExistingFile(true)
        setMediaType(exercise.media_type)
        setExistingFileName(fileNameFromUrl(exercise.file_url))
      } else {
        setMediaType(null)
        setKeepExistingFile(false)
      }
      return
    }
    const type = guessMediaType(next)
    if (!type) {
      setFile(null)
      setFileError('Obsługiwane są tylko pliki MP4 i PDF.')
      return
    }
    if (next.size > MAX_FILE_BYTES) {
      setFile(null)
      setFileError('Plik jest za duży - maksymalnie 80 MB.')
      return
    }
    setFile(next)
    setMediaType(type)
    setKeepExistingFile(false)
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
    const titleError = getExerciseTitleError(title)
    if (titleError) {
      setError(titleError)
      return
    }
    if (!isEdit && (!file || !mediaType)) {
      setFileError('Dodaj plik MP4 lub PDF z instrukcją dla pacjenta.')
      return
    }
    if (isEdit && !file && !keepExistingFile) {
      setFileError('Dodaj plik MP4 lub PDF albo przywróć obecny materiał.')
      return
    }
    if (!mediaType) {
      setFileError('Nie rozpoznano typu materiału.')
      return
    }

    setBusy(true)
    setError(null)
    try {
      const form = new FormData()
      form.append('title', title.trim())
      form.append('instruction', instruction.trim())
      form.append('media_type', mediaType)
      form.append('has_categories', '1')
      for (const categoryId of selectedCategories) {
        form.append('categories', categoryId)
      }
      if (file) {
        form.append('file', file)
      }

      if (isEdit && exercise) {
        await exercisesApi.update(exercise.id, form)
      } else {
        await exercisesApi.create(form)
      }
      onSaved()
      onClose()
    } catch (err) {
      setError(
        getErrorMessage(
          err,
          isEdit ? 'Nie udało się zapisać ćwiczenia.' : 'Nie udało się dodać ćwiczenia.',
        ),
      )
    } finally {
      setBusy(false)
    }
  }

  const showDropzone = !file && !keepExistingFile
  const showFileCard = Boolean(file) || keepExistingFile

  return (
    <Modal
      open={open}
      size="lg"
      title={isEdit ? 'Edytuj ćwiczenie' : 'Nowe ćwiczenie'}
      description={
        isEdit
          ? 'Zmień opis, kategorie albo podmień materiał - pacjenci zobaczą aktualną wersję.'
          : 'Opisz ruch jasnym językiem i dołącz wideo lub PDF - pacjent zobaczy to w aplikacji.'
      }
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
            placeholder="np. Mostek biodrowy - wersja podstawowa"
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
              placeholder={'Krok po kroku: pozycja wyjściowa, ruch, tempo, oddech, na co uważać…'}
            />
            <span className="ui-field__hint">
              Krótko i konkretnie - pacjent czyta to na telefonie przed ćwiczeniem.
            </span>
          </label>
        </section>

        <section className="ex-create__section" aria-labelledby="ex-create-media">
          <div className="ex-create__section-head">
            <h3 id="ex-create-media">Materiał</h3>
            <p>
              {isEdit
                ? 'Zostaw obecny plik albo wgraj nowy MP4 / PDF.'
                : 'Wideo demonstracyjne (MP4) albo karta PDF.'}
            </p>
          </div>

          <input
            ref={fileInputRef}
            id={fileInputId}
            className="sr-only"
            type="file"
            accept={ACCEPT}
            onChange={(e) => applyFile(e.target.files?.[0] ?? null)}
          />

          {showDropzone ? (
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
          ) : null}

          {showFileCard ? (
            <div className="ex-create__file">
              <div
                className={`ex-create__file-badge ex-create__file-badge--${mediaType?.toLowerCase()}`}
              >
                {mediaType ? mediaLabel(mediaType) : 'Plik'}
              </div>
              <div className="ex-create__file-meta">
                <p className="ex-create__file-name" title={file?.name ?? existingFileName}>
                  {file ? file.name : existingFileName}
                </p>
                <p className="ex-create__file-size">
                  {file ? formatBytes(file.size) : keepExistingFile ? 'Obecny materiał' : ''}
                </p>
              </div>
              <div className="ex-create__file-actions">
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  onClick={() => fileInputRef.current?.click()}
                >
                  {keepExistingFile && !file ? 'Podmień' : 'Zmień'}
                </Button>
                {file ? (
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
                    {isEdit ? 'Przywróć' : 'Usuń'}
                  </Button>
                ) : null}
              </div>
            </div>
          ) : null}

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
              <p>
                Oznacz typ, okolicę, mięsień i ewentualne wskazanie - ułatwia filtrowanie w
                katalogu.
              </p>
            </div>
            {KIND_ORDER.map((kind) => {
              const list = groupedCategories[kind]
              if (!list.length) {
                return null
              }
              const meta = KIND_SECTION_LABELS[kind]
              return (
                <div key={kind} className="ex-create__cat-group">
                  <div className="ex-create__cat-group-head">
                    <h4>{meta.title}</h4>
                    <p>{meta.hint}</p>
                  </div>
                  <div className="ex-create__chips" role="group" aria-label={meta.title}>
                    {list.map((category) => {
                      const selected = selectedCategories.includes(category.id)
                      return (
                        <button
                          key={category.id}
                          type="button"
                          className={`ex-create__chip ex-create__chip--${kind.toLowerCase()}${
                            selected ? ' ex-create__chip--selected' : ''
                          }`}
                          aria-pressed={selected}
                          onClick={() => toggleCategory(category.id)}
                        >
                          {category.name}
                        </button>
                      )
                    })}
                  </div>
                </div>
              )
            })}
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
            {isEdit ? 'Zapisz zmiany' : 'Zapisz ćwiczenie'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
