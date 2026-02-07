import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import UploadDetailPage from './pages/UploadDetailPage';
import StatsPage from './pages/StatsPage';
import AdminPage from './pages/AdminPage';
import SharedPage from './pages/SharedPage';
import StudyGroupPage from './pages/StudyGroupPage';

function PrivateRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  return user ? children : <Navigate to="/login" />;
}

function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/" element={<PrivateRoute><DashboardPage /></PrivateRoute>} />
            <Route path="/uploads/:id" element={<PrivateRoute><UploadDetailPage /></PrivateRoute>} />
            <Route path="/stats" element={<PrivateRoute><StatsPage /></PrivateRoute>} />
            <Route path="/admin" element={<PrivateRoute><AdminPage /></PrivateRoute>} />
            <Route path="/shared" element={<PrivateRoute><SharedPage /></PrivateRoute>} />
            <Route path="/groups" element={<PrivateRoute><StudyGroupPage /></PrivateRoute>} />
          </Routes>
        </BrowserRouter>
      </ThemeProvider>
    </AuthProvider>
  );
}

export default App;
