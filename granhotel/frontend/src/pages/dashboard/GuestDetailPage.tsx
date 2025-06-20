// src/pages/dashboard/GuestDetailPage.tsx
import React from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { guestService } from '../../services/guestService';
import { Guest } from '../../types/guest';
import { useAuth } from '../../contexts/AuthContext';
import { UserRole } from '../../types/user';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import { useToast } from '../../contexts/ToastContext'; // For blacklist update feedback

const GuestDetailPage: React.FC = () => {
  const { guestId } = useParams<{ guestId: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  const canManageGuest = user?.role === UserRole.ADMIN || user?.role === UserRole.MANAGER;

  const {
    data: guest,
    isLoading,
    isError,
    error
  } = useQuery<Guest, Error>({
    queryKey: ['guest', guestId],
    queryFn: () => {
      if (!guestId) {
        return Promise.reject(new Error("ID de huésped es requerido."));
      }
      // guestId from useParams is string, service expects string for UUIDs
      return guestService.getGuestById(guestId);
    },
    enabled: !!guestId,
  });

  const blacklistMutation = useMutation({
     mutationFn: (data: { guestId: string; blacklistStatus: boolean }) =>
         guestService.updateGuestBlacklistStatus(data.guestId, { blacklist_status: data.blacklistStatus }),
     onSuccess: (updatedGuest) => {
       queryClient.invalidateQueries({ queryKey: ['guests'] });
       queryClient.invalidateQueries({ queryKey: ['guest', updatedGuest.id]});
       addToast(`Estado de lista negra para ${updatedGuest.first_name} ${updatedGuest.last_name} actualizado.`, 'success');
     },
     onError: (err: Error) => {
       addToast(`Error al actualizar lista negra: ${err.message}`, 'error');
     }
  });

  const handleBlacklistToggle = () => {
     if (!guest) return;
     const newStatus = !guest.is_blacklisted;
     const action = newStatus ? "agregar a" : "quitar de";
     if (window.confirm(`¿Está seguro de que desea ${action} la lista negra a ${guest.first_name} ${guest.last_name}?`)) {
         blacklistMutation.mutate({ guestId: guest.id, blacklistStatus: newStatus });
     }
  };

  if (!guestId) {
    return (
      <div className="p-4 text-center text-red-600">
        Error: No se especificó el ID del huésped.
        <Link to="/dashboard/guests" className="block mt-4 text-brand-primary hover:underline">Volver a la lista de huéspedes</Link>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <p className="text-brand-text-secondary">Cargando detalles del huésped...</p>
      </div>
    );
  }

  if (isError || !guest) {
    return (
      <div className="p-4 bg-red-100 border border-red-400 text-red-700 rounded-md">
        <p className="font-semibold">Error al cargar detalles del huésped:</p>
        <p>{error?.message || 'Huésped no encontrado o error desconocido.'}</p>
        <Link to="/dashboard/guests" className="block mt-4 text-brand-primary hover:underline">Volver a la lista de huéspedes</Link>
      </div>
    );
  }

  const formatAddress = (g: Guest) => {
     const parts = [g.address_street, g.address_city, g.address_state_province, g.address_postal_code, g.address_country];
     return parts.filter(Boolean).join(', ') || 'No especificada';
  }

  return (
    <div className="animate-fadeIn">
      <div className="flex flex-wrap justify-between items-center mb-6 gap-4">
        <h1 className="text-2xl sm:text-3xl font-semibold text-brand-text-primary">
          Detalle de Huésped: {guest.first_name} {guest.last_name}
        </h1>
        <Button onClick={() => navigate('/dashboard/guests')} variant="secondary" className="w-auto text-sm sm:text-base">
          &larr; Volver a la Lista
        </Button>
      </div>

      <Card>
        <dl className="divide-y divide-gray-200">
          <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4">
            <dt className="text-sm font-medium text-brand-text-secondary">Nombre Completo</dt>
            <dd className="mt-1 text-sm text-brand-text-primary sm:mt-0 sm:col-span-2">{guest.first_name} {guest.last_name}</dd>
          </div>
          <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4">
            <dt className="text-sm font-medium text-brand-text-secondary">Email</dt>
            <dd className="mt-1 text-sm text-brand-text-primary sm:mt-0 sm:col-span-2">{guest.email || 'No especificado'}</dd>
          </div>
          <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4">
            <dt className="text-sm font-medium text-brand-text-secondary">Teléfono</dt>
            <dd className="mt-1 text-sm text-brand-text-primary sm:mt-0 sm:col-span-2">{guest.phone_number || 'No especificado'}</dd>
          </div>
          <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4">
            <dt className="text-sm font-medium text-brand-text-secondary">Tipo de Documento</dt>
            <dd className="mt-1 text-sm text-brand-text-primary sm:mt-0 sm:col-span-2">{guest.document_type || 'No especificado'}</dd>
          </div>
          <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4">
            <dt className="text-sm font-medium text-brand-text-secondary">Número de Documento</dt>
            <dd className="mt-1 text-sm text-brand-text-primary sm:mt-0 sm:col-span-2">{guest.document_number || 'No especificado'}</dd>
          </div>
          <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4">
            <dt className="text-sm font-medium text-brand-text-secondary">Nacionalidad</dt>
            <dd className="mt-1 text-sm text-brand-text-primary sm:mt-0 sm:col-span-2">{guest.nationality || 'No especificada'}</dd>
          </div>
          <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4">
            <dt className="text-sm font-medium text-brand-text-secondary">Dirección</dt>
            <dd className="mt-1 text-sm text-brand-text-primary sm:mt-0 sm:col-span-2">{formatAddress(guest)}</dd>
          </div>
          <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4">
            <dt className="text-sm font-medium text-brand-text-secondary">Preferencias</dt>
            <dd className="mt-1 text-sm text-brand-text-primary sm:mt-0 sm:col-span-2 whitespace-pre-wrap">{guest.preferences || 'Ninguna especificada'}</dd>
          </div>
          <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4">
            <dt className="text-sm font-medium text-brand-text-secondary">En Lista Negra</dt>
            <dd className={`mt-1 text-sm font-semibold sm:mt-0 sm:col-span-2 ${guest.is_blacklisted ? 'text-red-600' : 'text-green-600'}`}>
              {guest.is_blacklisted ? 'Sí' : 'No'}
            </dd>
          </div>
          <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4">
            <dt className="text-sm font-medium text-brand-text-secondary">Registrado</dt>
            <dd className="mt-1 text-sm text-brand-text-primary sm:mt-0 sm:col-span-2">{new Date(guest.created_at).toLocaleString('es-PE', { dateStyle: 'long', timeStyle: 'short' })}</dd>
          </div>
          <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4">
            <dt className="text-sm font-medium text-brand-text-secondary">Última Actualización</dt>
            <dd className="mt-1 text-sm text-brand-text-primary sm:mt-0 sm:col-span-2">{new Date(guest.updated_at).toLocaleString('es-PE', { dateStyle: 'long', timeStyle: 'short' })}</dd>
          </div>
        </dl>

        {canManageGuest && (
          <div className="mt-6 pt-6 border-t border-gray-200 flex flex-wrap gap-3 justify-end">
            <Button
              onClick={handleBlacklistToggle}
              variant={guest.is_blacklisted ? 'secondary' : 'danger'}
              className="w-auto"
              isLoading={blacklistMutation.isPending}
            >
              {guest.is_blacklisted ? 'Quitar de Lista Negra' : 'Añadir a Lista Negra'}
            </Button>
            <Button
              onClick={() => navigate(`/dashboard/guests/${guest.id}/edit`)}
              variant="primary"
              className="w-auto"
            >
              Editar Huésped
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
};

export default GuestDetailPage;
