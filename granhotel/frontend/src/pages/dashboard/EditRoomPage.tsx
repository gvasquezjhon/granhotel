// src/pages/dashboard/EditRoomPage.tsx
import React from 'react';
   import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { roomService } from '../../services/roomService';
import { RoomFormInputs } from '../../types/roomSchemas';
   import { Room, RoomUpdatePayload } from '../../types/room';
import RoomForm from '../../components/rooms/RoomForm';
import Card from '../../components/ui/Card';
   import { useToast } from '../../contexts/ToastContext';

const EditRoomPage: React.FC = () => {
  const { roomId } = useParams<{ roomId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
     const { addToast } = useToast();

  const numericRoomId = roomId ? parseInt(roomId, 10) : undefined;

  const { data: room, isLoading: isLoadingRoom, isError, error: roomError } = useQuery<Room, Error>({
    queryKey: ['room', numericRoomId],
    queryFn: () => {
        if (!numericRoomId) return Promise.reject(new Error("ID de habitación inválido"));
        return roomService.getRoomById(numericRoomId);
    },
    enabled: !!numericRoomId,
  });

  const updateRoomMutation = useMutation({
    mutationFn: (data: { id: number; payload: RoomUpdatePayload }) => roomService.updateRoom(data.id, data.payload),
    onSuccess: (updatedRoom) => {
      queryClient.invalidateQueries({ queryKey: ['rooms'] });
      queryClient.invalidateQueries({ queryKey: ['room', updatedRoom.id] });
      // TODO: Add success toast
      console.log(`Habitación "${updatedRoom.name}" actualizada con éxito.`);
      navigate(`/dashboard/rooms/${updatedRoom.id}/view`);
    },
    onError: (error: any) => {
      // TODO: Add error toast
      const errorMsg = error.response?.data?.detail || error.message || "Ocurrió un error desconocido.";
      console.error("Error updating room:", errorMsg);
      alert(`Error al actualizar habitación: ${errorMsg}`);
    },
  });

  const handleSubmit = (data: RoomFormInputs) => {
    if (!numericRoomId) return;

    // Construct RoomUpdatePayload - only send changed fields.
    // However, RoomForm sends all fields. The service should handle partial updates if schema allows.
    // Our RoomUpdatePayload in types/room.ts is already all optional.
    // The RoomForm a Zod schema that requires all fields.
    // This means the form always submits all fields.
    // If we want true partial updates, the form or this handler needs to identify changed fields.
    // For now, send all fields as per RoomFormInputs, and backend PUT should handle it.
    const payload: RoomUpdatePayload = {
      ...data,
      price: Number(data.price),
      floor: data.floor ? Number(data.floor) : null,
      building: data.building || undefined, // Or null, depending on backend schema expectations for optional empty strings
      description: data.description || undefined,
    };
    updateRoomMutation.mutate({ id: numericRoomId, payload });
  };

  if (!numericRoomId && !isLoadingRoom) return ( // Check isLoadingRoom to avoid premature error render
    <div className="p-4 text-red-500 text-center">
        ID de habitación no válido.
        <Link to="/dashboard/rooms" className="block mt-2 text-brand-primary hover:underline">Volver</Link>
    </div>
  );
  if (isLoadingRoom) return <div className="p-6 text-center">Cargando datos de la habitación...</div>;
  if (isError || !room) return <div className="p-4 bg-red-100 text-red-700 rounded-md text-center">Error al cargar habitación: {roomError?.message || "No encontrada"}. <Link to="/dashboard/rooms" className="block mt-2 font-semibold text-brand-primary hover:underline">Volver</Link></div>;

  const initialFormData: Partial<RoomFormInputs> = {
     ...room,
     price: room.price, // Already number in Room type
     floor: room.floor ?? undefined, // Ensure undefined if null for form
     building: room.building ?? undefined,
     description: room.description ?? undefined,
  };

  return (
    <div className="animate-fadeIn">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold text-brand-text-primary">Editar Habitación: {room.name} (#{room.room_number})</h1>
        <Link
            to={`/dashboard/rooms/${room.id}/view`}
            className="text-sm text-brand-primary hover:text-brand-primary-dark hover:underline"
        >
            &larr; Volver a detalles
        </Link>
      </div>
      <Card>
        <RoomForm
          onSubmit={handleSubmit}
          initialData={initialFormData}
          isLoading={updateRoomMutation.isPending}
          submitButtonText="Guardar Cambios"
        />
      </Card>
    </div>
  );
};
export default EditRoomPage;
