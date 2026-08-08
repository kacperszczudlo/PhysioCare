import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from 'react'

import { authApi, therapistApi } from '@/api/auth'
import { getErrorMessage, getFieldError } from '@/api/client'
import type { QualificationLevel, TherapistProfile } from '@/api/types'
import { ErrorBanner, LoadingBlock, SuccessBanner } from '@/components/AsyncState'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import { PasswordRequirements } from '@/components/ui/PasswordRequirements'
import {
  getAddressError,
  getBioError,
  getCourseError,
} from '@/lib/fieldPolicy'
import { resolveMediaUrl } from '@/lib/mediaUrl'
import {
  getPasswordError,
  getPasswordRequirements,
  PASSWORD_MESSAGES,
  passwordsMatch,
} from '@/lib/passwordPolicy'
import { formatPhoneForApi, getPhoneError } from '@/lib/phonePolicy'
import './ProfilePage.css'

const QUALIFICATION_OPTIONS: { value: QualificationLevel; label: string }[] = [
  { value: 'TECHNIK', label: 'Technik fizjoterapii' },
  { value: 'LICENCJAT', label: 'Licencjat fizjoterapii' },
  { value: 'MAGISTER', label: 'Magister fizjoterapii' },
  { value: 'FIZJO_SPEC', label: 'Specjalista w dziedzinie fizjoterapii (FIZJO SPEC)' },
]

