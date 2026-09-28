import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Navbar } from './components/Navbar';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Login } from './pages/Login';
import { Roles } from './pages/Roles';
import { RoleDetail } from './pages/RoleDetail';
import { AddCandidate } from './pages/AddCandidate';
import { CandidateReport } from './pages/CandidateReport';
import { Costs } from './pages/Costs';
import { AssessIndex } from './pages/Assess/Index';
import { getAuthToken } from './api/client';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const token = getAuthToken();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const location = useLocation();
  const isCandidateAssessment = location.pathname.startsWith('/assess/');

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {!isCandidateAssessment && <Navbar />}
      <main className="flex-1 pb-12">{children}</main>
      {!isCandidateAssessment && (
        <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-500">
          <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
            <span>CandidateLens POC — See beyond the resume. Assess for readiness.</span>
            <span className="font-mono text-[11px]">Local Demo Mode (3-Call Architecture)</span>
          </div>
        </footer>
      )}
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary>
        <BrowserRouter>
          <Layout>
            <Routes>
              {/* Public Candidate Route */}
              <Route path="/assess/:token" element={<AssessIndex />} />

              {/* Public HR Login */}
              <Route path="/login" element={<Login />} />

              {/* Protected HR Routes */}
              <Route
                path="/roles"
                element={
                  <ProtectedRoute>
                    <Roles />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/roles/:roleId"
                element={
                  <ProtectedRoute>
                    <RoleDetail />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/roles/:roleId/add-candidate"
                element={
                  <ProtectedRoute>
                    <AddCandidate />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/candidates/:candidateId"
                element={
                  <ProtectedRoute>
                    <CandidateReport />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/costs"
                element={
                  <ProtectedRoute>
                    <Costs />
                  </ProtectedRoute>
                }
              />

              {/* Root redirect */}
              <Route path="/" element={<Navigate to="/roles" replace />} />
              <Route path="*" element={<Navigate to="/roles" replace />} />
            </Routes>
          </Layout>
        </BrowserRouter>
      </ErrorBoundary>
    </QueryClientProvider>
  );
};

export default App;
