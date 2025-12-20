import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AppThemeProvider } from '@/theme/theme';
import { AppShell } from '@/components/layout/AppShell';
import { useAuthStore } from '@/stores/authStore';
import { Login } from '@/pages/Login';
import { Register } from '@/pages/Register';
import { Dashboard } from '@/pages/Dashboard';
import { Schemas } from '@/pages/Schemas';
import { Metadata } from '@/pages/Metadata';
import { AssetTypes } from '@/pages/AssetTypes';
import { Analytics } from '@/pages/Analytics';
import { Users } from '@/pages/Users';
import { Box, Typography } from '@mui/material';

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated());
  return isAuthenticated ? children : <Navigate to="/login" />;
};

const PublicRoute = ({ children }: { children: React.ReactNode }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated());
  return !isAuthenticated ? children : <Navigate to="/dashboard" />;
};

export function App() {
  return (
    <AppThemeProvider>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#1E293B',
            color: '#F1F5F9',
            borderRadius: '8px',
          },
          success: {
            iconTheme: {
              primary: '#10B981',
              secondary: '#F1F5F9',
            },
          },
          error: {
            iconTheme: {
              primary: '#EF4444',
              secondary: '#F1F5F9',
            },
          },
        }}
      />
      <Router>
        <Routes>
          {/* Public Routes */}
          <Route
            path="/login"
            element={
              <PublicRoute>
                <Login />
              </PublicRoute>
            }
          />
          <Route
            path="/register"
            element={
              <PublicRoute>
                <Register />
              </PublicRoute>
            }
          />

          {/* Protected Routes */}
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <AppShell>
                  <Routes>
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/schemas" element={<Schemas />} />
                    <Route path="/asset-types" element={<AssetTypes />} />
                    <Route path="/analytics" element={<Analytics />} />
                    <Route path="/users" element={<Users />} />
                    <Route path="/metadata" element={<Metadata />} />
                    <Route
                      path="/analytics"
                      element={
                        <Box sx={{ p: 4 }}>
                          <Typography>Analytics Page (Coming Soon)</Typography>
                        </Box>
                      }
                    />
                    <Route
                      path="/settings"
                      element={
                        <Box sx={{ p: 4 }}>
                          <Typography>Settings Page (Coming Soon)</Typography>
                        </Box>
                      }
                    />
                    <Route path="/" element={<Navigate to="/dashboard" />} />
                  </Routes>
                </AppShell>
              </ProtectedRoute>
            }
          />
        </Routes>
      </Router>
    </AppThemeProvider>
  );
}
