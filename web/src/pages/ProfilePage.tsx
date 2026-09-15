import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from 'react'

import { therapistApi } from '@/api/auth'
import { getErrorMessage, getFieldError } from '@/api/client'
import type { QualificationLevel, TherapistProfile } from '@/api/types'
import { useAuth } from '@/auth/AuthContext'
import { ErrorBanner, LoadingBlock } from '@/components/AsyncState'
import { ProfileSkeleton } from '@/components/skeletons/WebSkeletons'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import { LocationField } from '@/components/location/LocationField'
import { PhoneField } from '@/components/ui/PhoneField'
import { useToast } from '@/components/ui/ToastContext'
import { DEFAULT_COUNTRY_CODE } from '@/lib/countries'
import { getAddressError, getBioError, getCourseError } from '@/lib/fieldPolicy'
import { useAuthenticatedMediaUrl } from '@/lib/authMedia'
import { formatPhoneForApi, getPhoneError, parseStoredPhone } from '@/lib/phonePolicy'
import './ProfilePage.css'

const QUALIFICATION_TILES: ReadonlyArray<{
  value: QualificationLevel
  title: string
  sub: string
}> = [
  {
    value: 'MAGISTER',
    title: 'Magister fizjoterapii',
    sub: 'Samodzielne planowanie i ordynacja wyrobów medycznych',
  },
  {
    value: 'LICENCJAT',
    title: 'Licencjat fizjoterapii',
    sub: 'Podstawowe planowanie i realizacja świadczeń',
  },
  {
    value: 'FIZJO_SPEC',
    title: 'Specjalista (FIZJO SPEC)',
    sub: 'Zaawansowany sprzęt i pełny zakres diagnostyki',
  },
  {
    value: 'TECHNIK',
    title: 'Technik fizjoterapii',
    sub: 'Realizacja zabiegów fizjoterapeutycznych',
  },
]

