// src/App.tsx
import React from 'react';
import { Routes, Route, Navigate, Outlet } from 'react-router-dom'; // Added Outlet
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import NotFoundPage from './pages/NotFoundPage';
import AuthLayout from './layouts/AuthLayout';
import MainLayout from './layouts/MainLayout';
import { useAuth } from './contexts/AuthContext'; // Import useAuth

const ProtectedRoute: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <div className="flex justify-center items-center min-h-screen">Cargando...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  // If authenticated, MainLayout will render its <Outlet /> for nested routes
  return <MainLayout />;
};

// PublicRoute to redirect authenticated users from login page (and other auth pages)
const PublicRoute: React.FC = () => {
    const { isAuthenticated, isLoading } = useAuth();
    if (isLoading) {
        return <div className="flex justify-center items-center min-h-screen">Cargando...</div>;
    }
    // If authenticated, redirect to dashboard, otherwise render the AuthLayout (which contains Outlet for login/register)
    return isAuthenticated ? <Navigate to="/dashboard" replace /> : <AuthLayout />;
};


const App: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
     return <div className="flex justify-center items-center min-h-screen">Verificando autenticación...</div>;
  }

  return (
    <Routes>
      <Route element={<PublicRoute />}>
        <Route path="/login" element={<LoginPage />} />
        {/* Example: <Route path="/register" element={<RegisterPage />} /> */}
      </Route>

      <Route path="/dashboard" element={<ProtectedRoute />}> {/* ProtectedRoute now includes MainLayout */}
        <Route index element={<DashboardPage />} />
        {/* Example nested routes for dashboard sections: */}
        {/* <Route path="rooms" element={<RoomsPage />} /> */}
        {/* <Route path="reservations" element={<ReservationsPage />} /> */}
      </Route>

      {/* Root path redirect logic:
          If initial loading is done:
          - If authenticated, go to /dashboard.
          - If not authenticated, go to /login.
      */}
      <Route
        path="/"
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Navigate to="/login" replace />}
      />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
};

export default App;
