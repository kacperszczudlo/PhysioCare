import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { AuthProvider } from '@/auth/AuthContext'
import { GuestRoute, ProtectedRoute } from '@/auth/ProtectedRoute'
import { AppLayout } from '@/layouts/AppLayout'
import { AuthLayout } from '@/layouts/AuthLayout'
import { LegalLayout } from '@/layouts/LegalLayout'
import { AccountDeletionPage } from '@/pages/AccountDeletionPage'
import { CookiePolicyPage } from '@/pages/CookiePolicyPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { ExercisesPage } from '@/pages/ExercisesPage'
import { LoginPage } from '@/pages/LoginPage'
import { PasswordResetPage } from '@/pages/PasswordResetPage'
import { PatientDetailPage } from '@/pages/PatientDetailPage'
import { PatientsPage } from '@/pages/PatientsPage'
import { PrivacyPolicyPage } from '@/pages/PrivacyPolicyPage'
import { ProfilePage } from '@/pages/ProfilePage'
import { RegisterPage } from '@/pages/RegisterPage'
import { SchedulePage } from '@/pages/SchedulePage'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
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
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
