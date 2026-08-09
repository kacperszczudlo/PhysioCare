import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from 'react'

import { therapistApi } from '@/api/auth'
import { getErrorMessage, getFieldError } from '@/api/client'
import type { QualificationLevel, TherapistProfile } from '@/api/types'
import { useAuth } from '@/auth/AuthContext'
import { ErrorBanner, LoadingBlock, SuccessBanner } from '@/components/AsyncState'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import { PhoneField } from '@/components/ui/PhoneField'
import { DEFAULT_COUNTRY_CODE } from '@/lib/countries'
import {
  getAddressError,
  getBioError,
  getCourseError,
} from '@/lib/fieldPolicy'
import { useAuthenticatedMediaUrl } from '@/lib/authMedia'
import { formatPhoneForApi, getPhoneError, parseStoredPhone } from '@/lib/phonePolicy'
import './ProfilePage.css'

const QUALIFICATION_OPTIONS: { value: QualificationLevel; label: string }[] = [
  { value: 'TECHNIK', label: 'Technik fizjoterapii' },
  { value: 'LICENCJAT', label: 'Licencjat fizjoterapii' },
  { value: 'MAGISTER', label: 'Magister fizjoterapii' },
  { value: 'FIZJO_SPEC', label: 'Specjalista w dziedzinie fizjoterapii (FIZJO SPEC)' },
]

