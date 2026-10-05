import { useEffect, useState } from 'react'

import { getErrorMessage } from '@/api/client'
import { reviewsApi } from '@/api/reviews'
import type { RatingSummary, ReviewItem } from '@/api/types'
import { EmptyState, ErrorBanner, LoadingBlock } from '@/components/AsyncState'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { useToast } from '@/components/ui/ToastContext'
import { AuthMediaImg } from '@/components/AuthMedia'
import { Select, type SelectOption } from '@/components/ui/Select'
import { useAuth } from '@/auth/AuthContext'
import './TherapistReviewsModal.css'

interface TherapistReviewsModalProps {
  open: boolean
  therapistId: string
  onClose: () => void
  onReviewsUpdated?: () => void
}

function StarIcon({ filled, size = 16 }: { filled: boolean; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill={filled ? '#f59e0b' : 'none'}
      stroke={filled ? '#f59e0b' : 'currentColor'}
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
    </svg>
  )
}

function StarRating({ rating, size = 16 }: { rating: number; size?: number }) {
  return (
    <div className="reviews-summary__stars" aria-label={`Ocena: ${rating} na 5 gwiazdek`}>
      {[1, 2, 3, 4, 5].map((star) => (
        <StarIcon key={star} filled={star <= rating} size={size} />
      ))}
    </div>
  )
}

function formatReviewDate(dateStr: string): string {
  try {
    return new Intl.DateTimeFormat('pl-PL', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    }).format(new Date(dateStr))
  } catch {
    return dateStr
  }
}

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return '?'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[1][0]).toUpperCase()
}

function ReviewAvatar({ item }: { item: ReviewItem }) {
  if (item.is_anonymous) {
    return (
      <div
        className="review-avatar review-avatar--anon"
        title="Anonimowy pacjent"
        aria-label="Anonimowy pacjent"
      >
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
          <circle cx="12" cy="7" r="4" />
        </svg>
      </div>
    )
  }

  if (item.author_avatar_url) {
    return (
      <div className="review-avatar review-avatar--img" title={item.author_name}>
        <AuthMediaImg
          path={item.author_avatar_url}
          alt={item.author_name}
          className="review-avatar__img"
        />
        <span className="review-avatar__fallback" aria-hidden="true">
          {getInitials(item.author_name)}
        </span>
      </div>
    )
  }

  return (
    <div
      className="review-avatar review-avatar--initials"
      title={item.author_name}
      aria-hidden="true"
    >
      {getInitials(item.author_name)}
    </div>
  )
}

const SORT_OPTIONS: SelectOption<'-created_at' | '-rating' | 'rating'>[] = [
  { value: '-created_at', label: 'Najnowsze' },
  { value: '-rating', label: 'Najwyższa ocena' },
  { value: 'rating', label: 'Najniższa ocena' },
]

