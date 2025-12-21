import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Home } from './components/Home'
import { Login } from './components/Login'
import { Dashboard } from './components/Dashboard'
import { ErrorBoundary } from './components/ErrorBoundary'
import { OfflineBanner } from './components/OfflineBanner'
import { UserProvider } from './contexts/UserContext'
import { ConversationProvider } from './contexts/ConversationContext'
import { ToastProvider } from './contexts/ToastContext'
import './App.css'

// Protected Route Component
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = localStorage.getItem('keliva_authenticated');
  const hasToken = localStorage.getItem('keliva_token');
  const isGuest = localStorage.getItem('keliva_guest');
  
  // Allow access if user has JWT token or is guest
  if (!isAuthenticated || (!hasToken && !isGuest)) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
}

function App() {
  return (
    <ErrorBoundary>
      <ToastProvider>
        <Router>
          <Routes>
            {/* Landing Page */}
            <Route path="/" element={<Home />} />
            
            {/* Login/Register */}
            <Route path="/login" element={<Login />} />
            
            {/* Redirect old welcome to login */}
            <Route path="/welcome" element={<Navigate to="/login" replace />} />
            
            {/* Protected App Dashboard */}
            <Route 
              path="/app" 
              element={
                <ProtectedRoute>
                  <UserProvider>
                    <ConversationProvider>
                      <OfflineBanner />
                      <Dashboard />
                    </ConversationProvider>
                  </UserProvider>
                </ProtectedRoute>
              } 
            />
          </Routes>
        </Router>
      </ToastProvider>
    </ErrorBoundary>
  )
}

export default App
