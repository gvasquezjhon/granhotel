// src/layouts/MainLayout.tsx
import React from 'react';
import { Outlet, Link, useNavigate } from 'react-router-dom'; // Import useNavigate
import { useAuth } from '../contexts/AuthContext'; // Import useAuth

const MainLayout: React.FC = () => {
  const { logout, user } = useAuth(); // Get logout function and user from context
  const navigate = useNavigate();

  const handleLogout = () => {
    logout(); // Call logout from AuthContext
    navigate('/login', { replace: true }); // Redirect to login page
  };

  return (
    <div className="flex flex-col min-h-screen">
      <header className="bg-indigo-700 text-white shadow-md">
        <nav className="container mx-auto px-4 sm:px-6 py-3 flex flex-wrap justify-between items-center">
          <Link to="/dashboard" className="text-xl font-bold">
            Gran Hotel Perú
          </Link>
          <div className="flex items-center space-x-2 sm:space-x-4 mt-2 sm:mt-0">
            {/* Navigation Links - Example */}
            <Link to="/dashboard" className="text-sm sm:text-base px-3 py-2 rounded hover:bg-indigo-600">Panel</Link>
            {/* Add more links based on user role perhaps */}
            {/* Example: Only show certain links to Admin/Manager */}
            {(user?.role === "ADMIN" || user?.role === "MANAGER") && (
              <>
                <Link to="/dashboard/rooms" className="text-sm sm:text-base px-3 py-2 rounded hover:bg-indigo-600">Habitaciones</Link>
                <Link to="/dashboard/reservations" className="text-sm sm:text-base px-3 py-2 rounded hover:bg-indigo-600">Reservas</Link>
              </>
            )}
            <span className="text-sm text-indigo-200 hidden sm:inline">
              {user ? `${user.first_name || ''} ${user.last_name || ''} (${user.role})` : ''}
            </span>
            <button
              onClick={handleLogout}
              className="text-sm sm:text-base px-3 py-2 bg-red-500 hover:bg-red-600 rounded"
            >
              Cerrar Sesión
            </button>
          </div>
        </nav>
      </header>
      <main className="flex-grow container mx-auto px-4 sm:px-6 py-8 bg-gray-100"> {/* Changed bg-gray-50 to bg-gray-100 for consistency */}
        <Outlet /> {/* Authenticated page content renders here */}
      </main>
      <footer className="bg-gray-800 text-white text-center p-4">
        © {new Date().getFullYear()} Gran Hotel Perú. Todos los derechos reservados.
      </footer>
    </div>
  );
};
export default MainLayout;
