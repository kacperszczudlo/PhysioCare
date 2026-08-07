import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from 'react'

import { authApi, therapistApi } from '@/api/auth'
import { getErrorMessage } from '@/api/client'
import type { TherapistProfile } from '@/api/types'
import { ErrorBanner, LoadingBlock } from '@/components/AsyncState'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import { resolveMediaUrl } from '@/lib/mediaUrl'
import './ProfilePage.css'

export function ProfilePage() {
  const [profile, setProfile] = useState<TherapistProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [phone, setPhone] = useState('')
  const [locationAddress, setLocationAddress] = useState('')
  const [bio, setBio] = useState('')
  const [courses, setCourses] = useState<string[]>([])
  const [newCourse, setNewCourse] = useState('')
  const [profileBusy, setProfileBusy] = useState(false)
  const [profileMessage, setProfileMessage] = useState<string | null>(null)

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
  const [copyMessage, setCopyMessage] = useState<string | null>(null)
  const [reloadToken, setReloadToken] = useState(0)

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
    const value = newCourse.trim()
    if (!value) {
      return
    }
    setCourses((prev) => [...prev, value])
    setNewCourse('')
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
      setCopyMessage('Skopiowano — przekaż ten kod pacjentowi przy rejestracji w aplikacji.')
    } catch {
      setCopyMessage('Nie udało się skopiować. Zaznacz kod ręcznie i skopiuj.')
    }
  }

  async function onSaveProfile(event: FormEvent) {
    event.preventDefault()
    setProfileBusy(true)
    setProfileMessage(null)
    setError(null)
    try {
      const updated = await therapistApi.updateProfile({
        phone: phone.trim(),
        location_address: locationAddress.trim(),
        bio: bio.trim(),
        courses,
      })
      setProfile(updated)
      setProfileMessage('Profil zapisany.')
    } catch (err) {
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
      setAvatarMessage('Avatar zapisany — widoczny w aplikacji pacjenta.')
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

    if (newPassword !== confirmPassword) {
      setPasswordError('Nowe hasła nie są identyczne.')
      return
    }
    if (newPassword.length < 8) {
      setPasswordError('Nowe hasło musi mieć co najmniej 8 znaków.')
      return
    }

    setPasswordBusy(true)
    try {
      const { detail } = await authApi.changePassword(currentPassword, newPassword)
      setPasswordMessage(detail)
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
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
        {copyMessage ? (
          <p className="profile-banner profile-banner--ok" role="status">
            {copyMessage}
          </p>
        ) : null}
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
              {avatarError ? (
                <p className="profile-banner profile-banner--error" role="alert">
                  {avatarError}
                </p>
              ) : null}
              {avatarMessage ? (
                <p className="profile-banner profile-banner--ok" role="status">
                  {avatarMessage}
                </p>
              ) : null}
            </div>
          </div>

          <Field
            label="Telefon"
            name="phone"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
          <Field
            label="Adres / lokalizacja gabinetu"
            name="location_address"
            value={locationAddress}
            onChange={(e) => setLocationAddress(e.target.value)}
            placeholder="np. ul. Kwiatowa 12, 00-001 Warszawa"
            hint="Widoczny dla pacjentów przy wizycie — kliknięcie otwiera mapę."
          />
          <label className="ui-field">
            <span className="ui-field__label">Biogram</span>
            <textarea
              className="profile-textarea"
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              rows={5}
              placeholder="Krótki opis doświadczenia i specjalizacji…"
            />
          </label>

          <div className="profile-courses">
            <h3>Kursy zawodowe</h3>
            {courses.length === 0 ? (
              <p className="profile-muted">Brak kursów — dodaj pierwszy poniżej.</p>
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
                onChange={(e) => setNewCourse(e.target.value)}
                placeholder="np. Terapia manualna — kurs podstawowy"
              />
              <Button type="button" variant="secondary" size="sm" onClick={addCourse}>
                + Dodaj
              </Button>
            </div>
          </div>

          {profileMessage ? (
            <p className="profile-banner profile-banner--ok" role="status">
              {profileMessage}
            </p>
          ) : null}

          <Button type="submit" loading={profileBusy}>
            Zapisz profil
          </Button>
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
            onChange={(e) => setNewPassword(e.target.value)}
            required
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

          {passwordError ? (
            <p className="profile-banner profile-banner--error" role="alert">
              {passwordError}
            </p>
          ) : null}
          {passwordMessage ? (
            <p className="profile-banner profile-banner--ok" role="status">
              {passwordMessage}
            </p>
          ) : null}

          <Button type="submit" loading={passwordBusy}>
            Zmień hasło
          </Button>
        </form>
      </div>
    </section>
  )
}
