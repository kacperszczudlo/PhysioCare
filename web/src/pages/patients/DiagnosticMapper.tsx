import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { Body, type BodyPartData, type BodyPartSlug } from 'simple-body-highlighter-react'

import { treatmentApi } from '@/api/treatment'
import { ApiError } from '@/api/client'
import type { BodyAreaPain, BodyViewSide } from '@/api/types'
import { Button } from '@/components/ui/Button'
import {
  BODY_MODEL_COLORS,
  PAIN_CHARACTERS,
  STRUCTURE_KIND_LABELS,
  groupTargetsByKind,
  isBodyPartSlug,
  regionLabel,
  targetLabel,
  targetsForRegion,
  vasColor,
  type StructureKind,
} from '@/lib/bodyMap'
import './DiagnosticMapper.css'

interface DiagnosticMapperProps {
  episodeId: string
}

const KIND_ORDER: StructureKind[] = ['JOINT', 'MUSCLE', 'BONE', 'SOFT']

function sideToModel(side: BodyViewSide): 'front' | 'back' {
  return side === 'FRONT' ? 'front' : 'back'
}

export function DiagnosticMapper({ episodeId }: DiagnosticMapperProps) {
  const [side, setSide] = useState<BodyViewSide>('FRONT')
  const [entries, setEntries] = useState<BodyAreaPain[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null)
  const [vas, setVas] = useState(5)
  const [characters, setCharacters] = useState<string[]>([])
  const [targets, setTargets] = useState<string[]>([])
  const [kindFilter, setKindFilter] = useState<StructureKind | 'ALL'>('ALL')
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    let cancelled = false

    async function load() {
      setLoading(true)
      setError(null)
      setSelectedRegion(null)
      try {
        const data = await treatmentApi.listBodyPain(episodeId)
        if (!cancelled) {
          setEntries(data)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'Nie udało się pobrać mapy ciała.')
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
  }, [episodeId])

  const sideEntries = useMemo(
    () => entries.filter((entry) => entry.view_side === side),
    [entries, side],
  )

  const selectedEntry = useMemo(
    () => sideEntries.find((entry) => entry.body_region === selectedRegion) ?? null,
    [sideEntries, selectedRegion],
  )

  const regionTargets = useMemo(
    () => (selectedRegion ? targetsForRegion(selectedRegion) : []),
    [selectedRegion],
  )

  const groupedTargets = useMemo(() => groupTargetsByKind(regionTargets), [regionTargets])

  const highlightData = useMemo((): BodyPartData[] => {
    const bySlug = new Map<BodyPartSlug, string>()

    for (const entry of sideEntries) {
      if (!isBodyPartSlug(entry.body_region)) continue
      bySlug.set(entry.body_region, vasColor(entry.vas_score))
    }

    if (selectedRegion && isBodyPartSlug(selectedRegion)) {
      bySlug.set(selectedRegion, vasColor(vas))
    }

    return Array.from(bySlug.entries()).map(([slug, color]) => ({ slug, color }))
  }, [sideEntries, selectedRegion, vas])

  function selectRegion(regionId: string) {
    setSelectedRegion(regionId)
    setKindFilter('ALL')
    const existing = entries.find(
      (entry) => entry.body_region === regionId && entry.view_side === side,
    )
    if (existing) {
      setVas(existing.vas_score)
      setCharacters(existing.pain_character ?? [])
      setTargets(existing.treatment_targets ?? [])
    } else {
      setVas(5)
      setCharacters([])
      setTargets([])
    }
    setError(null)
  }

  function onMuscleClick(slug: BodyPartSlug) {
    selectRegion(slug)
  }

  function clearSelection() {
    setSelectedRegion(null)
    setKindFilter('ALL')
  }

  function toggleCharacter(id: string) {
    setCharacters((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id],
    )
  }

  function toggleTarget(id: string) {
    setTargets((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id],
    )
  }

  async function onSave(event: FormEvent) {
    event.preventDefault()
    if (!selectedRegion) {
      return
    }
    setSaving(true)
    setError(null)
    try {
      if (selectedEntry) {
        const updated = await treatmentApi.updateBodyPain(episodeId, selectedEntry.id, {
          vas_score: vas,
          pain_character: characters,
          treatment_targets: targets,
        })
        setEntries((prev) => prev.map((entry) => (entry.id === updated.id ? updated : entry)))
      } else {
        const created = await treatmentApi.createBodyPain(episodeId, {
          body_region: selectedRegion,
          view_side: side,
          vas_score: vas,
          pain_character: characters,
          treatment_targets: targets,
        })
        setEntries((prev) => [...prev, created])
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Nie udało się zapisać wpisu VAS.')
    } finally {
      setSaving(false)
    }
  }

  async function onDelete() {
    if (!selectedEntry) {
      return
    }
    const confirmed = window.confirm(
      `Usunąć wpis VAS dla „${regionLabel(selectedEntry.body_region, side)}”?`,
    )
    if (!confirmed) {
      return
    }
    setDeleting(true)
    setError(null)
    try {
      await treatmentApi.deleteBodyPain(episodeId, selectedEntry.id)
      setEntries((prev) => prev.filter((entry) => entry.id !== selectedEntry.id))
      clearSelection()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Nie udało się usunąć wpisu VAS.')
    } finally {
      setDeleting(false)
    }
  }

  function switchSide(next: BodyViewSide) {
    setSide(next)
    clearSelection()
  }

  return (
    <section className="diag-map" aria-label="Diagnostic Mapper">
      <header className="diag-map__header">
        <div>
          <h3>Mapa ciała (VAS)</h3>
          <p className="diag-map__subtitle">
            Kliknij mięsień / region → VAS, charakter bólu i cel leczenia
          </p>
        </div>
        <div className="diag-map__tabs" role="tablist" aria-label="Strona ciała">
          <button
            type="button"
            role="tab"
            aria-selected={side === 'FRONT'}
            className={side === 'FRONT' ? 'diag-map__tab diag-map__tab--active' : 'diag-map__tab'}
            onClick={() => switchSide('FRONT')}
          >
            Przód
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={side === 'BACK'}
            className={side === 'BACK' ? 'diag-map__tab diag-map__tab--active' : 'diag-map__tab'}
            onClick={() => switchSide('BACK')}
          >
            Tył
          </button>
        </div>
      </header>

      {loading ? <p className="diag-map__muted">Ładowanie mapy…</p> : null}
      {error ? (
        <p className="diag-map__error" role="alert">
          {error}
        </p>
      ) : null}

      <div className="diag-map__layout">
        <div className="diag-map__canvas-wrap">
          <div className="diag-map__model" aria-label={side === 'FRONT' ? 'Sylwetka — przód' : 'Sylwetka — tył'}>
            <Body
              data={highlightData}
              onClick={onMuscleClick}
              gender="male"
              side={sideToModel(side)}
              scale={1.85}
              border="none"
              defaultFill={BODY_MODEL_COLORS.defaultFill}
              hiddenParts={['hair']}
            />
          </div>
        </div>

        <div className="diag-map__panel">
          {!selectedRegion ? (
            <p className="diag-map__muted">
              Wybierz region na sylwetce anatomicznej, aby zapisać VAS i cel terapii.
            </p>
          ) : (
            <form className="diag-map__form" onSubmit={(e) => void onSave(e)}>
              <h4>{regionLabel(selectedRegion, side)}</h4>
              <p className="diag-map__hint">
                Lokalizacja bólu na modelu → precyzyjny cel (staw / mięsień / kość).
              </p>

              <label className="diag-map__vas">
                <span>
                  VAS: <strong>{vas}</strong> / 10
                </span>
                <input
                  type="range"
                  min={0}
                  max={10}
                  step={1}
                  value={vas}
                  onChange={(e) => setVas(Number(e.target.value))}
                />
              </label>

              <fieldset className="diag-map__chars">
                <legend>Charakter bólu</legend>
                <div className="diag-map__char-list">
                  {PAIN_CHARACTERS.map((item) => (
                    <label key={item.id} className="diag-map__char">
                      <input
                        type="checkbox"
                        checked={characters.includes(item.id)}
                        onChange={() => toggleCharacter(item.id)}
                      />
                      {item.label}
                    </label>
                  ))}
                </div>
              </fieldset>

              {regionTargets.length > 0 ? (
                <fieldset className="diag-map__targets">
                  <legend>Cel leczenia</legend>
                  <div className="diag-map__kind-tabs" role="tablist" aria-label="Typ struktury">
                    <button
                      type="button"
                      className={
                        kindFilter === 'ALL'
                          ? 'diag-map__kind diag-map__kind--active'
                          : 'diag-map__kind'
                      }
                      onClick={() => setKindFilter('ALL')}
                    >
                      Wszystkie
                    </button>
                    {KIND_ORDER.map((kind) =>
                      groupedTargets[kind]?.length ? (
                        <button
                          key={kind}
                          type="button"
                          className={
                            kindFilter === kind
                              ? 'diag-map__kind diag-map__kind--active'
                              : 'diag-map__kind'
                          }
                          onClick={() => setKindFilter(kind)}
                        >
                          {STRUCTURE_KIND_LABELS[kind]}
                        </button>
                      ) : null,
                    )}
                  </div>

                  <div className="diag-map__target-groups">
                    {KIND_ORDER.map((kind) => {
                      const list = groupedTargets[kind]
                      if (!list?.length) return null
                      if (kindFilter !== 'ALL' && kindFilter !== kind) return null
                      return (
                        <div key={kind} className="diag-map__target-group">
                          {kindFilter === 'ALL' ? (
                            <h5 className="diag-map__target-kind">{STRUCTURE_KIND_LABELS[kind]}</h5>
                          ) : null}
                          <div className="diag-map__char-list">
                            {list.map((item) => (
                              <label key={item.id} className="diag-map__char diag-map__char--target">
                                <input
                                  type="checkbox"
                                  checked={targets.includes(item.id)}
                                  onChange={() => toggleTarget(item.id)}
                                />
                                {item.label}
                              </label>
                            ))}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </fieldset>
              ) : null}

              <div className="diag-map__actions">
                <Button type="submit" loading={saving} disabled={deleting}>
                  {selectedEntry ? 'Zaktualizuj' : 'Zapisz'}
                </Button>
                {selectedEntry ? (
                  <Button
                    type="button"
                    variant="secondary"
                    loading={deleting}
                    disabled={saving}
                    onClick={() => void onDelete()}
                  >
                    Usuń
                  </Button>
                ) : null}
                <button type="button" className="diag-map__clear" onClick={clearSelection}>
                  Anuluj wybór
                </button>
              </div>
            </form>
          )}

          {sideEntries.length > 0 ? (
            <ul className="diag-map__badges" aria-label="Wpisy VAS">
              {sideEntries.map((entry) => {
                const targetCount = entry.treatment_targets?.length ?? 0
                const firstTarget =
                  targetCount > 0
                    ? targetLabel(entry.treatment_targets[0], entry.body_region)
                    : null
                return (
                  <li key={entry.id}>
                    <button
                      type="button"
                      className="diag-map__badge"
                      style={{ background: vasColor(entry.vas_score) }}
                      onClick={() => selectRegion(entry.body_region)}
                    >
                      <span className="diag-map__badge-text">
                        <span>{regionLabel(entry.body_region, side)}</span>
                        {firstTarget ? (
                          <span className="diag-map__badge-sub">
                            {firstTarget}
                            {targetCount > 1 ? ` +${targetCount - 1}` : ''}
                          </span>
                        ) : null}
                      </span>
                      <strong>{entry.vas_score}</strong>
                    </button>
                  </li>
                )
              })}
            </ul>
          ) : null}
        </div>
      </div>
    </section>
  )
}
