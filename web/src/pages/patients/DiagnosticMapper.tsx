import { useEffect, useMemo, useState, type FormEvent } from 'react'

import { treatmentApi } from '@/api/treatment'
import { ApiError } from '@/api/client'
import type { BodyAreaPain, BodyViewSide } from '@/api/types'
import { Button } from '@/components/ui/Button'
import {
  BODY_REGIONS,
  PAIN_CHARACTERS,
  regionLabel,
  vasColor,
} from '@/lib/bodyMap'
import './DiagnosticMapper.css'

interface DiagnosticMapperProps {
  episodeId: string
}

export function DiagnosticMapper({ episodeId }: DiagnosticMapperProps) {
  const [side, setSide] = useState<BodyViewSide>('FRONT')
  const [entries, setEntries] = useState<BodyAreaPain[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null)
  const [vas, setVas] = useState(5)
  const [characters, setCharacters] = useState<string[]>([])
  const [saving, setSaving] = useState(false)

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

  function selectRegion(regionId: string) {
    setSelectedRegion(regionId)
    const existing = entries.find(
      (entry) => entry.body_region === regionId && entry.view_side === side,
    )
    if (existing) {
      setVas(existing.vas_score)
      setCharacters(existing.pain_character ?? [])
    } else {
      setVas(5)
      setCharacters([])
    }
    setError(null)
  }

  function toggleCharacter(id: string) {
    setCharacters((prev) =>
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
        })
        setEntries((prev) => prev.map((entry) => (entry.id === updated.id ? updated : entry)))
      } else {
        const created = await treatmentApi.createBodyPain(episodeId, {
          body_region: selectedRegion,
          view_side: side,
          vas_score: vas,
          pain_character: characters,
        })
        setEntries((prev) => [...prev, created])
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Nie udało się zapisać wpisu VAS.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="diag-map" aria-label="Diagnostic Mapper">
      <header className="diag-map__header">
        <h3>Mapa ciała (VAS)</h3>
        <div className="diag-map__tabs" role="tablist" aria-label="Strona ciała">
          <button
            type="button"
            role="tab"
            aria-selected={side === 'FRONT'}
            className={side === 'FRONT' ? 'diag-map__tab diag-map__tab--active' : 'diag-map__tab'}
            onClick={() => {
              setSide('FRONT')
              setSelectedRegion(null)
            }}
          >
            Przód
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={side === 'BACK'}
            className={side === 'BACK' ? 'diag-map__tab diag-map__tab--active' : 'diag-map__tab'}
            onClick={() => {
              setSide('BACK')
              setSelectedRegion(null)
            }}
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
          <svg
            className="diag-map__svg"
            viewBox="0 0 200 400"
            role="img"
            aria-label={side === 'FRONT' ? 'Sylwetka — przód' : 'Sylwetka — tył'}
          >
            <rect
              x="60"
              y="4"
              width="80"
              height="392"
              rx="40"
              className="diag-map__silhouette"
            />
            {BODY_REGIONS[side].map((region) => {
              const entry = sideEntries.find((item) => item.body_region === region.id)
              const selected = selectedRegion === region.id
              return (
                <g key={`${side}-${region.id}`}>
                  <rect
                    x={region.x}
                    y={region.y}
                    width={region.w}
                    height={region.h}
                    rx={region.rx ?? 6}
                    className={
                      selected
                        ? 'diag-map__region diag-map__region--selected'
                        : 'diag-map__region'
                    }
                    style={
                      entry
                        ? { fill: vasColor(entry.vas_score), opacity: 0.92 }
                        : undefined
                    }
                    role="button"
                    tabIndex={0}
                    aria-label={`${region.label}${entry ? `, VAS ${entry.vas_score}` : ''}`}
                    onClick={() => selectRegion(region.id)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault()
                        selectRegion(region.id)
                      }
                    }}
                  />
                  {entry ? (
                    <text
                      x={region.x + region.w / 2}
                      y={region.y + region.h / 2 + 4}
                      textAnchor="middle"
                      className="diag-map__vas-label"
                    >
                      {entry.vas_score}
                    </text>
                  ) : null}
                </g>
              )
            })}
          </svg>
        </div>

        <div className="diag-map__panel">
          {!selectedRegion ? (
            <p className="diag-map__muted">Kliknij region na sylwetce, aby ustawić VAS i charakter bólu.</p>
          ) : (
            <form className="diag-map__form" onSubmit={(e) => void onSave(e)}>
              <h4>{regionLabel(selectedRegion, side)}</h4>
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

              <Button type="submit" loading={saving}>
                {selectedEntry ? 'Zaktualizuj' : 'Zapisz'}
              </Button>
            </form>
          )}

          {sideEntries.length > 0 ? (
            <ul className="diag-map__badges" aria-label="Wpisy VAS">
              {sideEntries.map((entry) => (
                <li key={entry.id}>
                  <button
                    type="button"
                    className="diag-map__badge"
                    style={{ background: vasColor(entry.vas_score) }}
                    onClick={() => selectRegion(entry.body_region)}
                  >
                    <span>{regionLabel(entry.body_region, side)}</span>
                    <strong>{entry.vas_score}</strong>
                  </button>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      </div>
    </section>
  )
}
