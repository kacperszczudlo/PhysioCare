import { useEffect, useMemo, useState, type ChangeEvent } from 'react'

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
import { AuthMediaPdfLink, AuthMediaVideo } from '@/components/AuthMedia'
import './ExercisesPage.css'

const KIND_ORDER: CategoryKind[] = ['TYPE', 'REGION', 'MUSCLE', 'INJURY']
const PAGE_SIZE = 20

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
  const [totalCount, setTotalCount] = useState(0)
  const [page, setPage] = useState(1)
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
  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE))
  const rangeStart = totalCount === 0 ? 0 : (page - 1) * PAGE_SIZE + 1
  const rangeEnd = Math.min(page * PAGE_SIZE, totalCount)

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
    setPage(1)
  }, [typeFilter, regionFilter, muscleFilter, injuryFilter, mediaFilter, query])

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
          page,
        })
        if (!cancelled) {
          setExercises(data.results)
          setTotalCount(data.count)
        }
      } catch (err) {
        if (!cancelled) {
          setError(getErrorMessage(err, 'Nie udało się pobrać ćwiczeń.'))
          setExercises([])
          setTotalCount(0)
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
  }, [typeFilter, regionFilter, muscleFilter, injuryFilter, mediaFilter, query, page, reloadToken])

  function onFilterChange(setter: (value: string) => void) {
    return (e: ChangeEvent<HTMLSelectElement | HTMLInputElement>) => {
      setter(e.target.value)
    }
  }

  const hasActiveFilters = Boolean(
    query || typeFilter || regionFilter || muscleFilter || injuryFilter || mediaFilter,
  )

  function clearFilters() {
    setQuery('')
    setTypeFilter('')
    setRegionFilter('')
    setMuscleFilter('')
    setInjuryFilter('')
    setMediaFilter('')
  }

  return (
    <section className="exercises-page">
      <PageHeader
        title="Baza ćwiczeń"
        description="Katalog wideo i PDF - filtruj, potem wysyłaj pacjentom."
        actions={
          <Button type="button" onClick={() => setCreateOpen(true)}>
            + Dodaj ćwiczenie
          </Button>
        }
      />

      <div className="exercises-toolbar">
        <div className="exercises-toolbar__primary">
          <Field
            className="exercises-toolbar__search"
            label="Szukaj"
            name="q"
            value={query}
            onChange={onFilterChange(setQuery)}
            placeholder="Tytuł lub fragment instrukcji…"
            autoComplete="off"
          />
          <div className="exercises-media" role="group" aria-label="Typ pliku">
            <span className="exercises-media__label" id="exercises-media-label">
              Typ pliku
            </span>
            <div className="exercises-media__options" aria-labelledby="exercises-media-label">
              {(
                [
                  { value: '', label: 'Wszystkie' },
                  { value: 'VIDEO', label: 'Wideo' },
                  { value: 'PDF', label: 'PDF' },
                ] as const
              ).map((option) => {
                const selected = mediaFilter === option.value
                return (
                  <button
                    key={option.label}
                    type="button"
                    className={
                      selected
                        ? 'exercises-media__btn exercises-media__btn--active'
                        : 'exercises-media__btn'
                    }
                    aria-pressed={selected}
                    onClick={() => setMediaFilter(option.value)}
                  >
                    {option.label}
                  </button>
                )
              })}
            </div>
          </div>
        </div>

        <div className="exercises-toolbar__filters" role="group" aria-label="Filtry kategorii">
          <label className="ui-field">
            <span className="ui-field__label">Typ</span>
            <select
              className="exercises-select"
              value={typeFilter}
              onChange={onFilterChange(setTypeFilter)}
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
              onChange={onFilterChange(setRegionFilter)}
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
              onChange={onFilterChange(setMuscleFilter)}
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
              onChange={onFilterChange(setInjuryFilter)}
            >
              <option value="">Wszystkie</option>
              {grouped.INJURY.map((category) => (
                <option key={category.id} value={category.slug}>
                  {category.name}
                </option>
              ))}
            </select>
          </label>
          {hasActiveFilters ? (
            <div className="exercises-toolbar__clear">
              <Button type="button" size="sm" variant="ghost" onClick={clearFilters}>
                Wyczyść
              </Button>
            </div>
          ) : null}
        </div>
      </div>

      {error ? (
        <ErrorBanner message={error} onRetry={() => setReloadToken((value) => value + 1)} />
      ) : null}

      {loading ? <LoadingBlock label="Ładowanie katalogu…" /> : null}

      {!loading && !error && exercises.length === 0 ? (
        <EmptyState
          title="Brak ćwiczeń"
          description="Dodaj pierwsze ćwiczenie z krótką instrukcją i plikiem MP4 lub PDF - pacjent zobaczy je w aplikacji."
        />
      ) : null}

      {!loading && !error && exercises.length > 0 ? (
        <>
          <ul className="exercises-grid">
            {exercises.map((exercise) => {
              return (
                <li key={exercise.id} className="exercises-card">
                  <div className="exercises-card__media">
                    {exercise.media_type === 'VIDEO' ? (
                      <AuthMediaVideo path={exercise.file_url} className="exercises-card__player" />
                    ) : null}
                    {exercise.media_type === 'PDF' ? (
                      <AuthMediaPdfLink path={exercise.file_url} className="exercises-card__pdf">
                        <span className="exercises-card__type exercises-card__type--pdf">PDF</span>
                        <span>Otwórz dokument</span>
                      </AuthMediaPdfLink>
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

          <div className="exercises-pagination">
            <p className="exercises-pagination__meta">
              {rangeStart}-{rangeEnd} z {totalCount}
            </p>
            <div className="exercises-pagination__controls">
              <Button
                type="button"
                size="sm"
                variant="secondary"
                disabled={page <= 1 || loading}
                onClick={() => setPage((value) => Math.max(1, value - 1))}
              >
                Poprzednia
              </Button>
              <span className="exercises-pagination__page">
                Strona {page} / {totalPages}
              </span>
              <Button
                type="button"
                size="sm"
                variant="secondary"
                disabled={page >= totalPages || loading}
                onClick={() => setPage((value) => value + 1)}
              >
                Następna
              </Button>
            </div>
          </div>
        </>
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