export function TherapistReviewsModal({
  open,
  therapistId,
  onClose,
  onReviewsUpdated,
}: TherapistReviewsModalProps) {
  const { toast } = useToast()
  const { user } = useAuth()
  const therapistFullName =
    `${user?.first_name ?? ''} ${user?.last_name ?? ''}`.trim() || 'Fizjoterapeuta'
  const therapistInitials =
    `${user?.first_name?.[0] ?? ''}${user?.last_name?.[0] ?? ''}`.toUpperCase() || 'FT'

  const [reviews, setReviews] = useState<ReviewItem[]>([])
  const [summary, setSummary] = useState<RatingSummary | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [ratingFilter, setRatingFilter] = useState<number | null>(null)
  const [ordering, setOrdering] = useState<'-created_at' | '-rating' | 'rating'>('-created_at')

  // Stan odpowiedzi na opinię
  const [replyingToId, setReplyingToId] = useState<string | null>(null)
  const [replyDraft, setReplyDraft] = useState('')
  const [replySubmitting, setReplySubmitting] = useState(false)
  const [replyError, setReplyError] = useState<string | null>(null)

  useEffect(() => {
    if (!open || !therapistId) return

    let cancelled = false
    async function fetchData() {
      setLoading(true)
      setError(null)
      try {
        const [reviewsData, summaryData] = await Promise.all([
          reviewsApi.listReviews(therapistId, ratingFilter ?? undefined, ordering),
          reviewsApi.getRatingSummary(therapistId),
        ])
        if (!cancelled) {
          setReviews(reviewsData)
          setSummary(summaryData)
        }
      } catch (err) {
        if (!cancelled) {
          setError(getErrorMessage(err, 'Nie udało się pobrać opinii pacjentów.'))
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void fetchData()
    return () => {
      cancelled = true
    }
  }, [open, therapistId, ratingFilter, ordering])

  function startReplying(review: ReviewItem) {
    setReplyingToId(review.id)
    setReplyDraft(review.therapist_reply || '')
    setReplyError(null)
  }

  function cancelReplying() {
    setReplyingToId(null)
    setReplyDraft('')
    setReplyError(null)
  }

  async function handleSendReply(reviewId: string) {
    const trimmed = replyDraft.trim()
    if (!trimmed) {
      const msg = 'Treść odpowiedzi nie może być pusta.'
      setReplyError(msg)
      toast.error('Wpisz treść odpowiedzi przed jej zapisaniem.', {
        title: 'Brak treści odpowiedzi',
      })
      return
    }

    setReplySubmitting(true)
    setReplyError(null)
    try {
      const updated = await reviewsApi.replyToReview(reviewId, trimmed)
      setReviews((prev) =>
        prev.map((r) => (r.id === reviewId ? { ...r, ...updated, therapist_reply: trimmed } : r)),
      )
      toast.success('Twoja odpowiedź została pomyślnie opublikowana pod opinią pacjenta.', {
        title: 'Odpowiedź wysłana',
      })
      setReplyingToId(null)
      setReplyDraft('')
      onReviewsUpdated?.()
    } catch (err) {
      const errMsg = getErrorMessage(err, 'Nie udało się zapisać odpowiedzi.')
      setReplyError(errMsg)
      toast.error(errMsg, { title: 'Błąd zapisu' })
    } finally {
      setReplySubmitting(false)
    }
  }

  const totalReviews = summary?.total_reviews ?? 0
  const avgRating = summary ? Number(summary.average_rating).toFixed(1) : '0.0'

  return (
    <Modal
      open={open}
      title="Opinie i oceny pacjentów"
      description="Przeglądaj recenzje pacjentów oraz odpowiadaj na opinie."
      size="lg"
      onClose={onClose}
    >
      <div className="reviews-modal">
        {summary && totalReviews > 0 ? (
          <div className="reviews-summary">
            <div className="reviews-summary__score">
              <span className="reviews-summary__avg">{avgRating}</span>
              <StarRating rating={Math.round(Number(summary.average_rating))} size={18} />
              <span className="reviews-summary__count">
                {totalReviews} {totalReviews === 1 ? 'opinia' : totalReviews < 5 ? 'opinie' : 'opinii'}
              </span>
            </div>

            <div className="reviews-summary__breakdown">
              {[5, 4, 3, 2, 1].map((stars) => {
                const count = summary.rating_breakdown?.[String(stars)] ?? 0
                const percent = totalReviews > 0 ? Math.round((count / totalReviews) * 100) : 0
                return (
                  <button
                    key={stars}
                    type="button"
                    className="reviews-breakdown-row"
                    onClick={() =>
                      setRatingFilter((prev) => (prev === stars ? null : stars))
                    }
                    title={`Pokaż opinie z oceną ${stars}★`}
                  >
                    <span className="reviews-breakdown-row__star">{stars} ★</span>
                    <div className="reviews-breakdown-row__track">
                      <div
                        className="reviews-breakdown-row__fill"
                        style={{ width: `${percent}%` }}
                      />
                    </div>
                    <span className="reviews-breakdown-row__count">{count}</span>
                  </button>
                )
              })}
            </div>
          </div>
        ) : null}

        {totalReviews > 0 ? (
          <div className="reviews-toolbar">
            <div className="reviews-filters" role="group" aria-label="Filtry ocen">
              <button
                type="button"
                className={`reviews-filter-btn ${ratingFilter === null ? 'reviews-filter-btn--active' : ''}`}
                onClick={() => setRatingFilter(null)}
              >
                Wszystkie ({totalReviews})
              </button>
              {[5, 4, 3, 2, 1].map((stars) => {
                const count = summary?.rating_breakdown?.[String(stars)] ?? 0
                if (count === 0) return null
                return (
                  <button
                    key={stars}
                    type="button"
                    className={`reviews-filter-btn ${ratingFilter === stars ? 'reviews-filter-btn--active' : ''}`}
                    onClick={() => setRatingFilter(stars)}
                  >
                    {stars} ★ ({count})
                  </button>
                )
              })}
            </div>

            <div className="reviews-sort">
              <span className="reviews-sort__label">Sortuj:</span>
              <Select
                value={ordering}
                onChange={(val) => setOrdering(val as '-created_at' | '-rating' | 'rating')}
                options={SORT_OPTIONS}
                ariaLabel="Sortuj opinie"
                className="reviews-sort__select-custom"
              />
            </div>
          </div>
        ) : null}

        {loading ? <LoadingBlock label="Ładowanie opinii pacjentów..." /> : null}

        {error ? <ErrorBanner message={error} /> : null}

        {!loading && !error && reviews.length === 0 ? (
          <EmptyState
            title={ratingFilter ? 'Brak opinii dla wybranej oceny' : 'Brak wystawionych opinii'}
            description={
              ratingFilter
                ? 'Spróbuj wybrać inny filtr gwiazdek lub zresetować filtr.'
                : 'Gdy pacjenci ocenią Twoje wizyty, ich opinie pojawią się w tym miejscu.'
            }
            action={
              ratingFilter ? (
                <Button variant="secondary" onClick={() => setRatingFilter(null)}>
                  Pokaż wszystkie opinie
                </Button>
              ) : undefined
            }
          />
        ) : null}

        {!loading && !error && reviews.length > 0 ? (
          <div className="reviews-list">
            {reviews.map((item) => (
              <article key={item.id} className="review-card">
                <header className="review-card__header">
                  <div className="review-card__author-group">
                    <ReviewAvatar item={item} />
                    <div className="review-card__author">
                      <div className="review-card__name-row">
                        <span className="review-card__author-name">{item.author_name}</span>
                        {item.is_verified ? (
                          <span
                            className="review-card__verified-badge"
                            title="Opinia po zrealizowanej wizycie"
                          >
                            ✓ Zweryfikowana wizyta
                          </span>
                        ) : null}
                      </div>
                      <span className="review-card__date">{formatReviewDate(item.created_at)}</span>
                    </div>
                  </div>
                  <div className="review-card__stars">
                    <StarRating rating={item.rating} size={15} />
                  </div>
                </header>

                {item.comment ? (
                  <p className="review-card__comment">{item.comment}</p>
                ) : (
                  <p className="review-card__empty-comment">
                    Pacjent ocenił wizytę bez komentarza tekstowego.
                  </p>
                )}

                {item.therapist_reply && replyingToId !== item.id ? (
                  <div className="review-card__reply">
                    <div className="review-card__reply-header">
                      <div className="review-reply__author-group">
                        <div className="review-reply__avatar" title={therapistFullName}>
                          {user?.avatar_url ? (
                            <AuthMediaImg
                              path={user.avatar_url}
                              alt={therapistFullName}
                              className="review-reply__avatar-img"
                            />
                          ) : null}
                          <span className="review-reply__avatar-fallback" aria-hidden="true">
                            {therapistInitials}
                          </span>
                        </div>
                        <div className="review-reply__meta">
                          <div className="review-reply__name-row">
                            <span className="review-reply__author-name">{therapistFullName}</span>
                            <span className="review-reply__badge">Fizjoterapeuta</span>
                          </div>
                          {item.therapist_replied_at ? (
                            <span className="review-card__reply-date">
                              {formatReviewDate(item.therapist_replied_at)}
                            </span>
                          ) : null}
                        </div>
                      </div>
                    </div>
                    <p className="review-card__reply-text">{item.therapist_reply}</p>
                    <div className="review-card__reply-actions">
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => startReplying(item)}
                      >
                        Edytuj odpowiedź
                      </Button>
                    </div>
                  </div>
                ) : null}

                {!item.therapist_reply && replyingToId !== item.id ? (
                  <div className="review-card__reply-actions">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => startReplying(item)}
                    >
                      Odpowiedz na opinię
                    </Button>
                  </div>
                ) : null}

                {replyingToId === item.id ? (
                  <div className="review-reply-form">
                    <label htmlFor={`reply-${item.id}`} className="review-card__reply-title">
                      {item.therapist_reply ? 'Edytuj odpowiedź na opinię:' : 'Napisz odpowiedź na opinię:'}
                    </label>
                    <textarea
                      id={`reply-${item.id}`}
                      className={`review-reply-form__textarea ${replyError ? 'review-reply-form__textarea--error' : ''}`.trim()}
                      placeholder="Dziękuję za opinię i zaufanie..."
                      value={replyDraft}
                      onChange={(e) => {
                        setReplyDraft(e.target.value)
                        if (replyError) setReplyError(null)
                      }}
                      rows={3}
                      disabled={replySubmitting}
                      aria-invalid={replyError ? true : undefined}
                      aria-describedby={replyError ? `reply-err-${item.id}` : undefined}
                    />
                    {replyError ? (
                      <p id={`reply-err-${item.id}`} className="review-reply-form__error" role="alert">
                        <svg
                          width="14"
                          height="14"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2.5"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          aria-hidden="true"
                        >
                          <circle cx="12" cy="12" r="10" />
                          <line x1="12" y1="8" x2="12" y2="12" />
                          <line x1="12" y1="16" x2="12.01" y2="16" />
                        </svg>
                        <span>{replyError}</span>
                      </p>
                    ) : null}
                    <div className="review-reply-form__actions">
                      <Button
                        type="button"
                        variant="secondary"
                        size="sm"
                        onClick={cancelReplying}
                        disabled={replySubmitting}
                      >
                        Anuluj
                      </Button>
                      <Button
                        type="button"
                        variant="primary"
                        size="sm"
                        onClick={() => handleSendReply(item.id)}
                        disabled={replySubmitting}
                      >
                        {replySubmitting ? 'Zapisywanie...' : 'Zapisz odpowiedź'}
                      </Button>
                    </div>
                  </div>
                ) : null}
              </article>
            ))}
          </div>
        ) : null}
      </div>
    </Modal>
  )
}
