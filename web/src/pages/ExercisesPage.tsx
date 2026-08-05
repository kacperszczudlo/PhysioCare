import { useEffect, useMemo, useState } from 'react'

import { exercisesApi } from '@/api/exercises'
import { getErrorMessage } from '@/api/client'
import type { CategoryKind, Exercise, ExerciseCategory, MediaType } from '@/api/types'
import { EmptyState, ErrorBanner, LoadingBlock } from '@/components/AsyncState'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import { AssignExerciseModal } from '@/pages/exercises/AssignExerciseModal'
import { CreateExerciseModal } from '@/pages/exercises/CreateExerciseModal'
import { DeleteExerciseModal } from '@/pages/exercises/DeleteExerciseModal'
import { resolveMediaUrl } from '@/lib/mediaUrl'
import './ExercisesPage.css'

const KIND_ORDER: CategoryKind[] = ['TYPE', 'REGION', 'MUSCLE', 'INJURY']

const KIND_LABELS: Record<CategoryKind, string> = {
  TYPE: 'Typ',
  REGION: 'Okolica',
  MUSCLE: 'Mięsień',
  INJURY: 'Kontuzja',
}

function mediaLabel(type: MediaType): string {
  return type === 'VIDEO' ? 'Wideo' : 'PDF'
}

function groupByKind(categories: ExerciseCategory[]): Record<CategoryKind, ExerciseCategory[]> {
  const groups = {
    TYPE: [] as ExerciseCategory[],
    REGION: [] as ExerciseCategory[],
    MUSCLE: [] as ExerciseCategory[],
    INJURY: [] as ExerciseCategory[],
  }
  for (const category of categories) {
    groups[category.kind]?.push(category)
  }
  return groups
}

export function ExercisesPage() {
  const [exercises, setExercises] = useState<Exercise[]>([])
  const [categories, setCategories] = useState<ExerciseCategory[]>([])
  const [typeFilter, setTypeFilter] = useState('')
  const [regionFilter, setRegionFilter] = useState('')
  const [muscleFilter, setMuscleFilter] = useState('')
  const [injuryFilter, setInjuryFilter] = useState('')
  const [mediaFilter, setMediaFilter] = useState<MediaType | ''>('')
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reloadToken, setReloadToken] = useState(0)

  const [createOpen, setCreateOpen] = useState(false)
  const [editTarget, setEditTarget] = useState<Exercise | null>(null)
  const [assignTarget, setAssignTarget] = useState<Exercise | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<Exercise | null>(null)

  const grouped = useMemo(() => groupByKind(categories), [categories])

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
          type: typeFilter || undefined,
          region: regionFilter || undefined,
          muscle: muscleFilter || undefined,
          injury: injuryFilter || undefined,
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
  }, [typeFilter, regionFilter, muscleFilter, injuryFilter, mediaFilter, query, reloadToken])

  return (
    <section className="exercises-page">
      <PageHeader
        title="Baza ćwiczeń"
        description="Katalog wideo i PDF — filtruj po typie, okolicy, mięśniu i kontuzji, potem wysyłaj pacjentom."
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
          <span className="ui-field__label">Typ ćwiczenia</span>
          <select
            className="exercises-select"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          >
            <option value="">Wszystkie</option>
            {grouped.TYPE.map((category) => (
              <option key={category.id} value={category.slug}>
                {category.name}
              </option>
            ))}
          </select>
        </label>
        <label className="ui-field">
          <span className="ui-field__label">Okolica</span>
          <select
            className="exercises-select"
            value={regionFilter}
            onChange={(e) => setRegionFilter(e.target.value)}
          >
            <option value="">Wszystkie</option>
            {grouped.REGION.map((category) => (
              <option key={category.id} value={category.slug}>
                {category.name}
              </option>
            ))}
          </select>
        </label>
        <label className="ui-field">
          <span className="ui-field__label">Mięsień</span>
          <select
            className="exercises-select"
            value={muscleFilter}
            onChange={(e) => setMuscleFilter(e.target.value)}
          >
            <option value="">Wszystkie</option>
            {grouped.MUSCLE.map((category) => (
              <option key={category.id} value={category.slug}>
                {category.name}
              </option>
            ))}
          </select>
        </label>
        <label className="ui-field">
          <span className="ui-field__label">Kontuzja</span>
          <select
            className="exercises-select"
            value={injuryFilter}
            onChange={(e) => setInjuryFilter(e.target.value)}
          >
            <option value="">Wszystkie</option>
            {grouped.INJURY.map((category) => (
              <option key={category.id} value={category.slug}>
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
        />
      ) : null}

      {!loading && !error && exercises.length > 0 ? (
        <ul className="exercises-grid">
          {exercises.map((exercise) => {
            const mediaUrl = resolveMediaUrl(exercise.file_url)
            return (
              <li key={exercise.id} className="exercises-card">
                <div className="exercises-card__media">
                  {mediaUrl && exercise.media_type === 'VIDEO' ? (
                    <video
                      className="exercises-card__player"
                      src={mediaUrl}
                      controls
                      preload="metadata"
                      playsInline
                    />
                  ) : null}
                  {mediaUrl && exercise.media_type === 'PDF' ? (
                    <a
                      className="exercises-card__pdf"
                      href={mediaUrl}
                      target="_blank"
                      rel="noreferrer"
                    >
                      <span className="exercises-card__type exercises-card__type--pdf">PDF</span>
                      <span>Otwórz dokument</span>
                    </a>
                  ) : null}
                </div>
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
                    {KIND_ORDER.flatMap((kind) =>
                      exercise.categories
                        .filter((category) => category.kind === kind)
                        .map((category) => (
                          <li
                            key={category.id}
                            className={`exercises-card__tag exercises-card__tag--${kind.toLowerCase()}`}
                            title={KIND_LABELS[kind]}
                          >
                            {category.name}
                          </li>
                        )),
                    )}
                  </ul>
                ) : null}
                <div className="exercises-card__actions">
                  <div className="exercises-card__buttons">
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      onClick={() => setDeleteTarget(exercise)}
                    >
                      Usuń
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="secondary"
                      onClick={() => setEditTarget(exercise)}
                    >
                      Edytuj
                    </Button>
                    <Button type="button" size="sm" onClick={() => setAssignTarget(exercise)}>
                      Przypisz
                    </Button>
                  </div>
                </div>
              </li>
            )
          })}
        </ul>
      ) : null}

      <CreateExerciseModal
        open={createOpen || editTarget !== null}
        categories={categories}
        exercise={editTarget}
        onClose={() => {
          setCreateOpen(false)
          setEditTarget(null)
        }}
        onSaved={() => setReloadToken((value) => value + 1)}
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
