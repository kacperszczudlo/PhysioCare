import { useEffect, useState } from 'react'

import { exercisesApi } from '@/api/exercises'
import { getErrorMessage } from '@/api/client'
import type { Exercise, ExerciseCategory, MediaType } from '@/api/types'
import { EmptyState, ErrorBanner, LoadingBlock } from '@/components/AsyncState'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import { AssignExerciseModal } from '@/pages/exercises/AssignExerciseModal'
import { CreateExerciseModal } from '@/pages/exercises/CreateExerciseModal'
import { DeleteExerciseModal } from '@/pages/exercises/DeleteExerciseModal'
import './ExercisesPage.css'

function mediaLabel(type: MediaType): string {
  return type === 'VIDEO' ? 'Wideo' : 'PDF'
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
  const [assignTarget, setAssignTarget] = useState<Exercise | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<Exercise | null>(null)

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

  return (
    <section className="exercises-page">
      <PageHeader
        title="Baza ćwiczeń"
        description="Katalog wideo i PDF — filtruj, dodawaj i wysyłaj pacjentom do aplikacji."
        actions={
          <Button type="button" onClick={() => setCreateOpen(true)}>
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
          placeholder="Tytuł lub fragment instrukcji…"
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
          description="Dodaj pierwsze ćwiczenie z krótką instrukcją i plikiem MP4 lub PDF — pacjent zobaczy je w aplikacji."
          action={
            <Button type="button" size="sm" onClick={() => setCreateOpen(true)}>
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
                <span
                  className={`exercises-card__type exercises-card__type--${exercise.media_type.toLowerCase()}`}
                >
                  {mediaLabel(exercise.media_type)}
                </span>
                <h2 className="exercises-card__title">{exercise.title}</h2>
              </div>
              {exercise.instruction ? (
                <p className="exercises-card__instruction">{exercise.instruction}</p>
              ) : (
                <p className="exercises-card__instruction exercises-card__instruction--empty">
                  Bez instrukcji tekstowej
                </p>
              )}
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
                <div className="exercises-card__buttons">
                  <Button type="button" size="sm" variant="ghost" onClick={() => setDeleteTarget(exercise)}>
                    Usuń
                  </Button>
                  <Button type="button" size="sm" onClick={() => setAssignTarget(exercise)}>
                    Przypisz
                  </Button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      ) : null}

      <CreateExerciseModal
        open={createOpen}
        categories={categories}
        onClose={() => setCreateOpen(false)}
        onCreated={() => setReloadToken((value) => value + 1)}
      />

      <DeleteExerciseModal
        open={deleteTarget !== null}
        exercise={deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onDeleted={() => setReloadToken((value) => value + 1)}
      />

      <AssignExerciseModal
        open={assignTarget !== null}
        exercise={assignTarget}
        onClose={() => setAssignTarget(null)}
        onAssigned={() => undefined}
      />
    </section>
  )
}
