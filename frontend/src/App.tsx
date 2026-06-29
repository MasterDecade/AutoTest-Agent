import { Routes, Route } from 'react-router-dom'
import MainLayout from './layouts/MainLayout'
import Dashboard from './pages/Dashboard'
import Projects from './pages/Projects'
import ProjectContent from './pages/ProjectContent'
import SubmitCode from './pages/SubmitCode'
import ReviewPlan from './pages/ReviewPlan'
import CompareScores from './pages/CompareScores'
import SettingsLLM from './pages/SettingsLLM'

function App() {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/projects" element={<Projects />} />
        <Route path="/projects/:projectId/content" element={<ProjectContent />} />
        <Route path="/projects/:projectId/submit" element={<SubmitCode />} />
        <Route path="/projects/:projectId/review" element={<ReviewPlan />} />
        <Route path="/projects/:projectId/compare" element={<CompareScores />} />
        <Route path="/settings/llm" element={<SettingsLLM />} />
      </Route>
    </Routes>
  )
}

export default App
