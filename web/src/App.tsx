import { lazy, Suspense } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { AuthProvider } from '@/auth/AuthContext'
import { GuestRoute, ProtectedRoute } from '@/auth/ProtectedRoute'
import { LoadingBlock } from '@/components/AsyncState'
import { ToastContainer } from '@/components/ui/ToastContainer'
import { ToastProvider } from '@/components/ui/ToastContext'
import { AppLayout } from '@/layouts/AppLayout'
import { AuthLayout } from '@/layouts/AuthLayout'
import { LegalLayout } from '@/layouts/LegalLayout'

// Podział paczki aplikacji (Route-based code splitting i leniwe ładowanie widoków)
const AccountDeletionPage = lazy(() =>
  import('@/pages/AccountDeletionPage').then((m) => ({ default: m.AccountDeletionPage }))
)
const CookiePolicyPage = lazy(() =>
  import('@/pages/CookiePolicyPage').then((m) => ({ default: m.CookiePolicyPage }))
)
const DashboardPage = lazy(() =>
  import('@/pages/DashboardPage').then((m) => ({ default: m.DashboardPage }))
)
const EmailVerifyPage = lazy(() =>
  import('@/pages/EmailVerifyPage').then((m) => ({ default: m.EmailVerifyPage }))
)
const ExercisesPage = lazy(() =>
  import('@/pages/ExercisesPage').then((m) => ({ default: m.ExercisesPage }))
)
const LoginPage = lazy(() =>
  import('@/pages/LoginPage').then((m) => ({ default: m.LoginPage }))
)
const PasswordResetPage = lazy(() =>
  import('@/pages/PasswordResetPage').then((m) => ({ default: m.PasswordResetPage }))
)
const PatientDetailPage = lazy(() =>
  import('@/pages/PatientDetailPage').then((m) => ({ default: m.PatientDetailPage }))
)
const PatientsPage = lazy(() =>
  import('@/pages/PatientsPage').then((m) => ({ default: m.PatientsPage }))
)
const PrivacyPolicyPage = lazy(() =>
  import('@/pages/PrivacyPolicyPage').then((m) => ({ default: m.PrivacyPolicyPage }))
)
const ProfilePage = lazy(() =>
  import('@/pages/ProfilePage').then((m) => ({ default: m.ProfilePage }))
)
const RegisterPage = lazy(() =>
  import('@/pages/RegisterPage').then((m) => ({ default: m.RegisterPage }))
)
const SchedulePage = lazy(() =>
  import('@/pages/SchedulePage').then((m) => ({ default: m.SchedulePage }))
)
const SettingsPage = lazy(() =>
  import('@/pages/SettingsPage').then((m) => ({ default: m.SettingsPage }))
)

function RouteLoadingFallback() {
  return (
    <div
      style={{
        display: 'grid',
        placeItems: 'center',
        minHeight: '50vh',
        padding: '2rem',
      }}
    >
      <LoadingBlock label="Ładowanie…" variant="panel" />
    </div>
  )
}

/**
 * Główny komponent widoku z konfiguracją trasowania React Router v6, leniwym ładowaniem tras
 * i dostawców kontekstu (AuthProvider, ToastProvider).
 */
export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <BrowserRouter>
          <ToastContainer />
          <Suspense fallback={<RouteLoadingFallback />}>
            <Routes>
              <Route element={<LegalLayout />}>
                <Route path="/privacy" element={<PrivacyPolicyPage />} />
                <Route path="/cookies" element={<CookiePolicyPage />} />
                <Route path="/account-deletion" element={<AccountDeletionPage />} />
              </Route>

              <Route element={<GuestRoute />}>
                <Route element={<AuthLayout />}>
                  <Route path="/login" element={<LoginPage />} />
                  <Route path="/register" element={<RegisterPage />} />
                  <Route path="/verify-email" element={<EmailVerifyPage />} />
                  <Route path="/password-reset" element={<PasswordResetPage />} />
                  <Route path="/reset" element={<PasswordResetPage />} />
                </Route>
              </Route>

              <Route element={<ProtectedRoute />}>
                <Route element={<AppLayout />}>
                  <Route index element={<DashboardPage />} />
                  <Route path="/schedule" element={<SchedulePage />} />
                  <Route path="/patients" element={<PatientsPage />} />
                  <Route path="/patients/:patientId" element={<PatientDetailPage />} />
                  <Route path="/exercises" element={<ExercisesPage />} />
                  <Route path="/profile" element={<ProfilePage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                </Route>
              </Route>

              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </AuthProvider>
    </ToastProvider>
  )
}
