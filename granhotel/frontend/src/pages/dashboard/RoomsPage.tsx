// src/pages/dashboard/RoomsPage.tsx
import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import { roomService } from '../../services/roomService';
   import { useToast } from '../../contexts/ToastContext';
import { Room } from '../../types/room';
import { useAuth } from '../../contexts/AuthContext';
import { UserRole } from '../../types/user'; // Assuming UserRole enum/type is defined here or imported
import Button from '../../components/ui/Button';
import Card from '../../components/ui/Card';

// Define a key for react-query
const ROOMS_QUERY_KEY = 'rooms';

const RoomsPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
     const { addToast } = useToast();

  const { data: rooms, isLoading, error, isError } = useQuery<Room[], Error>({
    queryKey: [ROOMS_QUERY_KEY],
    queryFn: () => roomService.getRooms({ limit: 100 }),
  });

  const deleteRoomMutation = useMutation({
     mutationFn: roomService.deleteRoom,
     onSuccess: (deletedRoom) => {
       queryClient.invalidateQueries({ queryKey: [ROOMS_QUERY_KEY] });
       console.log(`Room "${deletedRoom.name}" deleted successfully.`);
       // TODO: Add toast notification
     },
     onError: (err: Error) => {
       console.error("Error deleting room:", err.message);
       alert(`Error al eliminar habitación: ${err.message}`);
     }
  });

  const handleDeleteRoom = (roomId: number, roomName: string) => {
     if (window.confirm(`¿Está seguro de que desea eliminar la habitación "${roomName}"? Esta acción no se puede deshacer.`)) {
         deleteRoomMutation.mutate(roomId);
     }
  };

  const canManageRooms = user?.role === UserRole.ADMIN || user?.role === UserRole.MANAGER;

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <p className="text-brand-text-secondary">Cargando habitaciones...</p>
        {/* Or a spinner component */}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-4 bg-red-100 border border-red-400 text-red-700 rounded-md">
        <p className="font-semibold">Error al cargar habitaciones:</p>
        <p>{error?.message || 'Ocurrió un error desconocido.'}</p>
      </div>
    );
  }

  return (
    <div className="animate-fadeIn">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-semibold text-brand-text-primary">
          Gestión de Habitaciones
        </h1>
        {canManageRooms && (
          <Button onClick={() => navigate('/dashboard/rooms/new')} variant="primary">
            Crear Nueva Habitación
          </Button>
        )}
      </div>

      {rooms && rooms.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {rooms.map((room) => (
            <Card key={room.id} className="flex flex-col justify-between group"> {/* Added group for hover effects if needed */}
              <div>
                <div className="flex justify-between items-start mb-2">
                  <h2 className="text-xl font-semibold text-brand-primary group-hover:text-brand-primary-dark transition-colors">
                     {room.name} (#{room.room_number})
                  </h2>
                  <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${
                     room.status === 'Available' ? 'bg-green-100 text-green-700' :
                     room.status === 'Occupied' ? 'bg-red-100 text-red-700' :
                     room.status === 'Maintenance' ? 'bg-yellow-100 text-yellow-700' :
                     'bg-blue-100 text-blue-700' // Cleaning or other
                  }`}>
                     {room.status}
                  </span>
                </div>
                <p className="text-sm text-brand-text-secondary mb-1">Tipo: {room.type}</p>
                <p className="text-sm text-brand-text-secondary mb-1">
                  Precio: S/ {typeof room.price === 'number' ? room.price.toFixed(2) : parseFloat(String(room.price)).toFixed(2)} PEN por noche
                </p>
                {room.floor && <p className="text-sm text-brand-text-secondary mb-1">Piso: {room.floor}</p>}
              </div>
              <div className="mt-auto pt-4 border-t border-gray-200 flex flex-wrap gap-2 justify-end"> {/* mt-auto pushes to bottom, flex-wrap and gap for better spacing */}
                <Button
                  onClick={() => navigate(`/dashboard/rooms/${room.id}/view`)}
                  variant="secondary"
                  className="w-auto text-xs px-3 py-1"
                >
                  Ver Detalles
                </Button>
                {canManageRooms && (
                  <>
                    <Button
                      onClick={() => navigate(`/dashboard/rooms/${room.id}/edit`)}
                      variant="primary"
                      className="w-auto text-xs px-3 py-1"
                    >
                      Editar
                    </Button>
                    <Button
                      onClick={() => handleDeleteRoom(room.id, room.name)}
                      variant="danger"
                      className="w-auto text-xs px-3 py-1"
                      isLoading={deleteRoomMutation.variables === room.id && deleteRoomMutation.isPending}
                    >
                      Eliminar
                    </Button>
                  </>
                )}
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <div className="text-center py-10">
          <p className="text-brand-text-secondary">No hay habitaciones para mostrar.</p>
          {canManageRooms && (
             <p className="mt-2 text-sm">Puede empezar <Link to="/dashboard/rooms/new" className="text-brand-primary hover:underline">creando una nueva habitación</Link>.</p>
          )}
        </div>
      )}
    </div>
  );
};

export default RoomsPage;
