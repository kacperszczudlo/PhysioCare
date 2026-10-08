import { useCallback, useEffect, useState } from 'react'

import { adminApi } from '@/api/admin'
import { getErrorMessage } from '@/api/client'
import type { AdminUserDetail, AdminUserListItem } from '@/api/types'
import { LoadingBlock } from '@/components/AsyncState'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Select } from '@/components/ui/Select'
import { useToast } from '@/components/ui/ToastContext'
import { IconEye, IconKey, IconLock, IconSearch, IconTrash, IconUnlock } from './AdminIcons'
import './AdminUsersPage.css'

const PAGE_SIZE = 20

function initials(first?: string, last?: string): string {
  const value = `${first?.charAt(0) ?? ''}${last?.charAt(0) ?? ''}`.toUpperCase()
  return value || '?'
}

/**
 * Widok zarządzania kontami użytkowników (pacjenci, fizjoterapeuci, administratorzy).
 * Obsługuje filtrowanie, blokowanie kont, reset hasła, podgląd szczegółów oraz procedurę RODO.
 */
export function AdminUsersPage() {
  const { toast } = useToast()
  const [users, setUsers] = useState<AdminUserListItem[]>([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [isLoading, setIsLoading] = useState(true)

  // Filtry
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<string>('')

  // Szczegóły wybranego użytkownika
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null)
  const [userDetail, setUserDetail] = useState<AdminUserDetail | null>(null)
  const [isLoadingDetail, setIsLoadingDetail] = useState(false)

  // Modal usunięcia / dezaktywacji
  const [userToDelete, setUserToDelete] = useState<AdminUserListItem | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  // Modal potwierdzenia wysyłki resetu hasła
  const [userToResetPassword, setUserToResetPassword] = useState<
    AdminUserListItem | AdminUserDetail | null
  >(null)
  const [isResettingPassword, setIsResettingPassword] = useState(false)

  const fetchUsers = useCallback(async () => {
    setIsLoading(true)
    try {
      const res = await adminApi.getUsers({
        search: search.trim() || undefined,
        role: roleFilter || undefined,
        is_active: statusFilter === '' ? undefined : statusFilter === 'active',
        page,
      })
      setUsers(res.results)
      setCount(res.count)
    } catch {
      toast.error('Nie udało się pobrać listy użytkowników.')
    } finally {
      setIsLoading(false)
    }
  }, [search, roleFilter, statusFilter, page, toast])

  useEffect(() => {
    void fetchUsers()
  }, [fetchUsers])

  const openUserDetail = async (userId: string) => {
    setSelectedUserId(userId)
    setIsLoadingDetail(true)
    try {
      const data = await adminApi.getUserDetail(userId)
      setUserDetail(data)
    } catch {
      toast.error('Nie udało się pobrać szczegółów użytkownika.')
      setSelectedUserId(null)
    } finally {
      setIsLoadingDetail(false)
    }
  }

  const handleToggleStatus = async (user: AdminUserListItem | AdminUserDetail) => {
    try {
      const updated = await adminApi.toggleUserStatus(user.id, !user.is_active)
      setUsers((prev) =>
        prev.map((u) => (u.id === user.id ? { ...u, is_active: updated.is_active } : u)),
      )
      if (userDetail && userDetail.id === user.id) {
        setUserDetail({ ...userDetail, is_active: updated.is_active })
      }
      toast.success(
        updated.is_active
          ? `Konto ${user.email} zostało odblokowane.`
          : `Konto ${user.email} zostało zablokowane.`,
      )
    } catch (err) {
      toast.error(getErrorMessage(err, 'Nie udało się zmienić statusu konta użytkownika.'))
    }
  }

  const handleConfirmResetPassword = async () => {
    if (!userToResetPassword) return
    setIsResettingPassword(true)
    try {
      await adminApi.resetUserPassword(userToResetPassword.id)
      toast.success(`Kod resetowania hasła został wysłany na adres ${userToResetPassword.email}.`)
      setUserToResetPassword(null)
    } catch (err) {
      toast.error(getErrorMessage(err, 'Wysyłka resetu hasła nie powiodła się.'))
    } finally {
      setIsResettingPassword(false)
    }
  }

  const handleConfirmDelete = async () => {
    if (!userToDelete) return
    setIsDeleting(true)
    try {
      await adminApi.softDeleteUser(userToDelete.id)
      toast.success(
        `Konto ${userToDelete.email} zostało pomyślnie usunięte i zanonimizowane (RODO).`,
      )
      setUserToDelete(null)
      void fetchUsers()
    } catch (err) {
      toast.error(getErrorMessage(err, 'Nie udało się usunąć użytkownika.'))
    } finally {
      setIsDeleting(false)
    }
  }

  const roleBadgeClass = (role: string) => {
    switch (role) {
      case 'ADMIN':
        return 'admin-badge admin-badge--admin'
      case 'THERAPIST':
        return 'admin-badge admin-badge--therapist'
      case 'PATIENT':
        return 'admin-badge admin-badge--patient'
      default:
        return 'admin-badge'
    }
  }

  const roleLabel = (role: string) => {
    switch (role) {
      case 'ADMIN':
        return 'Administrator'
      case 'THERAPIST':
        return 'Fizjoterapeuta (Web)'
      case 'PATIENT':
        return 'Pacjent (App)'
      default:
        return role
    }
  }

  return (
    <div className="admin-users-page">
      <PageHeader
        title="Zarządzanie Użytkownikami"
        description={`Łącznie ${count} zarejestrowanych kont w systemie PhysioCare.`}
      />

      {/* Pasek filtrów */}
      <div className="admin-filters-bar">
        <div className="admin-search-wrapper">
          <IconSearch className="admin-search-icon" />
          <input
            type="text"
            className="admin-input admin-input--search"
            placeholder="Szukaj po nazwisku lub e-mail..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setPage(1)
            }}
          />
        </div>

        <Select
          className="admin-filter-control"
          value={roleFilter}
          onChange={(val) => {
            setRoleFilter(val)
            setPage(1)
          }}
          options={[
            { value: '', label: 'Wszystkie role' },
            { value: 'PATIENT', label: 'Pacjenci' },
            { value: 'THERAPIST', label: 'Fizjoterapeuci' },
            { value: 'ADMIN', label: 'Administratorzy' },
          ]}
          ariaLabel="Filtruj według roli"
        />

        <Select
          className="admin-filter-control"
          value={statusFilter}
          onChange={(val) => {
            setStatusFilter(val)
            setPage(1)
          }}
          options={[
            { value: '', label: 'Wszystkie statusy' },
            { value: 'active', label: 'Tylko aktywni' },
            { value: 'blocked', label: 'Tylko zablokowani' },
          ]}
          ariaLabel="Filtruj według statusu"
        />
      </div>

      {/* Tabela użytkowników */}
      <div className="admin-table-container">
        {isLoading ? (
          <div className="admin-table-loading">
            <LoadingBlock label="Pobieranie listy użytkowników…" />
          </div>
        ) : users.length === 0 ? (
          <div className="admin-empty-state">
            <p>Nie znaleziono użytkowników spełniających podane kryteria.</p>
          </div>
        ) : (
          <div className="admin-table-scroll">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Użytkownik</th>
                  <th>Rola</th>
                  <th>Status</th>
                  <th>Data rejestracji</th>
                  <th className="admin-th-actions">Akcje</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id}>
                    <td>
                      <div className="admin-user-cell">
                        <span className="admin-user-avatar">
                          {initials(u.first_name, u.last_name)}
                        </span>
                        <div>
                          <div className="admin-user-name">
                            {u.first_name} {u.last_name}
                          </div>
                          <div className="admin-user-email">{u.email}</div>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className={roleBadgeClass(u.role)}>{roleLabel(u.role)}</span>
                    </td>
                    <td>
                      {u.is_active ? (
                        <span className="admin-status-pill admin-status-pill--active">
                          <span className="admin-status-dot" aria-hidden="true" />
                          <span>Aktywny</span>
                        </span>
                      ) : (
                        <span className="admin-status-pill admin-status-pill--blocked">
                          <span className="admin-status-dot" aria-hidden="true" />
                          <span>Zablokowany</span>
                        </span>
                      )}
                    </td>
                    <td className="admin-date-cell">
                      {new Date(u.created_at).toLocaleDateString('pl-PL')}
                    </td>
                    <td className="admin-td-actions">
                      <div className="admin-action-buttons">
                        <Button
                          variant="secondary"
                          size="sm"
                          className="admin-action-btn--icon-only"
                          onClick={() => void openUserDetail(u.id)}
                          title="Szczegóły konta"
                          aria-label={`Szczegóły konta ${u.first_name} ${u.last_name}`}
                        >
                          <IconEye />
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          className="admin-action-btn--icon-only"
                          onClick={() => void handleToggleStatus(u)}
                          title={u.is_active ? 'Zablokuj konto' : 'Odblokuj konto'}
                          aria-label={
                            u.is_active
                              ? `Zablokuj konto ${u.first_name} ${u.last_name}`
                              : `Odblokuj konto ${u.first_name} ${u.last_name}`
                          }
                        >
                          {u.is_active ? <IconLock /> : <IconUnlock />}
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          className="admin-action-btn--icon-only"
                          onClick={() => setUserToResetPassword(u)}
                          title="Wyślij kod resetu hasła"
                          aria-label={`Wyślij kod resetu hasła dla ${u.first_name} ${u.last_name}`}
                        >
                          <IconKey />
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          className="admin-action-btn--icon-only admin-action-btn--danger"
                          onClick={() => setUserToDelete(u)}
                          title="Usuń / zanonimizuj (RODO)"
                          aria-label={`Usuń konto użytkownika ${u.first_name} ${u.last_name}`}
                        >
                          <IconTrash />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Paginacja */}
        <div className="admin-pagination">
          <span className="admin-pagination__info">
            Strona {page} z {Math.max(1, Math.ceil(count / PAGE_SIZE))}
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
              disabled={page * PAGE_SIZE >= count}
              onClick={() => setPage((p) => p + 1)}
            >
              Następna
            </Button>
          </div>
        </div>
      </div>

      {/* Modal Szczegółów Użytkownika */}
      {selectedUserId && (
        <Modal
          open={true}
          title="Szczegóły Użytkownika"
          onClose={() => {
            setSelectedUserId(null)
            setUserDetail(null)
          }}
        >
          {isLoadingDetail || !userDetail ? (
            <LoadingBlock label="Ładowanie profilu…" />
          ) : (
            <div className="admin-modal-detail">
              <div className="admin-modal-header-profile">
                <span className="admin-user-avatar admin-user-avatar--lg">
                  {initials(userDetail.first_name, userDetail.last_name)}
                </span>
                <div>
                  <h3 className="admin-modal-user-name">
                    {userDetail.first_name} {userDetail.last_name}
                  </h3>
                  <p className="admin-modal-user-email">{userDetail.email}</p>
                  <span className={roleBadgeClass(userDetail.role)}>
                    {roleLabel(userDetail.role)}
                  </span>
                </div>
              </div>

              <div className="admin-detail-grid">
                <div className="admin-detail-item">
                  <span className="admin-detail-label">Status konta</span>
                  <span className="admin-detail-value">
                    {userDetail.is_active ? 'Aktywne' : 'Zablokowane'}
                  </span>
                </div>
                <div className="admin-detail-item">
                  <span className="admin-detail-label">Weryfikacja e-mail</span>
                  <span className="admin-detail-value">
                    {userDetail.email_verified ? 'Zweryfikowany' : 'Niezweryfikowany'}
                  </span>
                </div>
                <div className="admin-detail-item">
                  <span className="admin-detail-label">Uwierzytelnianie 2FA</span>
                  <span className="admin-detail-value">
                    {userDetail.has_mfa ? 'Aktywne (TOTP)' : 'Wyłączone'}
                  </span>
                </div>
                <div className="admin-detail-item">
                  <span className="admin-detail-label">Data utworzenia</span>
                  <span className="admin-detail-value">
                    {new Date(userDetail.created_at).toLocaleString('pl-PL')}
                  </span>
                </div>
              </div>

              {/* Sekcja profilu terapeuty */}
              {userDetail.role === 'THERAPIST' && userDetail.profile_info && (
                <div className="admin-detail-section">
                  <h4 className="admin-detail-section__title">Profil Fizjoterapeuty</h4>
                  <div className="admin-detail-grid">
                    <div className="admin-detail-item">
                      <span className="admin-detail-label">Numer PWZFz</span>
                      <span className="admin-detail-value">
                        {userDetail.profile_info.pwzf_number || 'Brak'}
                      </span>
                    </div>
                    <div className="admin-detail-item">
                      <span className="admin-detail-label">Kwalifikacja</span>
                      <span className="admin-detail-value">
                        {userDetail.profile_info.qualification_level || 'Brak'}
                      </span>
                    </div>
                    <div className="admin-detail-item">
                      <span className="admin-detail-label">Doświadczenie</span>
                      <span className="admin-detail-value">
                        {userDetail.profile_info.experience_years ?? 0} lat
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Sekcja profilu pacjenta */}
              {userDetail.role === 'PATIENT' && userDetail.profile_info && (
                <div className="admin-detail-section">
                  <h4 className="admin-detail-section__title">Profil Pacjenta</h4>
                  <div className="admin-detail-grid">
                    <div className="admin-detail-item">
                      <span className="admin-detail-label">Numer telefonu</span>
                      <span className="admin-detail-value">
                        {userDetail.profile_info.phone || 'Brak danych'}
                      </span>
                    </div>
                    <div className="admin-detail-item">
                      <span className="admin-detail-label">Liczba wizyt</span>
                      <span className="admin-detail-value">{userDetail.visits_count}</span>
                    </div>
                  </div>
                </div>
              )}

              <div className="admin-modal-actions">
                <Button variant="secondary" onClick={() => void handleToggleStatus(userDetail)}>
                  {userDetail.is_active ? 'Zablokuj konto' : 'Odblokuj konto'}
                </Button>
                <Button variant="ghost" onClick={() => setUserToResetPassword(userDetail)}>
                  Wyślij reset hasła
                </Button>
              </div>
            </div>
          )}
        </Modal>
      )}

      {/* Modal potwierdzenia wysłania resetu hasła */}
      {userToResetPassword && (
        <Modal
          open={true}
          title="Potwierdzenie wysłania resetu hasła"
          onClose={() => setUserToResetPassword(null)}
        >
          <div className="admin-modal-delete-content">
            <p className="admin-delete-warning">
              Czy na pewno chcesz wysłać kod resetowania hasła dla użytkownika{' '}
              <strong>{userToResetPassword.email}</strong>?
            </p>
            <p className="admin-delete-subtext">
              Na podany adres e-mail zostanie przesłany 6-cyfrowy kod weryfikacyjny, który umożliwi
              użytkownikowi bezpieczne ustawienie nowego hasła.
            </p>
            <div className="admin-modal-actions">
              <Button
                variant="secondary"
                disabled={isResettingPassword}
                onClick={() => setUserToResetPassword(null)}
              >
                Anuluj
              </Button>
              <Button
                variant="primary"
                loading={isResettingPassword}
                onClick={() => void handleConfirmResetPassword()}
              >
                Wyślij kod resetu
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Modal potwierdzenia usunięcia (RODO) */}
      {userToDelete && (
        <Modal
          open={true}
          title="Potwierdzenie Dezaktywacji Konta (RODO)"
          onClose={() => setUserToDelete(null)}
        >
          <div className="admin-modal-delete-content">
            <p className="admin-delete-warning">
              Czy na pewno chcesz dezaktywować i zanonimizować konto{' '}
              <strong>{userToDelete.email}</strong>?
            </p>
            <p className="admin-delete-subtext">
              Zgodnie z procedurą RODO dane osobowe (PII) zostaną zanonimizowane, a wszystkie sesje
              i tokeny zostaną unieważnione. Operacja jest nieodwracalna.
            </p>
            <div className="admin-modal-actions">
              <Button
                variant="secondary"
                disabled={isDeleting}
                onClick={() => setUserToDelete(null)}
              >
                Anuluj
              </Button>
              <Button
                variant="danger"
                loading={isDeleting}
                onClick={() => void handleConfirmDelete()}
              >
                Potwierdź dezaktywację
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}
