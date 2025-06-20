// src/App.tsx
import React from 'react';
import { Routes, Route, Navigate, Outlet } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import NotFoundPage from './pages/NotFoundPage';
import AuthLayout from './layouts/AuthLayout';
import MainLayout from './layouts/MainLayout';
import { useAuth } from './contexts/AuthContext';

// Room Management Pages
import RoomsPage from './pages/dashboard/RoomsPage';
import CreateRoomPage from './pages/dashboard/CreateRoomPage';
import RoomDetailPage from './pages/dashboard/RoomDetailPage';
import EditRoomPage from './pages/dashboard/EditRoomPage';

// Guest Management Pages
import GuestsPage from './pages/dashboard/GuestsPage';
import CreateGuestPage from './pages/dashboard/CreateGuestPage';
import GuestDetailPage from './pages/dashboard/GuestDetailPage';
import EditGuestPage from './pages/dashboard/EditGuestPage';


const ProtectedRoute: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) {
    return <div className="flex justify-center items-center min-h-screen text-brand-text-primary">Cargando...</div>;
  }
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <MainLayout />;
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
      {/* Public routes */}
      <Route element={<PublicRoute />}>
        <Route path="/login" element={<LoginPage />} />
      </Route>

      {/* Protected routes - Main application */}
      <Route path="/dashboard" element={<ProtectedRoute />}>
        <Route index element={<DashboardPage />} />

        {/* Room Management Routes */}
        <Route path="rooms">
          <Route index element={<RoomsPage />} />
          <Route path="new" element={<CreateRoomPage />} />
          <Route path=":roomId/view" element={<RoomDetailPage />} />
          <Route path=":roomId/edit" element={<EditRoomPage />} />
        </Route>

        {/* Guest Management Routes */}
        <Route path="guests">
          <Route index element={<GuestsPage />} />
          <Route path="new" element={<CreateGuestPage />} />
          <Route path=":guestId/view" element={<GuestDetailPage />} />
          <Route path=":guestId/edit" element={<EditGuestPage />} />
        </Route>

        {/* Placeholder for other dashboard sections */}
        {/* <Route path="reservations" element={<ReservationsPage />} /> */}
      </Route>

      <Route
        path="/"
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Navigate to="/login" replace />}
      />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
};

export default App;
