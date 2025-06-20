// src/pages/dashboard/RoomDetailPage.tsx
import React from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { roomService } from '../../services/roomService';
import { Room } from '../../types/room';
import { useAuth } from '../../contexts/AuthContext';
import { UserRole } from '../../types/user';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';

const RoomDetailPage: React.FC = () => {
  const { roomId } = useParams<{ roomId: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();

  const canManage = user?.role === UserRole.ADMIN || user?.role === UserRole.MANAGER;

  const {
    data: room,
    isLoading,
    isError,
    error
  } = useQuery<Room, Error>({
    queryKey: ['room', roomId], // Unique query key including roomId
    queryFn: () => {
      if (!roomId) {
        // This case should ideally be caught by router or a check before this component renders
        // but as a safeguard:
        return Promise.reject(new Error("Room ID is required."));
      }
      return roomService.getRoomById(parseInt(roomId, 10));
    },
    enabled: !!roomId, // Only run query if roomId is available and valid number
  });

  if (!roomId || isNaN(parseInt(roomId, 10))) {
    return (
      <div className="p-4 text-center text-red-600">
        Error: ID de habitación inválido o no especificado.
        <Link to="/dashboard/rooms" className="block mt-4 text-brand-primary hover:underline">Volver a la lista de habitaciones</Link>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <p className="text-brand-text-secondary">Cargando detalles de la habitación...</p>
        {/* Or a spinner component */}
      </div>
    );
  }

  if (isError || !room) {
    return (
      <div className="p-4 bg-red-100 border border-red-400 text-red-700 rounded-md">
        <p className="font-semibold">Error al cargar detalles de la habitación:</p>
        <p>{error?.message || 'Habitación no encontrada o error desconocido.'}</p>
        <Link to="/dashboard/rooms" className="block mt-4 text-brand-primary hover:underline">Volver a la lista de habitaciones</Link>
      </div>
    );
  }

  return (
    <div className="animate-fadeIn">
      <div className="flex flex-wrap justify-between items-center mb-6 gap-4">
        <h1 className="text-2xl sm:text-3xl font-semibold text-brand-text-primary">
          Detalle: {room.name} (#{room.room_number})
        </h1>
        <Button onClick={() => navigate('/dashboard/rooms')} variant="secondary" className="w-auto text-sm sm:text-base">
          &larr; Volver a la Lista
        </Button>
      </div>

      <Card>
        <dl className="divide-y divide-gray-200"> {/* Use <dl> for definition list semantics */}
          <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-0"> {/* Adjusted px for dl */}
            <dt className="text-sm font-medium text-brand-text-secondary">Nombre / Designación</dt>
            <dd className="mt-1 text-sm text-brand-text-primary sm:mt-0 sm:col-span-2">{room.name}</dd>
          </div>
          <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-0">
            <dt className="text-sm font-medium text-brand-text-secondary">Número de Habitación</dt>
            <dd className="mt-1 text-sm text-brand-text-primary sm:mt-0 sm:col-span-2">{room.room_number}</dd>
          </div>
          <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-0">
            <dt className="text-sm font-medium text-brand-text-secondary">Tipo</dt>
            <dd className="mt-1 text-sm text-brand-text-primary sm:mt-0 sm:col-span-2">{room.type}</dd>
          </div>
          <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-0">
            <dt className="text-sm font-medium text-brand-text-secondary">Precio por Noche</dt>
            <dd className="mt-1 text-sm text-brand-text-primary sm:mt-0 sm:col-span-2">
              S/ {typeof room.price === 'number' ? room.price.toFixed(2) : parseFloat(String(room.price)).toFixed(2)} PEN
            </dd>
          </div>
          <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-0">
            <dt className="text-sm font-medium text-brand-text-secondary">Estado Actual</dt>
            <dd className={`mt-1 text-sm font-semibold sm:mt-0 sm:col-span-2 ${
               room.status === 'Available' ? 'text-green-600' :
               room.status === 'Occupied' ? 'text-red-600' :
               room.status === 'Maintenance' ? 'text-yellow-600' :
               'text-blue-600' // Cleaning or other
            }`}>
              {room.status}
            </dd>
          </div>
          {room.floor !== null && room.floor !== undefined && (
            <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-0">
              <dt className="text-sm font-medium text-brand-text-secondary">Piso</dt>
              <dd className="mt-1 text-sm text-brand-text-primary sm:mt-0 sm:col-span-2">{room.floor}</dd>
            </div>
          )}
          {room.building && (
            <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-0">
              <dt className="text-sm font-medium text-brand-text-secondary">Edificio/Sección</dt>
              <dd className="mt-1 text-sm text-brand-text-primary sm:mt-0 sm:col-span-2">{room.building}</dd>
            </div>
          )}
           <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-0">
             <dt className="text-sm font-medium text-brand-text-secondary">Creada</dt>
             <dd className="mt-1 text-sm text-brand-text-primary sm:mt-0 sm:col-span-2">{new Date(room.created_at).toLocaleString('es-PE', { dateStyle: 'long', timeStyle: 'short' })}</dd>
           </div>
           <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-0">
             <dt className="text-sm font-medium text-brand-text-secondary">Última Actualización</dt>
             <dd className="mt-1 text-sm text-brand-text-primary sm:mt-0 sm:col-span-2">{new Date(room.updated_at).toLocaleString('es-PE', { dateStyle: 'long', timeStyle: 'short' })}</dd>
           </div>
        </dl>
        {room.description && (
          <div className="mt-6 pt-4 border-t border-gray-200">
            <h3 className="text-sm font-medium text-brand-text-secondary">Descripción</h3> {/* Changed text-gray-500 to theme */}
            <p className="mt-1 text-sm text-brand-text-primary whitespace-pre-wrap">{room.description}</p> {/* Changed text-base to text-sm */}
          </div>
        )}
        {canManage && (
          <div className="mt-6 pt-6 border-t border-gray-200 flex justify-end"> {/* Added border color */}
            <Button
              onClick={() => navigate(`/dashboard/rooms/${room.id}/edit`)}
              variant="primary"
              className="w-auto"
            >
              Editar Habitación
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
};

export default RoomDetailPage;
