import { useEffect, useMemo, useState, type FormEvent } from 'react'

import { exercisesApi } from '@/api/exercises'
import { getErrorMessage } from '@/api/client'
import type { Exercise, ExerciseCategory, MediaType } from '@/api/types'
import { EmptyState, ErrorBanner, LoadingBlock } from '@/components/AsyncState'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import { Modal } from '@/components/ui/Modal'
import { AssignExerciseModal } from '@/pages/exercises/AssignExerciseModal'
import './ExercisesPage.css'

function mediaLabel(type: MediaType): string {
  return type === 'VIDEO' ? 'Wideo' : 'PDF'
}

function guessMediaType(file: File | null): MediaType {
  if (!file) {
    return 'VIDEO'
  }
  if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
    return 'PDF'
  }
  return 'VIDEO'
}

export function ExercisesPage() {
  const [exercises, setExercises] = useState<Exercise[]>([])
  const [categories, setCategories] = useState<ExerciseCategory[]>([])
  const [categoryFilter, setCategoryFilter] = useState('')
  const [mediaFilter, setMediaFilter] = useState<MediaType | ''>('')
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reloadToken, setReloadToken] = useState(0)

  const [createOpen, setCreateOpen] = useState(false)
  const [title, setTitle] = useState('')
  const [instruction, setInstruction] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])
  const [createBusy, setCreateBusy] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)

  const [assignTarget, setAssignTarget] = useState<Exercise | null>(null)

  useEffect(() => {
    let cancelled = false
    async function loadCategories() {
      try {
        const data = await exercisesApi.listCategories()
        if (!cancelled) {
          setCategories(data)
        }
      } catch {
        if (!cancelled) {
          setCategories([])
        }
      }
    }
    void loadCategories()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const data = await exercisesApi.list({
          category: categoryFilter || undefined,
          media_type: mediaFilter || undefined,
          q: query || undefined,
        })
        if (!cancelled) {
          setExercises(data)
        }
      } catch (err) {
        if (!cancelled) {
          setError(getErrorMessage(err, 'Nie udało się pobrać ćwiczeń.'))
          setExercises([])
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
  }, [categoryFilter, mediaFilter, query, reloadToken])

  const selectedCategoryNames = useMemo(() => {
    const map = new Map(categories.map((item) => [item.id, item.name]))
    return selectedCategories.map((id) => map.get(id) ?? id)
  }, [categories, selectedCategories])

  function toggleCategory(id: string) {
    setSelectedCategories((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id],
    )
  }

  function openCreate() {
    setTitle('')
    setInstruction('')
    setFile(null)
    setSelectedCategories([])
    setCreateError(null)
    setCreateOpen(true)
  }

  async function onCreate(event: FormEvent) {
    event.preventDefault()
    if (!file) {
      setCreateError('Dodaj plik MP4 lub PDF.')
      return
    }
    setCreateBusy(true)
    setCreateError(null)
    try {
      const form = new FormData()
      form.append('title', title.trim())
      form.append('instruction', instruction.trim())
      form.append('media_type', guessMediaType(file))
      form.append('file', file)
      for (const categoryId of selectedCategories) {
        form.append('categories', categoryId)
      }
      await exercisesApi.create(form)
      setCreateOpen(false)
      setReloadToken((value) => value + 1)
    } catch (err) {
      setCreateError(getErrorMessage(err, 'Nie udało się dodać ćwiczenia.'))
    } finally {
      setCreateBusy(false)
    }
  }

  return (
    <section className="exercises-page">
      <PageHeader
        title="Baza ćwiczeń"
        description="Katalog wideo i PDF — filtruj, dodawaj i wysyłaj pacjentom do aplikacji."
        actions={
          <Button type="button" onClick={openCreate}>
            + Dodaj ćwiczenie
          </Button>
        }
      />

      <div className="exercises-filters">
        <Field
          label="Szukaj"
          name="q"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Tytuł…"
        />
        <label className="ui-field">
          <span className="ui-field__label">Kategoria</span>
          <select
            className="exercises-select"
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
          >
            <option value="">Wszystkie</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </label>
        <label className="ui-field">
          <span className="ui-field__label">Typ pliku</span>
          <select
            className="exercises-select"
            value={mediaFilter}
            onChange={(e) => setMediaFilter(e.target.value as MediaType | '')}
          >
            <option value="">Wszystkie</option>
            <option value="VIDEO">Wideo</option>
            <option value="PDF">PDF</option>
          </select>
        </label>
      </div>

      {error ? (
        <ErrorBanner message={error} onRetry={() => setReloadToken((value) => value + 1)} />
      ) : null}

      {loading ? <LoadingBlock label="Ładowanie katalogu…" /> : null}

      {!loading && !error && exercises.length === 0 ? (
        <EmptyState
          title="Brak ćwiczeń"
          description="Nie znaleziono pozycji dla aktywnych filtrów. Dodaj ćwiczenie z plikiem MP4 lub PDF."
          action={
            <Button type="button" size="sm" onClick={openCreate}>
              + Dodaj ćwiczenie
            </Button>
          }
        />
      ) : null}

      {!loading && !error && exercises.length > 0 ? (
        <ul className="exercises-grid">
          {exercises.map((exercise) => (
            <li key={exercise.id} className="exercises-card">
              <div className="exercises-card__top">
                <span className="exercises-card__type">{mediaLabel(exercise.media_type)}</span>
                <h2 className="exercises-card__title">{exercise.title}</h2>
              </div>
              {exercise.instruction ? (
                <p className="exercises-card__instruction">{exercise.instruction}</p>
              ) : null}
              {exercise.categories.length > 0 ? (
                <ul className="exercises-card__tags">
                  {exercise.categories.map((category) => (
                    <li key={category.id}>{category.name}</li>
                  ))}
                </ul>
              ) : null}
              <div className="exercises-card__actions">
                <a
                  className="exercises-card__link"
                  href={exercise.file_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  Podgląd pliku
                </a>
                <Button type="button" size="sm" onClick={() => setAssignTarget(exercise)}>
                  Przypisz
                </Button>
              </div>
            </li>
          ))}
        </ul>
      ) : null}

      <Modal open={createOpen} title="Nowe ćwiczenie" onClose={() => setCreateOpen(false)}>
        <form className="ui-modal__form" onSubmit={(e) => void onCreate(e)}>
          <Field
            label="Tytuł"
            name="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />
          <label className="ui-field">
            <span className="ui-field__label">Instrukcja</span>
            <textarea
              className="ui-modal__textarea"
              value={instruction}
              onChange={(e) => setInstruction(e.target.value)}
              rows={3}
            />
          </label>
          <label className="ui-field">
            <span className="ui-field__label">Plik (MP4 lub PDF)</span>
            <input
              type="file"
              accept="video/mp4,application/pdf,.mp4,.pdf"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              required
            />
          </label>
          {categories.length > 0 ? (
            <fieldset className="exercises-cats">
              <legend>Kategorie</legend>
              <div className="exercises-cats__list">
                {categories.map((category) => (
                  <label key={category.id} className="exercises-cats__item">
                    <input
                      type="checkbox"
                      checked={selectedCategories.includes(category.id)}
                      onChange={() => toggleCategory(category.id)}
                    />
                    {category.name}
                  </label>
                ))}
              </div>
              {selectedCategoryNames.length > 0 ? (
                <p className="exercises-muted">Wybrane: {selectedCategoryNames.join(', ')}</p>
              ) : null}
            </fieldset>
          ) : null}
          {createError ? (
            <p className="ui-modal__error" role="alert">
              {createError}
            </p>
          ) : null}
          <div className="ui-modal__actions">
            <Button type="button" variant="secondary" onClick={() => setCreateOpen(false)}>
              Anuluj
            </Button>
            <Button type="submit" loading={createBusy}>
              Zapisz
            </Button>
          </div>
        </form>
      </Modal>

      <AssignExerciseModal
        open={assignTarget !== null}
        exercise={assignTarget}
        onClose={() => setAssignTarget(null)}
        onAssigned={() => undefined}
      />
    </section>
  )
}
