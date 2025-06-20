// src/layouts/AuthLayout.tsx
import React from 'react';
import { Outlet } from 'react-router-dom';

const AuthLayout: React.FC = () => {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-gradient-theme p-4 sm:p-6 lg:p-8"> {/* Used new gradient */}
      {/* Optional: Add a logo or branding here */}
      {/* <img src="/logo-gran-hotel.png" alt="Gran Hotel Perú" className="mb-8 h-12 w-auto" /> */}
      <Outlet />
    </main>
  );
};
export default AuthLayout;
