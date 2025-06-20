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

// Reservation System Pages
import ReservationsPage from './pages/dashboard/ReservationsPage';
import CreateReservationPage from './pages/dashboard/CreateReservationPage';
import ReservationDetailPage from './pages/dashboard/ReservationDetailPage';
import EditReservationPage from './pages/dashboard/EditReservationPage';


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

        <Route path="rooms"> {/* No element needed on parent if it just provides Outlet context */}
          <Route index element={<RoomsPage />} />
          <Route path="new" element={<CreateRoomPage />} />
          <Route path=":roomId/view" element={<RoomDetailPage />} />
          <Route path=":roomId/edit" element={<EditRoomPage />} />
        </Route>

        <Route path="guests">
          <Route index element={<GuestsPage />} />
          <Route path="new" element={<CreateGuestPage />} />
          <Route path=":guestId/view" element={<GuestDetailPage />} />
          <Route path=":guestId/edit" element={<EditGuestPage />} />
        </Route>

        <Route path="reservations">
          <Route index element={<ReservationsPage />} />
          <Route path="new" element={<CreateReservationPage />} />
          <Route path=":reservationId/view" element={<ReservationDetailPage />} />
          <Route path=":reservationId/edit" element={<EditReservationPage />} />
        </Route>

        {/* Placeholder for other dashboard sections */}
        {/* <Route path="products" element={<ProductsPage />} /> */}
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