export function ProfilePage() {
  const { refreshSession } = useAuth()
  const { toast } = useToast()
  const [profile, setProfile] = useState<TherapistProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [phoneCountryCode, setPhoneCountryCode] = useState(DEFAULT_COUNTRY_CODE)
  const [phoneNational, setPhoneNational] = useState('')
  const [locationAddress, setLocationAddress] = useState('')
  const [bio, setBio] = useState('')
  const [courses, setCourses] = useState<string[]>([])
  const [newCourse, setNewCourse] = useState('')
  const [qualificationLevel, setQualificationLevel] = useState<QualificationLevel>('MAGISTER')
  const [experienceYears, setExperienceYears] = useState(0)
  const [profileBusy, setProfileBusy] = useState(false)
  const [fieldErrors, setFieldErrors] = useState<{
    firstName?: string
    lastName?: string
    phone?: string
    locationAddress?: string
    bio?: string
    newCourse?: string
  }>({})

  const [avatarBusy, setAvatarBusy] = useState(false)
  const [avatarError, setAvatarError] = useState<string | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

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
        setFirstName(data.first_name ?? '')
        setLastName(data.last_name ?? '')
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

  function resetForm() {
    if (!profile) return
    setFirstName(profile.first_name ?? '')
    setLastName(profile.last_name ?? '')
    const parsedPhone = parseStoredPhone(profile.phone)
    setPhoneCountryCode(parsedPhone.countryCode)
    setPhoneNational(parsedPhone.nationalNumber)
    setLocationAddress(profile.location_address ?? '')
    setBio(profile.bio ?? '')
    setCourses(Array.isArray(profile.courses) ? profile.courses : [])
    setQualificationLevel(profile.qualification_level ?? 'MAGISTER')
    setExperienceYears(profile.experience_years ?? 0)
    setNewCourse('')
    setFieldErrors({})
  }

  const initialPhone = profile ? parseStoredPhone(profile.phone) : null
  const isDirty = Boolean(
    profile &&
    (firstName.trim() !== (profile.first_name ?? '') ||
      lastName.trim() !== (profile.last_name ?? '') ||
      phoneCountryCode !== initialPhone?.countryCode ||
      phoneNational !== initialPhone?.nationalNumber ||
      locationAddress !== (profile.location_address ?? '') ||
      bio !== (profile.bio ?? '') ||
      qualificationLevel !== (profile.qualification_level ?? 'MAGISTER') ||
      experienceYears !== (profile.experience_years ?? 0) ||
      JSON.stringify(courses) !== JSON.stringify(profile.courses ?? [])),
  )

  useEffect(() => {
    function handleBeforeUnload(e: BeforeUnloadEvent) {
      if (isDirty) {
        e.preventDefault()
        e.returnValue = ''
      }
    }
    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [isDirty])

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



  async function onSaveProfile(event: FormEvent) {
    event.preventDefault()
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
        first_name: firstName.trim() || undefined,
        last_name: lastName.trim() || undefined,
        phone: formatPhoneForApi(phoneNational, phoneCountryCode),
        location_address: locationAddress.trim(),
        bio: bio.trim(),
        courses,
        qualification_level: qualificationLevel,
        experience_years: experienceYears,
      })
      setProfile(updated)
      setFirstName(updated.first_name ?? '')
      setLastName(updated.last_name ?? '')
      await refreshSession().catch(() => undefined)
      const parsedPhone = parseStoredPhone(updated.phone)
      setPhoneCountryCode(parsedPhone.countryCode)
      setPhoneNational(parsedPhone.nationalNumber)
      setQualificationLevel(updated.qualification_level ?? 'MAGISTER')
      setExperienceYears(updated.experience_years ?? 0)
      toast.success('Dane profilu zostały zapisane.', { title: 'Sukces' })
    } catch (err) {
      const apiFirstName = getFieldError(err, 'first_name')
      const apiLastName = getFieldError(err, 'last_name')
      const apiPhone = getFieldError(err, 'phone')
      const apiAddress = getFieldError(err, 'location_address')
      const apiBio = getFieldError(err, 'bio')
      if (apiFirstName || apiLastName || apiPhone || apiAddress || apiBio) {
        setFieldErrors({
          firstName: apiFirstName ?? undefined,
          lastName: apiLastName ?? undefined,
          phone: apiPhone ?? undefined,
          locationAddress: apiAddress ?? undefined,
          bio: apiBio ?? undefined,
        })
      }
      const errMsg = getErrorMessage(err, 'Nie udało się zapisać profilu.')
      setError(errMsg)
      toast.error(errMsg)
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
      const err = 'Dozwolone formaty: JPEG, PNG, WebP.'
      setAvatarError(err)
      toast.error(err)
      return
    }
    if (file.size > 5 * 1024 * 1024) {
      const err = 'Zdjęcie nie może być większe niż 5 MB.'
      setAvatarError(err)
      toast.error(err)
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
    setAvatarBusy(true)
    try {
      const updated = await therapistApi.uploadAvatar(file)
      setProfile(updated)
      await refreshSession().catch(() => undefined)
      toast.success('Zdjęcie profilowe zostało zapisane.', { title: 'Sukces' })
      URL.revokeObjectURL(localPreview)
      setPreviewUrl(null)
    } catch (err) {
      const errMsg = getErrorMessage(err, 'Nie udało się przesłać avatara.')
      setAvatarError(errMsg)
      toast.error(errMsg)
    } finally {
      setAvatarBusy(false)
    }
  }

  if (loading) {
    return (
      <section>
        <LoadingBlock label="Ładowanie profilu…" skeleton={<ProfileSkeleton />} />
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
              </div>
            </div>

            <div className="profile-fields">
              <div
                className="profile-fields profile-fields--split"
                style={{ margin: 0, padding: 0 }}
              >
                <Field
                  label="Imię"
                  name="first_name"
                  value={firstName}
                  onChange={(e) => {
                    setFirstName(e.target.value)
                    if (fieldErrors.firstName) {
                      setFieldErrors((prev) => ({ ...prev, firstName: undefined }))
                    }
                  }}
                  error={fieldErrors.firstName}
                />
                <Field
                  label="Nazwisko"
                  name="last_name"
                  value={lastName}
                  onChange={(e) => {
                    setLastName(e.target.value)
                    if (fieldErrors.lastName) {
                      setFieldErrors((prev) => ({ ...prev, lastName: undefined }))
                    }
                  }}
                  error={fieldErrors.lastName}
                />
              </div>
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
              <LocationField
                label="Adres / lokalizacja gabinetu"
                name="location_address"
                value={locationAddress}
                onChange={(val) => {
                  setLocationAddress(val)
                  if (fieldErrors.locationAddress) {
                    setFieldErrors((prev) => ({ ...prev, locationAddress: undefined }))
                  }
                }}
                error={fieldErrors.locationAddress}
                placeholder="np. ul. Kwiatowa 12, 00-001 Warszawa"
                hint="Widoczny dla pacjentów przy wizycie. Możesz wyszukać adres lub ustawić go na interaktywnej mapie."
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
              <div className="ui-field" style={{ gridColumn: '1 / -1' }}>
                <span className="ui-field__label">Kwalifikacja zawodowa</span>
                <div className="qualification-grid" role="radiogroup" aria-label="Kwalifikacja zawodowa">
                  {QUALIFICATION_TILES.map((tile) => {
                    const isSelected = qualificationLevel === tile.value
                    return (
                      <button
                        key={tile.value}
                        type="button"
                        role="radio"
                        aria-checked={isSelected}
                        className={`qualification-tile ${isSelected ? 'qualification-tile--selected' : ''}`}
                        onClick={() => setQualificationLevel(tile.value)}
                      >
                        <span className="qualification-tile__title">{tile.title}</span>
                        <span className="qualification-tile__sub">{tile.sub}</span>
                      </button>
                    )
                  })}
                </div>
                <span className="ui-field__hint" style={{ marginTop: '0.5rem' }}>
                  Determinuje prawo do diagnozy funkcjonalnej i ordynacji wyrobów medycznych w panelu.
                </span>
              </div>

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
                    fieldErrors.bio
                      ? 'profile-textarea profile-textarea--error'
                      : 'profile-textarea'
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

          <div
            className={
              isDirty
                ? 'profile-floating-bar profile-floating-bar--visible'
                : 'profile-floating-bar'
            }
            role="region"
            aria-label="Niezapisane zmiany w profilu"
            aria-live="polite"
          >
            <div className="profile-floating-bar__status">
              <span className="profile-floating-bar__dot" aria-hidden="true" />
              <div className="profile-floating-bar__labels">
                <span className="profile-floating-bar__title">Masz niezapisane zmiany</span>
                <span className="profile-floating-bar__desc">
                  Zapisz lub anuluj wprowadzone modyfikacje w profilu.
                </span>
              </div>
            </div>
            <div className="profile-floating-bar__actions">
              <button
                type="button"
                className="profile-floating-bar__btn profile-floating-bar__btn--secondary"
                disabled={profileBusy}
                onClick={resetForm}
              >
                Odrzuć
              </button>
              <button
                type="submit"
                className="profile-floating-bar__btn profile-floating-bar__btn--primary"
                disabled={profileBusy}
              >
                {profileBusy ? 'Zapisywanie…' : 'Zapisz profil'}
              </button>
            </div>
          </div>
        </form>

        <aside className="profile-aside">

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
