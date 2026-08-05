import { useEffect, useState, type FormEvent } from 'react'

import { authApi, therapistApi } from '@/api/auth'
import { getErrorMessage } from '@/api/client'
import type { TherapistProfile } from '@/api/types'
import { ErrorBanner, LoadingBlock } from '@/components/AsyncState'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import './ProfilePage.css'

export function ProfilePage() {
  const [profile, setProfile] = useState<TherapistProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [phone, setPhone] = useState('')
  const [bio, setBio] = useState('')
  const [avatarUrl, setAvatarUrl] = useState('')
  const [courses, setCourses] = useState<string[]>([])
  const [newCourse, setNewCourse] = useState('')
  const [profileBusy, setProfileBusy] = useState(false)
  const [profileMessage, setProfileMessage] = useState<string | null>(null)

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordBusy, setPasswordBusy] = useState(false)
  const [passwordError, setPasswordError] = useState<string | null>(null)
  const [passwordMessage, setPasswordMessage] = useState<string | null>(null)
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
        setBio(data.bio ?? '')
        setAvatarUrl(data.avatar_url ?? '')
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

  async function onSaveProfile(event: FormEvent) {
    event.preventDefault()
    setProfileBusy(true)
    setProfileMessage(null)
    setError(null)
    try {
      const updated = await therapistApi.updateProfile({
        phone: phone.trim(),
        bio: bio.trim(),
        avatar_url: avatarUrl.trim(),
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

  return (
    <section className="profile-page">
      <PageHeader
        title={`${profile.first_name} ${profile.last_name}`}
        description={`PWZFz ${profile.pwzf_number} · ${profile.email}`}
      />

      {error ? <ErrorBanner message={error} /> : null}

      <div className="profile-layout">
        <form className="profile-panel" onSubmit={(e) => void onSaveProfile(e)}>
          <h2>Dane gabinetowe</h2>
          <Field
            label="Telefon"
            name="phone"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
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
          <Field
            label="URL avatara"
            name="avatar_url"
            value={avatarUrl}
            onChange={(e) => setAvatarUrl(e.target.value)}
            hint="Opcjonalny link do zdjęcia (widoczny w aplikacji pacjenta)."
          />

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
