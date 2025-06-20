// src/pages/dashboard/EditReservationPage.tsx
import React from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reservationService } from '../../services/reservationService';
import { ReservationFormInputs } from '../../types/reservationSchemas';
import { Reservation, ReservationUpdatePayload } from '../../types/reservation'; // Import ReservationUpdatePayload
import ReservationForm from '../../components/reservations/ReservationForm';
import Card from '../../components/ui/Card';
import { useToast } from '../../contexts/ToastContext';
import { useAuth } from '../../contexts/AuthContext';
import { UserRole } from '../../types/user';

const EditReservationPage: React.FC = () => {
  const { reservationId } = useParams<{ reservationId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  const { user } = useAuth();

  const numericReservationId = reservationId ? parseInt(reservationId, 10) : undefined;

  // Basic permission check for edit page access
  if (!user || ![UserRole.ADMIN, UserRole.MANAGER, UserRole.RECEPTIONIST].includes(user.role)) {
     return (
        <div className="p-6 text-red-500">
            No tiene permisos para editar reservas.
            <Link to="/dashboard/reservations" className="block mt-2 text-brand-primary hover:underline">Volver</Link>
        </div>
     );
  }

  const { data: reservation, isLoading: isLoadingReservation, isError, error: reservationError } = useQuery<Reservation, Error>({
    queryKey: ['reservation', numericReservationId],
    queryFn: () => numericReservationId ? reservationService.getReservationById(numericReservationId) : Promise.reject(new Error("ID de reserva inválido")),
    enabled: !!numericReservationId,
  });

  const updateReservationMutation = useMutation({
    mutationFn: (data: { id: number; payload: ReservationUpdatePayload }) => reservationService.updateReservationDetails(data.id, data.payload),
    onSuccess: (updatedReservation) => {
      queryClient.invalidateQueries({ queryKey: ['reservations'] });
      queryClient.invalidateQueries({ queryKey: ['reservation', updatedReservation.id] });
      addToast(`Reserva ID ${updatedReservation.id} actualizada con éxito.`, 'success');
      navigate(`/dashboard/reservations/${updatedReservation.id}/view`);
    },
    onError: (error: any) => {
      const errorMsg = error.response?.data?.detail || error.message || "Ocurrió un error desconocido.";
      addToast(`Error al actualizar reserva: ${errorMsg}`, 'error');
    },
  });

  const handleSubmitForm = (data: ReservationFormInputs) => {
    if (!numericReservationId) return;
    const payload: ReservationUpdatePayload = {
      // Only include fields that are part of ReservationUpdatePayload
      guest_id: data.guest_id, // Assuming guest_id can be changed, though often not
      room_id: Number(data.room_id),
      check_in_date: data.check_in_date,
      check_out_date: data.check_out_date,
      status: data.status,
      notes: data.notes || null,
      // total_price is not directly updatable via this form/payload
    };
    updateReservationMutation.mutate({ id: numericReservationId, payload });
  };

  if (!numericReservationId && !isLoadingReservation) return (
    <div className="p-4 text-red-500 text-center">
        ID de reserva no válido.
        <Link to="/dashboard/reservations" className="block mt-2 text-brand-primary hover:underline">Volver</Link>
    </div>
  );
  if (isLoadingReservation) return <div className="p-6 text-center text-brand-text-secondary">Cargando datos de la reserva...</div>;
  if (isError || !reservation) return <div className="p-4 bg-red-100 text-red-700 rounded-md text-center">Error al cargar reserva: {reservationError?.message || "No encontrada"}. <Link to="/dashboard/reservations" className="block mt-2 font-semibold text-brand-primary hover:underline">Volver</Link></div>;

  // Prepare initialData for the form, ensuring all form fields are accounted for.
  const initialFormData: Partial<ReservationFormInputs> = {
     guest_id: String(reservation.guest_id), // Convert UUID to string for form
     room_id: Number(reservation.room_id),
     check_in_date: reservation.check_in_date, // Already "YYYY-MM-DD" string
     check_out_date: reservation.check_out_date, // Already "YYYY-MM-DD" string
     status: reservation.status,
     notes: reservation.notes || undefined,
  };

  return (
    <div className="animate-fadeIn">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold text-brand-text-primary">Editar Reserva ID: {reservation.id}</h1>
        <Link
            to={`/dashboard/reservations/${reservation.id}/view`}
            className="text-sm text-brand-primary hover:text-brand-primary-dark hover:underline"
        >
            &larr; Volver a detalles
        </Link>
      </div>
      <Card>
        <ReservationForm
          onSubmit={handleSubmitForm}
          initialData={initialFormData}
          isLoading={updateReservationMutation.isPending}
          submitButtonText="Guardar Cambios"
          isEditMode={true}
        />
      </Card>
    </div>
  );
};
export default EditReservationPage;
