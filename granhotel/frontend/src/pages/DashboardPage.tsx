// src/pages/DashboardPage.tsx
import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext'; // To get user info
import Card from '../components/ui/Card'; // Reusable Card component
import { UserRole } from '../types/user'; // Assuming UserRole enum/type is defined here or imported

// Define an interface for quick link items
interface QuickLinkItem {
  to: string;
  title: string;
  description: string;
  icon?: React.ReactNode; // Optional: for an icon element
  roles?: UserRole[]; // Roles that can see this link
}

const DashboardPage: React.FC = () => {
  const { user } = useAuth();

  const quickLinks: QuickLinkItem[] = [
    {
      to: '/dashboard/rooms', // Placeholder - will be actual route
      title: 'Gestionar Habitaciones',
      description: 'Ver, crear y editar tipos de habitaciones y estado.',
      roles: [UserRole.ADMIN, UserRole.MANAGER],
    },
    {
      to: '/dashboard/reservations', // Placeholder
      title: 'Ver Reservas',
      description: 'Consultar y administrar las reservas de huéspedes.',
      roles: [UserRole.ADMIN, UserRole.MANAGER, UserRole.RECEPTIONIST],
    },
    {
      to: '/dashboard/pos', // Placeholder
      title: 'Punto de Venta (POS)',
      description: 'Realizar ventas de productos y servicios.',
      roles: [UserRole.ADMIN, UserRole.MANAGER, UserRole.RECEPTIONIST],
    },
    {
      to: '/dashboard/housekeeping', // Placeholder
      title: 'Limpieza (Housekeeping)',
      description: 'Administrar tareas y estado de limpieza de habitaciones.',
      roles: [UserRole.ADMIN, UserRole.MANAGER, UserRole.HOUSEKEEPER],
    },
    {
      to: '/dashboard/reports', // Placeholder
      title: 'Reportes y Analíticas',
      description: 'Visualizar reportes de ocupación, ventas e inventario.',
      roles: [UserRole.ADMIN, UserRole.MANAGER],
    },
    // Add more links as modules are developed
  ];

  const userHasRole = (allowedRoles?: UserRole[]) => {
    if (!allowedRoles || allowedRoles.length === 0) {
      return true; // No specific roles required, visible to all authenticated
    }
    if (!user || !user.role) {
      return false; // User or user role not defined
    }
    // user.role from AuthContext is already of type UserRole (enum) as per src/types/user.ts
    return allowedRoles.includes(user.role);
  };

  // Filter links based on user role
  const accessibleQuickLinks = quickLinks.filter(link => userHasRole(link.roles));

  return (
    <div className="animate-fadeIn"> {/* Simple fade-in animation example */}
      <h1 className="text-3xl font-semibold text-brand-text-primary mb-2">
        Panel Principal
      </h1>
      {user && (
        <p className="text-lg text-brand-text-secondary mb-8">
          Bienvenido de nuevo, {user.first_name || user.email}!
        </p>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {accessibleQuickLinks.map((link) => (
          <Link to={link.to} key={link.title} className="block hover:shadow-xl transition-shadow duration-300 rounded-xl">
            <Card title={link.title} className="h-full flex flex-col">
              <p className="text-brand-text-secondary text-sm flex-grow">
                {link.description}
              </p>
              {/* Optional: Add a footer or icon to the card if link.icon is present */}
              <div className="mt-4 text-brand-primary hover:text-brand-primary-dark font-semibold">
                 Ir →
              </div>
            </Card>
          </Link>
        ))}
        {accessibleQuickLinks.length === 0 && (
          <p className="text-brand-text-secondary md:col-span-2 lg:col-span-3 text-center py-8">
            {user?.role ? `No hay módulos configurados o accesibles para su rol (${user.role}).` : 'Cargando opciones disponibles...'}
          </p>
        )}
      </div>
    </div>
  );
};

export default DashboardPage;
