// src/App.tsx
import React from 'react';
import { Routes, Route, Navigate, Outlet } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import NotFoundPage from './pages/NotFoundPage';
import AuthLayout from './layouts/AuthLayout';
import MainLayout from './layouts/MainLayout';
import { useAuth } from './contexts/AuthContext';

// Import Room Management Pages
import RoomsPage from './pages/dashboard/RoomsPage';
import CreateRoomPage from './pages/dashboard/CreateRoomPage';
import RoomDetailPage from './pages/dashboard/RoomDetailPage';
import EditRoomPage from './pages/dashboard/EditRoomPage';

const ProtectedRoute: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <div className="flex justify-center items-center min-h-screen text-brand-text-primary">Cargando...</div>;
  }
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <MainLayout />; // MainLayout contains <Outlet /> for its children
};

const PublicRoute: React.FC = () => {
    const { isAuthenticated, isLoading } = useAuth();
    if (isLoading) {
        return <div className="flex justify-center items-center min-h-screen text-brand-text-primary">Cargando...</div>;
    }
    return isAuthenticated ? <Navigate to="/dashboard" replace /> : <AuthLayout />;
};

const App: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
     return <div className="flex justify-center items-center min-h-screen text-brand-text-primary">Verificando autenticación...</div>;
  }

  return (
    <Routes>
      {/* Public routes like login, register */}
      <Route element={<PublicRoute />}>
        <Route path="/login" element={<LoginPage />} />
        {/* <Route path="/register" element={<RegisterPage />} /> */}
      </Route>

      {/* Protected routes - Main application */}
      <Route path="/dashboard" element={<ProtectedRoute />}>
        <Route index element={<DashboardPage />} />

        {/* Room Management Routes */}
        {/* Using Outlet to render child routes within the MainLayout context provided by ProtectedRoute */}
        {/* The path "rooms" is relative to "/dashboard" */}
        <Route path="rooms">
          <Route index element={<RoomsPage />} />
          <Route path="new" element={<CreateRoomPage />} />
          <Route path=":roomId/view" element={<RoomDetailPage />} />
          <Route path=":roomId/edit" element={<EditRoomPage />} />
        </Route>

        {/* Placeholder for other dashboard sections */}
        {/* <Route path="reservations" element={<ReservationsPage />} /> */}
        {/* <Route path="guests" element={<GuestsPage />} /> */}
        {/* ... etc. ... */}
      </Route>

      {/* Root path redirect */}
      <Route
        path="/"
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Navigate to="/login" replace />}
      />

      {/* Catch-all for not found pages */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
};

export default App;
