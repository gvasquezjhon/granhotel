// src/pages/dashboard/ReservationDetailPage.tsx
import React from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reservationService } from '../../services/reservationService';
import { Reservation, ReservationStatus } from '../../types/reservation';
import { useAuth } from '../../contexts/AuthContext';
import { UserRole } from '../../types/user';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import { useToast } from '../../contexts/ToastContext';

const ReservationDetailPage: React.FC = () => {
  const { reservationId } = useParams<{ reservationId: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  const numericReservationId = reservationId ? parseInt(reservationId, 10) : undefined;

  const canManage = user?.role === UserRole.ADMIN || user?.role === UserRole.MANAGER;

  const {
    data: reservation,
    isLoading,
    isError,
    error
  } = useQuery<Reservation, Error>({
    queryKey: ['reservation', numericReservationId],
    queryFn: () => {
      if (!numericReservationId) {
        // This should ideally be caught before enabling the query or by router validation
        return Promise.reject(new Error("ID de reserva es requerido."));
      }
      return reservationService.getReservationById(numericReservationId);
    },
    enabled: !!numericReservationId,
  });

  const cancelReservationMutation = useMutation({
     mutationFn: reservationService.cancelReservation,
     onSuccess: (cancelledReservation) => {
       queryClient.invalidateQueries({ queryKey: ['reservations'] });
       queryClient.invalidateQueries({ queryKey: ['reservation', cancelledReservation.id]});
       addToast(`Reserva ID ${cancelledReservation.id} cancelada con éxito.`, 'success');
       // Optionally navigate or just let the page reflect the new status
     },
     onError: (err: Error) => {
       addToast(`Error al cancelar reserva: ${err.message}`, 'error');
     }
  });

  const handleCancelReservation = () => {
     if (!numericReservationId || !reservation) return;
     if (window.confirm(`¿Está seguro de que desea cancelar la Reserva ID ${reservation.id} para el huésped ${reservation.guest?.first_name || ''} ${reservation.guest?.last_name || ''}?`)) {
         cancelReservationMutation.mutate(numericReservationId);
     }
  };

  if (!numericReservationId && !isLoading) { // Check isLoading to avoid premature error render
    return (
      <div className="p-4 text-center text-red-600">
        Error: No se especificó el ID de la reserva o es inválido.
        <Link to="/dashboard/reservations" className="block mt-4 text-brand-primary hover:underline">Volver a la lista de reservas</Link>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <p className="text-brand-text-secondary">Cargando detalles de la reserva...</p>
      </div>
    );
  }

  if (isError || !reservation) {
    return (
      <div className="p-4 bg-red-100 border border-red-400 text-red-700 rounded-md">
        <p className="font-semibold">Error al cargar detalles de la reserva:</p>
        <p>{error?.message || 'Reserva no encontrada o error desconocido.'}</p>
        <Link to="/dashboard/reservations" className="block mt-4 text-brand-primary hover:underline">Volver a la lista de reservas</Link>
      </div>
    );
  }

  const isCancellable = canManage &&
                        reservation.status !== ReservationStatus.CANCELLED &&
                        reservation.status !== ReservationStatus.CHECKED_OUT;
  const isEditable = canManage &&
                     reservation.status !== ReservationStatus.CANCELLED &&
                     reservation.status !== ReservationStatus.CHECKED_OUT;


  return (
    <div className="animate-fadeIn">
      <div className="flex flex-wrap justify-between items-center mb-6 gap-4">
        <h1 className="text-2xl sm:text-3xl font-semibold text-brand-text-primary">
          Detalle de Reserva ID: {reservation.id}
        </h1>
        <Button onClick={() => navigate('/dashboard/reservations')} variant="secondary" className="w-auto text-sm sm:text-base">
          &larr; Volver a la Lista
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2" title="Información de la Reserva">
          <dl className="divide-y divide-gray-200">
            <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4">
              <dt className="text-sm font-medium text-brand-text-secondary">Estado</dt>
              <dd className="mt-1 text-sm text-brand-text-primary sm:mt-0 sm:col-span-2">
                 <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                       reservation.status === ReservationStatus.CONFIRMED ? 'bg-green-100 text-green-800' :
                       reservation.status === ReservationStatus.PENDING ? 'bg-yellow-100 text-yellow-800' :
                       reservation.status === ReservationStatus.CHECKED_IN ? 'bg-blue-100 text-blue-800' :
                       reservation.status === ReservationStatus.CHECKED_OUT ? 'bg-slate-100 text-slate-600' :
                       reservation.status === ReservationStatus.CANCELLED ? 'bg-red-100 text-red-800' :
                       reservation.status === ReservationStatus.NO_SHOW ? 'bg-orange-100 text-orange-800' :
                       reservation.status === ReservationStatus.WAITLIST ? 'bg-purple-100 text-purple-800' :
                       'bg-gray-100 text-gray-600' // Default/fallback
                    }`}>
                       {reservation.status} {/* Consider using formattedStatusOptions here too if labels are different */}
                  </span>
              </dd>
            </div>
            <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4">
              <dt className="text-sm font-medium text-brand-text-secondary">Fecha de Reserva</dt>
              <dd className="mt-1 text-sm text-brand-text-primary sm:mt-0 sm:col-span-2">{new Date(reservation.reservation_date).toLocaleString('es-PE', { dateStyle: 'long', timeStyle: 'short' })}</dd>
            </div>
            <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4">
              <dt className="text-sm font-medium text-brand-text-secondary">Check-in</dt> {/* Dates are YYYY-MM-DD strings, add T00:00:00 for local time interpretation */}
              <dd className="mt-1 text-sm text-brand-text-primary sm:mt-0 sm:col-span-2">{new Date(reservation.check_in_date + 'T00:00:00').toLocaleDateString('es-PE', { dateStyle: 'long' })}</dd>
            </div>
            <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4">
              <dt className="text-sm font-medium text-brand-text-secondary">Check-out</dt>
              <dd className="mt-1 text-sm text-brand-text-primary sm:mt-0 sm:col-span-2">{new Date(reservation.check_out_date + 'T00:00:00').toLocaleDateString('es-PE', { dateStyle: 'long' })}</dd>
            </div>
            <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4">
              <dt className="text-sm font-medium text-brand-text-secondary">Precio Total</dt>
              <dd className="mt-1 text-sm text-brand-text-primary sm:mt-0 sm:col-span-2">S/ {reservation.total_price ? Number(reservation.total_price).toFixed(2) : 'N/A'} PEN</dd>
            </div>
            {reservation.notes && (
             <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4">
                 <dt className="text-sm font-medium text-brand-text-secondary">Notas</dt>
                 <dd className="mt-1 text-sm text-brand-text-primary sm:mt-0 sm:col-span-2 whitespace-pre-wrap">{reservation.notes}</dd>
             </div>
            )}
             <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4">
                 <dt className="text-sm font-medium text-brand-text-secondary">Creada</dt>
                 <dd className="mt-1 text-sm text-brand-text-secondary sm:mt-0 sm:col-span-2">{new Date(reservation.created_at).toLocaleString('es-PE', { dateStyle: 'short', timeStyle: 'short' })}</dd>
             </div>
             <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4">
                 <dt className="text-sm font-medium text-brand-text-secondary">Actualizada</dt>
                 <dd className="mt-1 text-sm text-brand-text-secondary sm:mt-0 sm:col-span-2">{new Date(reservation.updated_at).toLocaleString('es-PE', { dateStyle: 'short', timeStyle: 'short' })}</dd>
             </div>
          </dl>
          { (isEditable || isCancellable) && (
             <div className="mt-6 pt-4 border-t border-gray-200 flex flex-wrap gap-3 justify-end">
                 {isEditable && (
                     <Button
                         onClick={() => navigate(`/dashboard/reservations/${reservation.id}/edit`)}
                         variant="primary" className="w-auto"
                     >
                         Editar Reserva
                     </Button>
                 )}
                 {isCancellable && (
                     <Button
                         onClick={handleCancelReservation}
                         variant="danger" className="w-auto"
                         isLoading={cancelReservationMutation.isPending && cancelReservationMutation.variables === numericReservationId}
                     >
                         Cancelar Reserva
                     </Button>
                 )}
             </div>
          )}
        </Card>

        {reservation.guest && (
          <Card className="lg:col-span-1" title={`Huésped: ${reservation.guest.first_name} ${reservation.guest.last_name}`}>
            <dl className="divide-y divide-gray-200">
              <div className="py-2 sm:grid sm:grid-cols-3 sm:gap-4">
                <dt className="text-sm font-medium text-brand-text-secondary">Email</dt>
                <dd className="mt-1 text-sm text-brand-text-primary sm:mt-0 sm:col-span-2">{reservation.guest.email || 'N/A'}</dd>
              </div>
              <div className="py-2 sm:grid sm:grid-cols-3 sm:gap-4">
                <dt className="text-sm font-medium text-brand-text-secondary">Teléfono</dt>
                <dd className="mt-1 text-sm text-brand-text-primary sm:mt-0 sm:col-span-2">{reservation.guest.phone_number || 'N/A'}</dd>
              </div>
              <div className="py-2 sm:grid sm:grid-cols-3 sm:gap-4">
                <dt className="text-sm font-medium text-brand-text-secondary">Documento</dt>
                <dd className="mt-1 text-sm text-brand-text-primary sm:mt-0 sm:col-span-2">{reservation.guest.document_type ? `${reservation.guest.document_type}: ${reservation.guest.document_number || ''}` : (reservation.guest.document_number || 'N/A')}</dd>
              </div>
              <div className="mt-4">
                 <Link to={`/dashboard/guests/${reservation.guest.id}/view`} className="text-sm text-brand-primary hover:underline">Ver Perfil Completo del Huésped &rarr;</Link>
              </div>
            </dl>
          </Card>
        )}

        {reservation.room && (
          <Card className="lg:col-span-1" title={`Habitación: ${reservation.room.name} (#${reservation.room.room_number})`}>
            <dl className="divide-y divide-gray-200">
              <div className="py-2 sm:grid sm:grid-cols-3 sm:gap-4">
                <dt className="text-sm font-medium text-brand-text-secondary">Tipo</dt>
                <dd className="mt-1 text-sm text-brand-text-primary sm:mt-0 sm:col-span-2">{reservation.room.type}</dd>
              </div>
              <div className="py-2 sm:grid sm:grid-cols-3 sm:gap-4">
                <dt className="text-sm font-medium text-brand-text-secondary">Precio Base</dt>
                <dd className="mt-1 text-sm text-brand-text-primary sm:mt-0 sm:col-span-2">S/ {Number(reservation.room.price).toFixed(2)} PEN</dd>
              </div>
              <div className="py-2 sm:grid sm:grid-cols-3 sm:gap-4">
                <dt className="text-sm font-medium text-brand-text-secondary">Estado Actual</dt>
                <dd className="mt-1 text-sm text-brand-text-primary sm:mt-0 sm:col-span-2">{reservation.room.status}</dd>
              </div>
               <div className="mt-4">
                 <Link to={`/dashboard/rooms/${reservation.room.id}/view`} className="text-sm text-brand-primary hover:underline">Ver Detalles Completos de Habitación &rarr;</Link>
              </div>
            </dl>
          </Card>
        )}
      </div>
    </div>
  );
};

export default ReservationDetailPage;
