import { useCallback, useEffect, useState } from 'react'

import { adminApi } from '@/api/admin'
import { getErrorMessage } from '@/api/client'
import type { AdminConsent, AdminPrivacyRequest } from '@/api/types'
import { LoadingBlock } from '@/components/AsyncState'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Select } from '@/components/ui/Select'
import { useToast } from '@/components/ui/ToastContext'
import { IconSearch, IconShield } from './AdminIcons'
import './AdminPrivacyPage.css'
import './AdminUsersPage.css'

const PAGE_SIZE = 20

type ActiveTab = 'requests' | 'consents'

export function AdminPrivacyPage() {
  const { toast } = useToast()
  const [activeTab, setActiveTab] = useState<ActiveTab>('requests')

  // Stan Wniosków RODO
  const [requests, setRequests] = useState<AdminPrivacyRequest[]>([])
  const [requestsCount, setRequestsCount] = useState(0)
  const [requestsPage, setRequestsPage] = useState(1)
  const [requestsLoading, setRequestsLoading] = useState(true)
  const [requestsSearch, setRequestsSearch] = useState('')
  const [processedFilter, setProcessedFilter] = useState<string>('')

  // Stan Zgód RODO
  const [consents, setConsents] = useState<AdminConsent[]>([])
  const [consentsCount, setConsentsCount] = useState(0)
  const [consentsPage, setConsentsPage] = useState(1)
  const [consentsLoading, setConsentsLoading] = useState(true)
  const [consentsSearch, setConsentsSearch] = useState('')
  const [consentTypeFilter, setConsentTypeFilter] = useState<string>('')
  const [grantedFilter, setGrantedFilter] = useState<string>('')

  // Modal przetwarzania wniosku
  const [selectedRequest, setSelectedRequest] = useState<AdminPrivacyRequest | null>(null)
  const [adminNotes, setAdminNotes] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)

  // Pobieranie wniosków
  const fetchRequests = useCallback(async () => {
    setRequestsLoading(true)
    try {
      const res = await adminApi.getPrivacyRequests({
        is_processed: processedFilter === '' ? undefined : processedFilter === 'processed',
        search: requestsSearch || undefined,
        page: requestsPage,
      })
      setRequests(res.results)
      setRequestsCount(res.count)
    } catch (err) {
      toast.error(getErrorMessage(err, 'Nie udało się pobrać listy wniosków RODO.'))
    } finally {
      setRequestsLoading(false)
    }
  }, [processedFilter, requestsSearch, requestsPage, toast])

  // Pobieranie zgód
  const fetchConsents = useCallback(async () => {
    setConsentsLoading(true)
    try {
      const res = await adminApi.getConsents({
        consent_type: consentTypeFilter || undefined,
        granted: grantedFilter === '' ? undefined : grantedFilter === 'granted',
        search: consentsSearch || undefined,
        page: consentsPage,
      })
      setConsents(res.results)
      setConsentsCount(res.count)
    } catch (err) {
      toast.error(getErrorMessage(err, 'Nie udało się pobrać rejestru zgód pacjentów.'))
    } finally {
      setConsentsLoading(false)
    }
  }, [consentTypeFilter, grantedFilter, consentsSearch, consentsPage, toast])

  useEffect(() => {
    if (activeTab === 'requests') {
      void fetchRequests()
    } else {
      void fetchConsents()
    }
  }, [activeTab, fetchRequests, fetchConsents])

  const handleOpenProcessModal = (req: AdminPrivacyRequest) => {
    setSelectedRequest(req)
    setAdminNotes('')
  }

  const handleConfirmProcess = async () => {
    if (!selectedRequest) return
    setIsProcessing(true)
    try {
      await adminApi.processPrivacyRequest(selectedRequest.id, adminNotes)
      toast.success(
        `Wniosek użytkownika ${selectedRequest.user_email} został pomyślnie zrealizowany. Dane osobowe zanonimizowano.`,
      )
      setSelectedRequest(null)
      void fetchRequests()
    } catch (err) {
      toast.error(getErrorMessage(err, 'Nie udało się zrealizować wniosku usunięcia konta.'))
    } finally {
      setIsProcessing(false)
    }
  }

  const totalRequestsPages = Math.ceil(requestsCount / PAGE_SIZE) || 1
  const totalConsentsPages = Math.ceil(consentsCount / PAGE_SIZE) || 1

  return (
    <div className="admin-privacy-page">
      <PageHeader
        title="RODO i Zarządzanie Prywatnością"
        description="Obsługa wniosków o usunięcie konta (Art. 17 RODO - Prawo do bycia zapomnianym) oraz audyt zgód pacjentów (Art. 7 RODO)."
      />

      {/* Zakładki */}
      <div className="admin-privacy-tabs" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'requests'}
          className={`admin-privacy-tab ${
            activeTab === 'requests' ? 'admin-privacy-tab--active' : ''
          }`}
          onClick={() => setActiveTab('requests')}
        >
          <IconShield />
          <span>Wnioski o usunięcie konta ({requestsCount})</span>
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'consents'}
          className={`admin-privacy-tab ${
            activeTab === 'consents' ? 'admin-privacy-tab--active' : ''
          }`}
          onClick={() => setActiveTab('consents')}
        >
          <span>Rejestr zgód pacjentów ({consentsCount})</span>
        </button>
      </div>

      {activeTab === 'requests' ? (
        <>
          {/* Pasek filtrów wniosków */}
          <div className="admin-privacy-filters">
            <div className="admin-search-wrapper">
              <IconSearch className="admin-search-icon" />
              <input
                type="text"
                className="admin-input admin-input--search"
                placeholder="Szukaj po e-mailu, nazwisku lub powodzie..."
                value={requestsSearch}
                onChange={(e) => {
                  setRequestsSearch(e.target.value)
                  setRequestsPage(1)
                }}
              />
            </div>

            <Select
              className="admin-filter-control"
              value={processedFilter}
              onChange={(val) => {
                setProcessedFilter(val)
                setRequestsPage(1)
              }}
              options={[
                { value: '', label: 'Wszystkie wnioski' },
                { value: 'pending', label: 'Tylko oczekujące' },
                { value: 'processed', label: 'Tylko zrealizowane' },
              ]}
            />
          </div>

          {/* Tabela wniosków */}
          <div className="admin-table-container">
            {requestsLoading ? (
              <LoadingBlock label="Ładowanie wniosków RODO…" variant="panel" />
            ) : (
              <div className="admin-table-scroll">
                <table className="admin-table">
                  <thead>
                    <tr>
                      <th>Wnioskodawca</th>
                      <th>Powód rezygnacji</th>
                      <th>Data zgłoszenia</th>
                      <th>Status</th>
                      <th className="admin-th-actions">Akcje</th>
                    </tr>
                  </thead>
                  <tbody>
                    {requests.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="admin-td-empty">
                          Brak wniosków o usunięcie konta w wybranym filtrze.
                        </td>
                      </tr>
                    ) : (
                      requests.map((r) => (
                        <tr key={r.id}>
                          <td>
                            <div className="admin-user-cell">
                              <div>
                                {r.user_full_name &&
                                r.user_full_name !== 'Usunięte Konto' &&
                                r.user_full_name !== '(Użytkownik)' ? (
                                  <>
                                    <div className="admin-user-name">{r.user_full_name}</div>
                                    <div className="admin-user-email">{r.user_email}</div>
                                  </>
                                ) : (
                                  <div className="admin-user-name">{r.user_email}</div>
                                )}
                              </div>
                            </div>
                          </td>
                          <td className="admin-reason-cell" title={r.reason || 'Brak uzasadnienia'}>
                            {r.reason || <span className="text-muted">(Brak uzasadnienia)</span>}
                          </td>
                          <td className="admin-date-cell">
                            {new Date(r.created_at).toLocaleDateString('pl-PL')}
                          </td>
                          <td>
                            {r.is_processed ? (
                              <span
                                className="admin-status-pill admin-status-pill--active"
                                title={
                                  r.processed_at
                                    ? `Data realizacji: ${new Date(r.processed_at).toLocaleString('pl-PL')}`
                                    : undefined
                                }
                              >
                                <span className="admin-status-dot" aria-hidden="true" />
                                <span>Zrealizowany</span>
                                {r.processed_at && (
                                  <span className="admin-status-pill__date">
                                    · {new Date(r.processed_at).toLocaleDateString('pl-PL')}
                                  </span>
                                )}
                              </span>
                            ) : (
                              <span className="admin-status-pill admin-status-pill--pending">
                                <span className="admin-status-dot" aria-hidden="true" />
                                <span>Oczekuje na realizację</span>
                              </span>
                            )}
                          </td>
                          <td className="admin-td-actions">
                            {!r.is_processed && (
                              <Button
                                variant="secondary"
                                size="sm"
                                onClick={() => handleOpenProcessModal(r)}
                                title="Zrealizuj usunięcie konta i anonimizację danych"
                              >
                                Zrealizuj (RODO)
                              </Button>
                            )}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {/* Paginacja wniosków */}
            {requestsCount > 0 && (
              <div className="admin-pagination">
                <span className="admin-pagination__info">
                  Strona {requestsPage} z {Math.max(1, totalRequestsPages)}
                </span>
                <div className="admin-pagination__controls">
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={requestsPage <= 1}
                    onClick={() => setRequestsPage((p) => Math.max(1, p - 1))}
                  >
                    Poprzednia
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={requestsPage >= totalRequestsPages}
                    onClick={() => setRequestsPage((p) => p + 1)}
                  >
                    Następna
                  </Button>
                </div>
              </div>
            )}
          </div>
        </>
      ) : (
        <>
          {/* Pasek filtrów zgód */}
          <div className="admin-privacy-filters">
            <div className="admin-search-wrapper">
              <IconSearch className="admin-search-icon" />
              <input
                type="text"
                className="admin-input admin-input--search"
                placeholder="Szukaj po e-mailu lub nazwisku..."
                value={consentsSearch}
                onChange={(e) => {
                  setConsentsSearch(e.target.value)
                  setConsentsPage(1)
                }}
              />
            </div>

            <Select
              className="admin-filter-control"
              value={consentTypeFilter}
              onChange={(val) => {
                setConsentTypeFilter(val)
                setConsentsPage(1)
              }}
              options={[
                { value: '', label: 'Wszystkie typy zgód' },
                { value: 'TERMS_REQUIRED', label: 'Regulamin (wymagany)' },
                { value: 'MEDICAL_DATA_REQUIRED', label: 'Dane medyczne (wymagany)' },
                { value: 'MARKETING_OPTIONAL', label: 'Marketing (opcjonalny)' },
                { value: 'RESEARCH_OPTIONAL', label: 'Badania (opcjonalny)' },
              ]}
            />

            <Select
              className="admin-filter-control"
              value={grantedFilter}
              onChange={(val) => {
                setGrantedFilter(val)
                setConsentsPage(1)
              }}
              options={[
                { value: '', label: 'Wszystkie statusy' },
                { value: 'granted', label: 'Zgoda udzielona' },
                { value: 'revoked', label: 'Brak zgody / wycofana' },
              ]}
            />
          </div>

          {/* Tabela zgód */}
          <div className="admin-table-container">
            {consentsLoading ? (
              <LoadingBlock label="Ładowanie rejestru zgód…" variant="panel" />
            ) : (
              <div className="admin-table-scroll">
                <table className="admin-table">
                  <thead>
                    <tr>
                      <th>Użytkownik</th>
                      <th>Typ zgody</th>
                      <th>Status zgody</th>
                      <th>Data wyrażenia zgody</th>
                    </tr>
                  </thead>
                  <tbody>
                    {consents.length === 0 ? (
                      <tr>
                        <td colSpan={4} className="admin-td-empty">
                          Brak wpisów w rejestrze zgód dla wybranych filtrów.
                        </td>
                      </tr>
                    ) : (
                      consents.map((c) => (
                        <tr key={c.id}>
                          <td>
                            <div className="admin-user-cell">
                              <div>
                                <div className="admin-user-name">{c.user_full_name}</div>
                                <div className="admin-user-email">{c.user_email}</div>
                              </div>
                            </div>
                          </td>
                          <td>
                            <span className="admin-badge admin-badge--therapist">
                              {c.consent_type_display}
                            </span>
                          </td>
                          <td>
                            {c.granted ? (
                              <span className="admin-status-pill admin-status-pill--active">
                                <span className="admin-status-dot" aria-hidden="true" />
                                <span>Udzielona</span>
                              </span>
                            ) : (
                              <span className="admin-status-pill admin-status-pill--blocked">
                                <span className="admin-status-dot" aria-hidden="true" />
                                <span>Brak zgody</span>
                              </span>
                            )}
                          </td>
                          <td className="admin-date-cell">
                            {new Date(c.granted_at).toLocaleString('pl-PL')}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {/* Paginacja zgód */}
            {consentsCount > 0 && (
              <div className="admin-pagination">
                <span className="admin-pagination__info">
                  Strona {consentsPage} z {Math.max(1, totalConsentsPages)}
                </span>
                <div className="admin-pagination__controls">
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={consentsPage <= 1}
                    onClick={() => setConsentsPage((p) => Math.max(1, p - 1))}
                  >
                    Poprzednia
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={consentsPage >= totalConsentsPages}
                    onClick={() => setConsentsPage((p) => p + 1)}
                  >
                    Następna
                  </Button>
                </div>
              </div>
            )}
          </div>
        </>
      )}

      {/* Modal realizacji wniosku RODO */}
      {selectedRequest && (
        <Modal
          open={true}
          title="Potwierdzenie Realizacji Wniosku RODO (Art. 17)"
          onClose={() => setSelectedRequest(null)}
        >
          <div className="admin-modal-delete-content">
            <p className="admin-delete-warning">
              Czy na pewno chcesz zrealizować wniosek o usunięcie konta dla{' '}
              <strong>{selectedRequest.user_email}</strong>?
            </p>
            <p className="admin-delete-subtext">
              Wykonanie tej operacji spowoduje trwałą anonimizację danych osobowych pacjenta
              (wyczyszczenie PESEL, numeru telefonu, podmianę e-mail na hash, dezaktywację konta
              oraz unieważnienie wszystkich sesji i tokenów push). Operacja ta jest{' '}
              <strong>nieodwracalna</strong>.
            </p>

            <div className="admin-modal-notes-field">
              <label htmlFor="admin-process-notes">
                Notatki z weryfikacji tożsamości (opcjonalnie):
              </label>
              <textarea
                id="admin-process-notes"
                placeholder="Np. Zweryfikowano telefonicznie wniosek pacjenta..."
                value={adminNotes}
                onChange={(e) => setAdminNotes(e.target.value)}
              />
            </div>

            {selectedRequest.notes && (
              <div className="admin-modal-notes-preview">
                <span className="admin-modal-notes-label">Wewnętrzne notatki systemowe:</span>
                <p className="admin-modal-notes-text">{selectedRequest.notes}</p>
              </div>
            )}

            <div className="admin-modal-actions">
              <Button
                variant="secondary"
                disabled={isProcessing}
                onClick={() => setSelectedRequest(null)}
              >
                Anuluj
              </Button>
              <Button
                variant="primary"
                loading={isProcessing}
                onClick={() => void handleConfirmProcess()}
              >
                Zrealizuj usunięcie (Anonimizacja)
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}

