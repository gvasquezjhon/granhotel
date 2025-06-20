// src/pages/dashboard/CreateRoomPage.tsx
import React from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
   import { useNavigate, Link }  from 'react-router-dom';
import { roomService } from '../../services/roomService';
import { RoomFormInputs } from '../../types/roomSchemas';
import RoomForm from '../../components/rooms/RoomForm';
import Card from '../../components/ui/Card';
   import { useToast } from '../../contexts/ToastContext';

const CreateRoomPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
     const { addToast } = useToast();

  const createRoomMutation = useMutation({
    mutationFn: roomService.createRoom,
    onSuccess: (newRoom) => {
      queryClient.invalidateQueries({ queryKey: ['rooms'] });
         addToast(`Habitación "${newRoom.name}" (#${newRoom.room_number}) creada con éxito.`, 'success');
      navigate('/dashboard/rooms');
    },
       onError: (error: any) => {
      const errorMsg = error.response?.data?.detail || error.message || "Ocurrió un error desconocido.";
         addToast(`Error al crear habitación: ${errorMsg}`, 'error');
    },
  });

  const handleSubmit = (data: RoomFormInputs) => {
    // Zod schema already preprocesses price to number and floor to number/null.
    // Ensure payload matches RoomCreatePayload from types/room.ts
    const payload = {
      ...data,
      price: Number(data.price), // Ensure it's number
      floor: data.floor ? Number(data.floor) : null,
      building: data.building || null, // Ensure empty string becomes null if model expects it
      description: data.description || null,
    };
    createRoomMutation.mutate(payload);
  };

  return (
    <div className="animate-fadeIn">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold text-brand-text-primary">Crear Nueva Habitación</h1>
        <Link
            to="/dashboard/rooms"
            className="text-sm text-brand-primary hover:text-brand-primary-dark hover:underline"
        >
            &larr; Volver a la lista
        </Link>
      </div>
      <Card>
        <RoomForm
          onSubmit={handleSubmit}
          isLoading={createRoomMutation.isPending}
          submitButtonText="Crear Habitación"
        />
      </Card>
    </div>
  );
};
export default CreateRoomPage;
