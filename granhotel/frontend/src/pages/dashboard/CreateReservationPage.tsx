// src/pages/dashboard/CreateReservationPage.tsx
import React from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate, Link }  from 'react-router-dom';
import { reservationService } from '../../services/reservationService';
import { ReservationFormInputs } from '../../types/reservationSchemas';
import { ReservationCreatePayload } from '../../types/reservation'; // For payload type
import ReservationForm from '../../components/reservations/ReservationForm';
import Card from '../../components/ui/Card';
import { useToast } from '../../contexts/ToastContext';
import { useAuth } from '../../contexts/AuthContext';
import { UserRole } from '../../types/user';


const CreateReservationPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  const { user } = useAuth();

  if (!user || ![UserRole.ADMIN, UserRole.MANAGER, UserRole.RECEPTIONIST].includes(user.role)) {
     return (
        <div className="p-6 text-red-500">
            No tiene permisos para crear reservas.
            <Link to="/dashboard/reservations" className="block mt-2 text-brand-primary hover:underline">Volver a la lista</Link>
        </div>
     );
  }

  const createReservationMutation = useMutation({
    mutationFn: (payload: ReservationCreatePayload) => reservationService.createReservation(payload),
    onSuccess: (newReservation) => {
      queryClient.invalidateQueries({ queryKey: ['reservations'] });
      addToast(`Reserva para Huésped ID ${newReservation.guest_id} (Habitación ID: ${newReservation.room_id}) creada con éxito.`, 'success');
      navigate('/dashboard/reservations');
    },
    onError: (error: any) => {
      const errorMsg = error.response?.data?.detail || error.message || "Ocurrió un error desconocido.";
      addToast(`Error al crear reserva: ${errorMsg}`, 'error');
    },
  });

  const handleSubmitForm = (data: ReservationFormInputs) => {
    const payload: ReservationCreatePayload = {
      guest_id: data.guest_id, // Already string (UUID) from form
      room_id: Number(data.room_id), // Zod preprocesses to number, ensure it's number
      check_in_date: data.check_in_date, // String "YYYY-MM-DD" from DatePicker via Controller
      check_out_date: data.check_out_date, // String "YYYY-MM-DD"
      status: data.status, // Enum value
      notes: data.notes || null,
    };
    createReservationMutation.mutate(payload);
  };

  return (
    <div className="animate-fadeIn">
      <div className="flex justify-between items-center mb-6">
      <h1 className="text-2xl font-semibold text-brand-text-primary">Crear Nueva Reserva</h1>
        <Link
            to="/dashboard/reservations"
            className="text-sm text-brand-primary hover:text-brand-primary-dark hover:underline"
        >
            &larr; Volver a la lista
        </Link>
      </div>
      <Card>
        <ReservationForm
          onSubmit={handleSubmitForm}
          isLoading={createReservationMutation.isPending}
          submitButtonText="Crear Reserva"
          isEditMode={false}
        />
      </Card>
    </div>
  );
};
export default CreateReservationPage;
