import { useCallback, useEffect, useState } from 'react'

import { adminApi } from '@/api/admin'
import type { AdminReview } from '@/api/types'
import { LoadingBlock } from '@/components/AsyncState'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/Button'
import { Select } from '@/components/ui/Select'
import { useToast } from '@/components/ui/ToastContext'
import { IconStar } from './AdminIcons'
import './AdminReviewsPage.css'

function RatingStars({ rating }: { rating: number }) {
  return (
    <div className="admin-stars-row" aria-label={`Ocena: ${rating} na 5`}>
      {[1, 2, 3, 4, 5].map((i) => (
        <IconStar
          key={i}
          className={`admin-star ${i <= rating ? 'admin-star--filled' : 'admin-star--empty'}`}
        />
      ))}
    </div>
  )
}

export function AdminReviewsPage() {
  const { toast } = useToast()
  const [reviews, setReviews] = useState<AdminReview[]>([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [isLoading, setIsLoading] = useState(true)

  // Filtry
  const [ratingFilter, setRatingFilter] = useState<string>('')
  const [visibilityFilter, setVisibilityFilter] = useState<string>('')

  const fetchReviews = useCallback(async () => {
    setIsLoading(true)
    try {
      const res = await adminApi.getReviews({
        rating: ratingFilter ? Number(ratingFilter) : undefined,
        is_visible: visibilityFilter === '' ? undefined : visibilityFilter === 'visible',
        page,
      })
      setReviews(res.results)
      setCount(res.count)
    } catch {
      toast.error('Nie udało się pobrać listy opinii.')
    } finally {
      setIsLoading(false)
    }
  }, [ratingFilter, visibilityFilter, page, toast])

  useEffect(() => {
    void fetchReviews()
  }, [fetchReviews])

  const handleToggleVisibility = async (review: AdminReview) => {
    try {
      const updated = await adminApi.toggleReviewVisibility(review.id, !review.is_visible)
      setReviews((prev) =>
        prev.map((r) => (r.id === review.id ? { ...r, is_visible: updated.is_visible } : r)),
      )
      toast.success(
        updated.is_visible
          ? 'Opinia jest teraz widoczna publicznie.'
          : 'Opinia została ukryta przed pacjentami (zmoderowana).',
      )
    } catch {
      toast.error('Nie udało się zmienić widoczności opinii.')
    }
  }

  return (
    <div className="admin-reviews-page">
      <PageHeader
        title="Moderacja Opinii Pacjentów"
        description={`Łącznie ${count} recenzji w systemie. Monitoruj jakość obsługi i zarządzaj widocznością komentarzy.`}
      />

      {/* Pasek filtrów */}
      <div className="admin-reviews-filters">
        <Select
          className="admin-filter-control"
          value={ratingFilter}
          onChange={(val) => {
            setRatingFilter(val)
            setPage(1)
          }}
          options={[
            { value: '', label: 'Wszystkie oceny' },
            { value: '5', label: '5 / 5 punktów' },
            { value: '4', label: '4 / 5 punktów' },
            { value: '3', label: '3 / 5 punktów' },
            { value: '2', label: '2 / 5 punktów' },
            { value: '1', label: '1 / 5 punktów' },
          ]}
          ariaLabel="Filtruj według oceny"
        />

        <Select
          className="admin-filter-control"
          value={visibilityFilter}
          onChange={(val) => {
            setVisibilityFilter(val)
            setPage(1)
          }}
          options={[
            { value: '', label: 'Wszystkie statusy' },
            { value: 'visible', label: 'Tylko widoczne publicznie' },
            { value: 'hidden', label: 'Ukryte przez moderatora' },
          ]}
          ariaLabel="Filtruj według statusu moderacji"
        />
      </div>

      {isLoading ? (
        <LoadingBlock label="Ładowanie opinii…" />
      ) : reviews.length === 0 ? (
        <div className="admin-reviews-empty">
          <p>Brak opinii spełniających wybrane kryteria.</p>
        </div>
      ) : (
        <div className="admin-reviews-list">
          {reviews.map((r) => (
            <div key={r.id} className="admin-review-card">
              <div className="admin-review-card__header">
                <div className="admin-review-card__author-info">
                  <h3 className="admin-review-card__author">{r.patient_name}</h3>
                  <span className="admin-review-card__therapist">
                    dla: <strong>{r.therapist_name}</strong>
                  </span>
                  <span className="admin-review-card__date">
                    {new Date(r.created_at).toLocaleDateString('pl-PL')}
                  </span>
                </div>

                <div className="admin-review-card__rating-col">
                  <RatingStars rating={r.rating} />
                  <span className="admin-review-card__score">{r.rating} / 5</span>
                </div>
              </div>

              {r.comment && (
                <div className="admin-review-card__body">
                  <p className="admin-review-card__comment">&ldquo;{r.comment}&rdquo;</p>
                </div>
              )}

              {r.therapist_reply && (
                <div className="admin-review-card__reply">
                  <span className="admin-review-card__reply-label">
                    Odpowiedź fizjoterapeuty ({r.therapist_name}):
                  </span>
                  <p className="admin-review-card__reply-text">{r.therapist_reply}</p>
                </div>
              )}

              <div className="admin-review-card__footer">
                <div className="admin-review-card__status">
                  Status widoczności:{' '}
                  {r.is_visible ? (
                    <span className="admin-status-pill admin-status-pill--active">
                      <span className="admin-status-dot" /> Widoczna publicznie
                    </span>
                  ) : (
                    <span className="admin-status-pill admin-status-pill--blocked">
                      <span className="admin-status-dot" /> Ukryta (zmoderowana)
                    </span>
                  )}
                </div>

                <Button
                  variant={r.is_visible ? 'secondary' : 'primary'}
                  size="sm"
                  onClick={() => void handleToggleVisibility(r)}
                >
                  {r.is_visible ? 'Ukryj opinię' : 'Przywróć widoczność'}
                </Button>
              </div>
            </div>
          ))}

          {/* Paginacja */}
          <div className="admin-pagination">
            <span className="admin-pagination__info">
              Strona {page} z {Math.max(1, Math.ceil(count / 20))}
            </span>
            <div className="admin-pagination__controls">
              <Button
                variant="secondary"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Poprzednia
              </Button>
              <Button
                variant="secondary"
                size="sm"
                disabled={page * 20 >= count}
                onClick={() => setPage((p) => p + 1)}
              >
                Następna
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
