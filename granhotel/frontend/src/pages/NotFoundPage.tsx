// src/pages/NotFoundPage.tsx
import React from 'react';
import { Link } from 'react-router-dom';

const NotFoundPage: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen text-center p-4">
      <h1 className="text-4xl font-bold text-red-600 mb-4">404 - Página No Encontrada</h1>
      <p className="text-lg text-gray-700 mb-6">
        Lo sentimos, la página que busca no existe.
      </p>
      <Link
        to="/"
        className="px-6 py-2 text-white bg-blue-600 rounded hover:bg-blue-700 transition-colors"
      >
        Volver al Inicio
      </Link>
    </div>
  );
};
export default NotFoundPage;
