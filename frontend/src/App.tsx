import { useEffect, useState, type ReactNode } from 'react'
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useLocation,
  useParams,
} from 'react-router-dom'

import { AppLayout } from './layouts/AppLayout'
import { AssessmentPage } from './pages/AssessmentPage'
import { AssessmentsPage } from './pages/AssessmentsPage'
import { CounsellorDashboardPage } from './pages/CounsellorDashboardPage'
import { CounsellorSessionPage } from './pages/CounsellorSessionPage'
import { HomePage } from './pages/HomePage'
import { LoginPage } from './pages/LoginPage'
import { PortalPage } from './pages/PortalPage'
import { ResultsPage } from './pages/ResultsPage'
import { StudentHistoryPage } from './pages/StudentHistoryPage'
import { api, getAccessToken } from './services/api'
import type { User, UserRole } from './types/auth'

type RoleProtectedRouteProps = {
  role: UserRole
  children: ReactNode
}

function RoleProtectedRoute({
  role,
  children,
}: RoleProtectedRouteProps) {
  const location = useLocation()
  const [user, setUser] = useState<User | null>(null)
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    let active = true

    async function checkAccess() {
      const token = getAccessToken()

      if (!token) {
        if (active) {
          setChecking(false)
        }
        return
      }

      try {
        const response = await api.get<User>('/auth/me', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })

        if (active) {
          setUser(response.data)
        }
      } catch {
        if (active) {
          setUser(null)
        }
      } finally {
        if (active) {
          setChecking(false)
        }
      }
    }

    void checkAccess()

    return () => {
      active = false
    }
  }, [location.pathname])

  if (checking) {
    return (
      <div className="rounded-xl border bg-white p-6 text-slate-600">
        Checking access...
      </div>
    )
  }

  if (!user) {
    return <Navigate to={`/login/${role}`} replace state={{ from: location.pathname }} />
  }

  if (user.role !== role) {
    return <Navigate to={`/portal/${user.role}`} replace />
  }

  return <>{children}</>
}

function PortalRoute() {
  const { role } = useParams<{ role: UserRole }>()

  if (role !== 'student' && role !== 'counsellor') {
    return <Navigate to="/" replace />
  }

  return (
    <RoleProtectedRoute role={role}>
      <PortalPage />
    </RoleProtectedRoute>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<HomePage />} />

          <Route path="login/:role" element={<LoginPage />} />

          <Route path="portal/:role" element={<PortalRoute />} />

          <Route
            path="assessments"
            element={
              <RoleProtectedRoute role="student">
                <AssessmentsPage />
              </RoleProtectedRoute>
            }
          />

          <Route
            path="assessments/:assessmentId"
            element={
              <RoleProtectedRoute role="student">
                <AssessmentPage />
              </RoleProtectedRoute>
            }
          />

          <Route
            path="results/:sessionId"
            element={
              <RoleProtectedRoute role="student">
                <ResultsPage />
              </RoleProtectedRoute>
            }
          />

          <Route
            path="counsellor"
            element={
              <RoleProtectedRoute role="counsellor">
                <CounsellorDashboardPage />
              </RoleProtectedRoute>
            }
          />

          <Route
            path="counsellor/students/:studentId"
            element={
              <RoleProtectedRoute role="counsellor">
                <StudentHistoryPage />
              </RoleProtectedRoute>
            }
          />

          <Route
            path="counsellor/sessions/:sessionId"
            element={
              <RoleProtectedRoute role="counsellor">
                <CounsellorSessionPage />
              </RoleProtectedRoute>
            }
          />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
