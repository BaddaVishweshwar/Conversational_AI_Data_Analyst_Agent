import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import LoginPage from './pages/LoginPage'
import LandingPage from './pages/LandingPage'
import DashboardPage from './pages/DashboardPage'
import AnalyticsPage from './pages/AnalyticsPage'
import DatasetPage from './pages/DatasetPage'
import ConnectionsPage from './pages/ConnectionsPage'
import AdminPage from './pages/AdminPage'
import { Toaster } from './components/ui/toaster'
import MainLayout from './components/MainLayout'
import { GoogleOAuthProvider } from '@react-oauth/google'
import ProtectedRoute from './components/ProtectedRoute'
import GetStartedPage from './pages/GetStartedPage'
import RegisterPage from './pages/RegisterPage'
import HistoryPage from './pages/HistoryPage'

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            refetchOnWindowFocus: false,
            retry: 1,
        },
    },
})

function App() {
    return (
        <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID || "PLACEHOLDER_CLIENT_ID"}>
            <QueryClientProvider client={queryClient}>
                <Router>
                    <Routes>
                        {/* Public Routes */}
                        <Route path="/login" element={<LoginPage />} />
                        <Route path="/register" element={<RegisterPage />} />
                        <Route path="/get-started" element={<GetStartedPage />} />

                        {/* Protected Routes (Wrapped in MainLayout and ProtectedRoute) */}
                        <Route path="/dashboard" element={<ProtectedRoute><MainLayout><DashboardPage /></MainLayout></ProtectedRoute>} />
                        <Route path="/analytics" element={<ProtectedRoute><MainLayout><AnalyticsPage /></MainLayout></ProtectedRoute>} />
                        <Route path="/datasets" element={<ProtectedRoute><MainLayout><DatasetPage /></MainLayout></ProtectedRoute>} />
                        <Route path="/connections" element={<ProtectedRoute><MainLayout><ConnectionsPage /></MainLayout></ProtectedRoute>} />
                        <Route path="/history" element={<ProtectedRoute><MainLayout><HistoryPage /></MainLayout></ProtectedRoute>} />
                        <Route path="/admin" element={<ProtectedRoute><AdminPage /></ProtectedRoute>} />

                        {/* Default Route */}
                        <Route path="/" element={<LandingPage />} />
                    </Routes>
                    <Toaster />
                </Router>
            </QueryClientProvider>
        </GoogleOAuthProvider>
    )
}

export default App