export function ProfilePage() {
  const [profile, setProfile] = useState<TherapistProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [phone, setPhone] = useState('')
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

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordBusy, setPasswordBusy] = useState(false)
  const [passwordError, setPasswordError] = useState<string | null>(null)
  const [passwordMessage, setPasswordMessage] = useState<string | null>(null)
  const [passwordTouched, setPasswordTouched] = useState(false)
  const [copyMessage, setCopyMessage] = useState<string | null>(null)
  const [copyError, setCopyError] = useState<string | null>(null)
  const [reloadToken, setReloadToken] = useState(0)

  const passwordRequirements = getPasswordRequirements(newPassword)

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
        setPhone(data.phone ?? '')
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
      phone: getPhoneError(phone) ?? undefined,
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
        phone: formatPhoneForApi(phone),
        location_address: locationAddress.trim(),
        bio: bio.trim(),
        courses,
        qualification_level: qualificationLevel,
        experience_years: experienceYears,
      })
      setProfile(updated)
      setPhone(updated.phone ?? '')
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
      setAvatarMessage('Zdjęcie profilowe zostało zapisane - widoczne w aplikacji pacjenta.')
      URL.revokeObjectURL(localPreview)
      setPreviewUrl(null)
    } catch (err) {
      setAvatarError(getErrorMessage(err, 'Nie udało się przesłać avatara.'))
    } finally {
      setAvatarBusy(false)
    }
  }

  async function onChangePassword(event: FormEvent) {
    event.preventDefault()
    setPasswordError(null)
    setPasswordMessage(null)

    if (!currentPassword.trim()) {
      setPasswordError('Podaj obecne hasło.')
      return
    }
    const newPasswordError = getPasswordError(newPassword)
    if (newPasswordError) {
      setPasswordError(newPasswordError)
      return
    }
    if (!passwordsMatch(newPassword, confirmPassword)) {
      setPasswordError(PASSWORD_MESSAGES.mismatch)
      return
    }

    setPasswordBusy(true)
    try {
      const { detail } = await authApi.changePassword(currentPassword, newPassword)
      setPasswordMessage(detail)
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      setPasswordTouched(false)
    } catch (err) {
      setPasswordError(getErrorMessage(err, 'Nie udało się zmienić hasła.'))
    } finally {
      setPasswordBusy(false)
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

  const avatarSrc = previewUrl ?? resolveMediaUrl(profile.avatar_url)
  const initials = `${profile.first_name?.[0] ?? ''}${profile.last_name?.[0] ?? ''}`.toUpperCase()

  return (
    <section className="profile-page">
      <PageHeader
        title={`${profile.first_name} ${profile.last_name}`}
        description={`PWZFz ${profile.pwzf_number} · ${profile.email}`}
      />

      {error ? <ErrorBanner message={error} /> : null}

      <aside className="profile-invite" aria-labelledby="invite-heading">
        <div className="profile-invite__copy">
          <h2 id="invite-heading">Kod dla pacjenta</h2>
          <p className="profile-muted">
            Pacjent podaje ten kod przy rejestracji w aplikacji mobilnej. Skopiuj i prześlij
            go pacjentowi (SMS, e-mail lub wiadomość).
          </p>
        </div>
        <div className="profile-invite__actions">
          <code className="profile-invite__id" title="ID profilu terapeuty">
            {profile.id}
          </code>
          <Button type="button" variant="secondary" size="sm" onClick={() => void copyTherapistId()}>
            Kopiuj kod
          </Button>
        </div>
        {copyError ? <ErrorBanner message={copyError} /> : null}
        {copyMessage ? <SuccessBanner message={copyMessage} /> : null}
      </aside>

      <div className="profile-layout">
        <form className="profile-panel" onSubmit={(e) => void onSaveProfile(e)}>
          <h2>Dane gabinetowe</h2>

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
              <p className="profile-muted">JPEG, PNG lub WebP · max 5 MB. Widoczne dla pacjentów.</p>
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

          <Field
            label="Telefon"
            name="phone"
            type="tel"
            inputMode="tel"
            value={phone}
            onChange={(e) => {
              setPhone(e.target.value)
              if (fieldErrors.phone) {
                setFieldErrors((prev) => ({ ...prev, phone: undefined }))
              }
            }}
            error={fieldErrors.phone}
            hint="Polski numer: 9 cyfr, opcjonalnie z +48"
            placeholder="np. 512 345 678"
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
              Determinuje prawo do diagnozy funkcjonalnej i ordynacji wyrobów (magister / FIZJO SPEC).
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
            hint="≥3 lata: samodzielne planowanie zabiegów (NFZ); ≥5 lat: nadzór."
          />

          {profile.competences ? (
            <div className="profile-competences" aria-label="Macierz kompetencji">
              <div className="profile-competences__head">
                <h3>Twoje uprawnienia</h3>
                <p className="profile-muted">
                  {profile.competences.qualification_label}
                  {' · '}
                  staż {profile.competences.experience_years}{' '}
                  {profile.competences.experience_years === 1 ? 'rok' : 'lat'}
                </p>
              </div>

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
                  <span className="profile-competences__chip profile-competences__chip--ok" role="listitem">
                    Wyroby: {profile.competences.device_groups.join(', ')}
                  </span>
                ) : (
                  <span className="profile-competences__chip" role="listitem">
                    Brak ordynacji wyrobów
                  </span>
                )}
              </div>

              <div className="profile-competences__columns">
                <section className="profile-competences__group" aria-labelledby="comp-allowed">
                  <h4 id="comp-allowed">
                    Uprawnienia
                    <span className="profile-competences__count">
                      {profile.competences.capabilities.filter((c) => c.allowed).length}
                    </span>
                  </h4>
                  <ul className="profile-competences__list">
                    {profile.competences.capabilities
                      .filter((cap) => cap.allowed)
                      .map((cap) => (
                        <li key={cap.code} className="profile-competences__item">
                          <details>
                            <summary>{cap.label}</summary>
                            <p>{cap.detail}</p>
                          </details>
                        </li>
                      ))}
                  </ul>
                </section>
              </div>
            </div>
          ) : null}

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
                + Dodaj
              </Button>
            </div>
          </div>

          <Button type="submit" loading={profileBusy}>
            Zapisz profil
          </Button>
          {profileMessage ? <SuccessBanner message={profileMessage} /> : null}
        </form>

        <form className="profile-panel" onSubmit={(e) => void onChangePassword(e)}>
          <h2>Zmiana hasła</h2>
          <Field
            label="Obecne hasło"
            name="current_password"
            type="password"
            autoComplete="current-password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            required
          />
          <Field
            label="Nowe hasło"
            name="new_password"
            type="password"
            autoComplete="new-password"
            value={newPassword}
            onChange={(e) => {
              setNewPassword(e.target.value)
              setPasswordTouched(true)
            }}
            onBlur={() => setPasswordTouched(true)}
            required
          />
          <PasswordRequirements
            requirements={passwordRequirements}
            showErrors={passwordTouched}
          />
          <Field
            label="Powtórz nowe hasło"
            name="confirm_password"
            type="password"
            autoComplete="new-password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />

          <Button type="submit" loading={passwordBusy}>
            Zmień hasło
          </Button>
          {passwordError ? <ErrorBanner message={passwordError} /> : null}
          {passwordMessage ? <SuccessBanner message={passwordMessage} /> : null}
        </form>
      </div>
    </section>
  )
}
