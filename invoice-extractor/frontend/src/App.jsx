import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/layout/Layout'
import UploadPage from './pages/UploadPage'
import DashboardPage from './pages/DashboardPage'
import ReviewPage from './pages/ReviewPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/upload" replace />} />
        <Route path="upload" element={<UploadPage />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="review" element={<ReviewPage />} />
        <Route path="review/:id" element={<ReviewPage />} />
      </Route>
    </Routes>
  )
}