export function ProfilePage() {
  const { refreshSession } = useAuth()
  const [profile, setProfile] = useState<TherapistProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [phoneCountryCode, setPhoneCountryCode] = useState(DEFAULT_COUNTRY_CODE)
  const [phoneNational, setPhoneNational] = useState('')
  const [locationAddress, setLocationAddress] = useState('')
  const [bio, setBio] = useState('')
  const [courses, setCourses] = useState<string[]>([])
  const [newCourse, setNewCourse] = useState('')
  const [qualificationLevel, setQualificationLevel] = useState<QualificationLevel>('MAGISTER')
  const [experienceYears, setExperienceYears] = useState(0)
  const [profileBusy, setProfileBusy] = useState(false)
  const [profileMessage, setProfileMessage] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<{
    phone?: string
    locationAddress?: string
    bio?: string
    newCourse?: string
  }>({})

  const [avatarBusy, setAvatarBusy] = useState(false)
  const [avatarMessage, setAvatarMessage] = useState<string | null>(null)
  const [avatarError, setAvatarError] = useState<string | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [copyMessage, setCopyMessage] = useState<string | null>(null)
  const [copyError, setCopyError] = useState<string | null>(null)
  const [reloadToken, setReloadToken] = useState(0)
  const { url: remoteAvatarUrl } = useAuthenticatedMediaUrl(profile?.avatar_url)

  useEffect(() => {
    let cancelled = false

    async function load() {
      setLoading(true)
      setError(null)
      try {
        const data = await therapistApi.getProfile()
        if (cancelled) {
          return
        }
        setProfile(data)
        const parsedPhone = parseStoredPhone(data.phone)
        setPhoneCountryCode(parsedPhone.countryCode)
        setPhoneNational(parsedPhone.nationalNumber)
        setLocationAddress(data.location_address ?? '')
        setBio(data.bio ?? '')
        setCourses(Array.isArray(data.courses) ? data.courses : [])
        setQualificationLevel(data.qualification_level ?? 'MAGISTER')
        setExperienceYears(data.experience_years ?? 0)
      } catch (err) {
        if (!cancelled) {
          setProfile(null)
          setError(getErrorMessage(err, 'Nie udało się pobrać profilu.'))
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
  }, [reloadToken])

  useEffect(() => {
    return () => {
      if (previewUrl?.startsWith('blob:')) {
        URL.revokeObjectURL(previewUrl)
      }
    }
  }, [previewUrl])

  function addCourse() {
    const courseError = getCourseError(newCourse)
    if (courseError) {
      setFieldErrors((prev) => ({ ...prev, newCourse: courseError }))
      return
    }
    setCourses((prev) => [...prev, newCourse.trim()])
    setNewCourse('')
    setFieldErrors((prev) => ({ ...prev, newCourse: undefined }))
  }

  function removeCourse(index: number) {
    setCourses((prev) => prev.filter((_, i) => i !== index))
  }

  async function copyTherapistId() {
    if (!profile?.id) {
      return
    }
    try {
      await navigator.clipboard.writeText(profile.id)
      setCopyError(null)
      setCopyMessage('Skopiowano - przekaż ten kod pacjentowi przy rejestracji w aplikacji.')
    } catch {
      setCopyMessage(null)
      setCopyError('Nie udało się skopiować. Zaznacz kod ręcznie i skopiuj.')
    }
  }

  async function onSaveProfile(event: FormEvent) {
    event.preventDefault()
    setProfileMessage(null)
    setError(null)

    const nextErrors = {
      phone: getPhoneError(phoneNational, phoneCountryCode) ?? undefined,
      locationAddress: getAddressError(locationAddress) ?? undefined,
      bio: getBioError(bio) ?? undefined,
    }
    if (nextErrors.phone || nextErrors.locationAddress || nextErrors.bio) {
      setFieldErrors((prev) => ({ ...prev, ...nextErrors }))
      return
    }

    setFieldErrors({})
    setProfileBusy(true)
    try {
      const updated = await therapistApi.updateProfile({
        phone: formatPhoneForApi(phoneNational, phoneCountryCode),
        location_address: locationAddress.trim(),
        bio: bio.trim(),
        courses,
        qualification_level: qualificationLevel,
        experience_years: experienceYears,
      })
      setProfile(updated)
      const parsedPhone = parseStoredPhone(updated.phone)
      setPhoneCountryCode(parsedPhone.countryCode)
      setPhoneNational(parsedPhone.nationalNumber)
      setQualificationLevel(updated.qualification_level ?? 'MAGISTER')
      setExperienceYears(updated.experience_years ?? 0)
      setProfileMessage('Dane profilu zostały zapisane.')
    } catch (err) {
      const apiPhone = getFieldError(err, 'phone')
      const apiAddress = getFieldError(err, 'location_address')
      const apiBio = getFieldError(err, 'bio')
      if (apiPhone || apiAddress || apiBio) {
        setFieldErrors({
          phone: apiPhone ?? undefined,
          locationAddress: apiAddress ?? undefined,
          bio: apiBio ?? undefined,
        })
      }
      setError(getErrorMessage(err, 'Nie udało się zapisać profilu.'))
    } finally {
      setProfileBusy(false)
    }
  }

  async function onAvatarSelected(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) {
      return
    }

    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      setAvatarError('Dozwolone formaty: JPEG, PNG, WebP.')
      return
    }
    if (file.size > 5 * 1024 * 1024) {
      setAvatarError('Zdjęcie nie może być większe niż 5 MB.')
      return
    }

    const localPreview = URL.createObjectURL(file)
    setPreviewUrl((prev) => {
      if (prev?.startsWith('blob:')) {
        URL.revokeObjectURL(prev)
      }
      return localPreview
    })
    setAvatarError(null)
    setAvatarMessage(null)
    setAvatarBusy(true)
    try {
      const updated = await therapistApi.uploadAvatar(file)
      setProfile(updated)
      await refreshSession().catch(() => undefined)
      setAvatarMessage('Zdjęcie profilowe zostało zapisane - widoczne w aplikacji pacjenta.')
      URL.revokeObjectURL(localPreview)
      setPreviewUrl(null)
    } catch (err) {
      setAvatarError(getErrorMessage(err, 'Nie udało się przesłać avatara.'))
    } finally {
      setAvatarBusy(false)
    }
  }

  if (loading) {
    return (
      <section>
        <LoadingBlock label="Ładowanie profilu…" variant="panel" />
      </section>
    )
  }

  if (!profile) {
    return (
      <section>
        <PageHeader title="Profil" description="Nie udało się wczytać danych." />
        {error ? (
          <ErrorBanner message={error} onRetry={() => setReloadToken((value) => value + 1)} />
        ) : null}
      </section>
    )
  }

  const avatarSrc = previewUrl ?? remoteAvatarUrl
  const initials = `${profile.first_name?.[0] ?? ''}${profile.last_name?.[0] ?? ''}`.toUpperCase()
  const allowedCapabilities = profile.competences?.capabilities.filter((c) => c.allowed) ?? []

  return (
    <section className="profile-page">
      <PageHeader
        title="Profil"
        description={`${profile.first_name} ${profile.last_name} · PWZFz ${profile.pwzf_number}`}
      />

      {error ? <ErrorBanner message={error} /> : null}

      <div className="profile-grid">
        <form className="profile-main" onSubmit={(e) => void onSaveProfile(e)}>
          <section className="profile-card" aria-labelledby="profile-identity-heading">
            <header className="profile-card__head">
              <h2 id="profile-identity-heading">Tożsamość</h2>
              <p className="profile-muted">Zdjęcie i dane widoczne dla pacjentów w aplikacji.</p>
            </header>

            <div className="profile-avatar">
              <div className="profile-avatar__preview" aria-hidden={!avatarSrc}>
                {avatarSrc ? (
                  <img src={avatarSrc} alt="" className="profile-avatar__img" />
                ) : (
                  <span className="profile-avatar__initials">{initials || '?'}</span>
                )}
              </div>
              <div className="profile-avatar__meta">
                <p className="profile-avatar__label">Zdjęcie profilowe</p>
                <p className="profile-muted">JPEG, PNG lub WebP · max 5 MB</p>
                <p className="profile-avatar__email">{profile.email}</p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  className="profile-avatar__input"
                  onChange={(e) => void onAvatarSelected(e)}
                />
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  loading={avatarBusy}
                  onClick={() => fileInputRef.current?.click()}
                >
                  Wybierz zdjęcie
                </Button>
                {avatarError ? <ErrorBanner message={avatarError} /> : null}
                {avatarMessage ? <SuccessBanner message={avatarMessage} /> : null}
              </div>
            </div>

            <div className="profile-fields">
              <PhoneField
                countryCode={phoneCountryCode}
                nationalNumber={phoneNational}
                onCountryChange={(code) => {
                  setPhoneCountryCode(code)
                  if (fieldErrors.phone) {
                    setFieldErrors((prev) => ({ ...prev, phone: undefined }))
                  }
                }}
                onNationalNumberChange={(value) => {
                  setPhoneNational(value)
                  if (fieldErrors.phone) {
                    setFieldErrors((prev) => ({ ...prev, phone: undefined }))
                  }
                }}
                error={fieldErrors.phone}
                hint="Wybierz kraj, żeby ustawić prefix numeru."
              />
              <Field
                label="Adres / lokalizacja gabinetu"
                name="location_address"
                value={locationAddress}
                onChange={(e) => {
                  setLocationAddress(e.target.value)
                  if (fieldErrors.locationAddress) {
                    setFieldErrors((prev) => ({ ...prev, locationAddress: undefined }))
                  }
                }}
                error={fieldErrors.locationAddress}
                placeholder="np. ul. Kwiatowa 12, 00-001 Warszawa"
                hint="Widoczny dla pacjentów przy wizycie - kliknięcie otwiera mapę."
              />
            </div>
          </section>

          <section className="profile-card" aria-labelledby="profile-qual-heading">
            <header className="profile-card__head">
              <h2 id="profile-qual-heading">Kwalifikacje</h2>
              <p className="profile-muted">
                Poziom i staż wpływają na uprawnienia w panelu (NFZ / FIZJO SPEC).
              </p>
            </header>

            <div className="profile-fields profile-fields--split">
              <label className="ui-field">
                <span className="ui-field__label">Kwalifikacja zawodowa</span>
                <select
                  className="profile-select"
                  value={qualificationLevel}
                  onChange={(e) => setQualificationLevel(e.target.value as QualificationLevel)}
                >
                  {QUALIFICATION_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
                <span className="ui-field__hint">
                  Determinuje prawo do diagnozy funkcjonalnej i ordynacji wyrobów.
                </span>
              </label>

              <Field
                label="Staż w zawodzie (lata)"
                name="experience_years"
                type="number"
                min={0}
                max={60}
                value={String(experienceYears)}
                onChange={(e) => setExperienceYears(Number(e.target.value) || 0)}
                hint="≥3 lata: planowanie zabiegów; ≥5 lat: nadzór."
              />
            </div>
          </section>

          <section className="profile-card" aria-labelledby="profile-about-heading">
            <header className="profile-card__head">
              <h2 id="profile-about-heading">O mnie</h2>
              <p className="profile-muted">Biogram i kursy widoczne w profilu pacjenta.</p>
            </header>

            <div className="profile-fields">
              <label className="ui-field">
                <span className="ui-field__label">Biogram</span>
                <textarea
                  className={
                    fieldErrors.bio ? 'profile-textarea profile-textarea--error' : 'profile-textarea'
                  }
                  value={bio}
                  onChange={(e) => {
                    setBio(e.target.value)
                    if (fieldErrors.bio) {
                      setFieldErrors((prev) => ({ ...prev, bio: undefined }))
                    }
                  }}
                  rows={5}
                  maxLength={2000}
                  placeholder="Krótki opis doświadczenia i specjalizacji…"
                  aria-invalid={fieldErrors.bio ? true : undefined}
                />
                {fieldErrors.bio ? (
                  <span className="ui-field__error" role="alert">
                    {fieldErrors.bio}
                  </span>
                ) : null}
              </label>

              <div className="profile-courses">
                <h3>Kursy zawodowe</h3>
                {courses.length === 0 ? (
                  <p className="profile-muted">Brak kursów - dodaj pierwszy poniżej.</p>
                ) : (
                  <ul className="profile-courses__list">
                    {courses.map((course, index) => (
                      <li key={`${course}-${index}`} className="profile-courses__item">
                        <span>{course}</span>
                        <button
                          type="button"
                          className="profile-courses__remove"
                          onClick={() => removeCourse(index)}
                          aria-label={`Usuń kurs: ${course}`}
                        >
                          Usuń
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
                <div className="profile-courses__add">
                  <Field
                    label="Nowy kurs"
                    name="new_course"
                    value={newCourse}
                    onChange={(e) => {
                      setNewCourse(e.target.value)
                      if (fieldErrors.newCourse) {
                        setFieldErrors((prev) => ({ ...prev, newCourse: undefined }))
                      }
                    }}
                    error={fieldErrors.newCourse}
                    placeholder="np. Terapia manualna - kurs podstawowy"
                  />
                  <Button type="button" variant="secondary" size="sm" onClick={addCourse}>
                    Dodaj
                  </Button>
                </div>
              </div>
            </div>
          </section>

          <div className="profile-actions">
            <Button type="submit" loading={profileBusy}>
              Zapisz profil
            </Button>
            {profileMessage ? <SuccessBanner message={profileMessage} /> : null}
          </div>
        </form>

        <aside className="profile-aside">
          <section className="profile-card profile-card--accent" aria-labelledby="invite-heading">
            <header className="profile-card__head">
              <h2 id="invite-heading">Kod dla pacjenta</h2>
              <p className="profile-muted">
                Pacjent podaje ten kod przy rejestracji w aplikacji mobilnej.
              </p>
            </header>
            <code className="profile-invite__id" title="ID profilu fizjoterapeuty">
              {profile.id}
            </code>
            <Button type="button" variant="secondary" onClick={() => void copyTherapistId()}>
              Kopiuj kod
            </Button>
            {copyError ? <ErrorBanner message={copyError} /> : null}
            {copyMessage ? <SuccessBanner message={copyMessage} /> : null}
          </section>

          {profile.competences ? (
            <section className="profile-card" aria-labelledby="comp-heading">
              <header className="profile-card__head">
                <h2 id="comp-heading">Uprawnienia</h2>
                <p className="profile-muted">
                  {profile.competences.qualification_label}
                  {' · '}
                  staż {profile.competences.experience_years}{' '}
                  {profile.competences.experience_years === 1 ? 'rok' : 'lat'}
                </p>
              </header>

              <div className="profile-competences__summary" role="list">
                <span
                  className={
                    profile.competences.can_plan_therapy
                      ? 'profile-competences__chip profile-competences__chip--ok'
                      : 'profile-competences__chip'
                  }
                  role="listitem"
                >
                  Planowanie terapii
                </span>
                <span
                  className={
                    profile.competences.can_supervise
                      ? 'profile-competences__chip profile-competences__chip--ok'
                      : 'profile-competences__chip'
                  }
                  role="listitem"
                >
                  Nadzór
                </span>
                <span
                  className={
                    profile.competences.is_fizjo_spec
                      ? 'profile-competences__chip profile-competences__chip--ok'
                      : 'profile-competences__chip'
                  }
                  role="listitem"
                >
                  FIZJO SPEC
                </span>
                {profile.competences.device_groups.length > 0 ? (
                  <span
                    className="profile-competences__chip profile-competences__chip--ok"
                    role="listitem"
                  >
                    Wyroby: {profile.competences.device_groups.join(', ')}
                  </span>
                ) : (
                  <span className="profile-competences__chip" role="listitem">
                    Brak ordynacji wyrobów
                  </span>
                )}
              </div>

              {allowedCapabilities.length > 0 ? (
                <ul className="profile-competences__list">
                  {allowedCapabilities.map((cap) => (
                    <li key={cap.code} className="profile-competences__item">
                      <details>
                        <summary>{cap.label}</summary>
                        <p>{cap.detail}</p>
                      </details>
                    </li>
                  ))}
                </ul>
              ) : null}
            </section>
          ) : null}
        </aside>
      </div>
    </section>
  )
}
