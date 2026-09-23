import { Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { useThemeStore } from '@/stores/theme-store'
import DashboardLayout from '@/components/layout/DashboardLayout'
import LandingPage from '@/pages/LandingPage'
import DashboardHome from '@/pages/DashboardHome'
import DocumentsPage from '@/pages/DocumentsPage'
import AskPage from '@/pages/AskPage'
import CollectionsPage from '@/pages/CollectionsPage'
import EvaluationPage from '@/pages/EvaluationPage'
import AnalyticsPage from '@/pages/AnalyticsPage'
import SettingsPage from '@/pages/SettingsPage'

export default function App() {
  const { theme } = useThemeStore()

  useEffect(() => {
    const root = document.documentElement
    if (theme === 'dark') {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
  }, [theme])

  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/dashboard" element={<DashboardLayout />}>
        <Route index element={<DashboardHome />} />
        <Route path="documents" element={<DocumentsPage />} />
        <Route path="ask" element={<AskPage />} />
        <Route path="collections" element={<CollectionsPage />} />
        <Route path="evaluation" element={<EvaluationPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
