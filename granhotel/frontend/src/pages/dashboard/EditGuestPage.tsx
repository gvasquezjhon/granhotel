// src/pages/dashboard/EditGuestPage.tsx
import React from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { guestService } from '../../services/guestService';
import { GuestFormInputs } from '../../types/guestSchemas';
import { Guest, GuestUpdatePayload } from '../../types/guest'; // Import GuestUpdatePayload
import GuestForm from '../../components/guests/GuestForm';
import Card from '../../components/ui/Card';
import { useToast } from '../../contexts/ToastContext';
import { useAuth } from '../../contexts/AuthContext';
import { UserRole } from '../../types/user';


const EditGuestPage: React.FC = () => {
  const { guestId } = useParams<{ guestId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  const { user } = useAuth();

  // Permission check
  if (!user || ![UserRole.ADMIN, UserRole.MANAGER].includes(user.role)) {
     return (
        <div className="p-6 text-red-600">
            No tiene los permisos necesarios para editar huéspedes.
            <Link to="/dashboard/guests" className="block mt-2 text-brand-primary hover:underline">Volver al panel</Link>
        </div>
     );
  }

  const { data: guest, isLoading: isLoadingGuest, isError, error: guestError } = useQuery<Guest, Error>({
    queryKey: ['guest', guestId], // guestId is string from URL
    queryFn: () => guestId ? guestService.getGuestById(guestId) : Promise.reject(new Error("ID de huésped inválido")),
    enabled: !!guestId,
  });

  const updateGuestMutation = useMutation({
    mutationFn: (data: { id: string; payload: GuestUpdatePayload }) => guestService.updateGuest(data.id, data.payload),
    onSuccess: (updatedGuest) => {
      queryClient.invalidateQueries({ queryKey: ['guests'] });
      queryClient.invalidateQueries({ queryKey: ['guest', updatedGuest.id] });
      addToast(`Huésped "${updatedGuest.first_name} ${updatedGuest.last_name}" actualizado con éxito.`, 'success');
      navigate(`/dashboard/guests/${updatedGuest.id}/view`);
    },
    onError: (error: any) => {
      const errorMsg = error.response?.data?.detail || error.message || "Ocurrió un error desconocido.";
      addToast(`Error al actualizar huésped: ${errorMsg}`, 'error');
    },
  });

  const handleSubmitForm = (data: GuestFormInputs) => {
    if (!guestId) return;
     const payload: GuestUpdatePayload = {
      ...data,
      email: data.email === '' ? null : data.email,
      phone_number: data.phone_number || null,
      document_type: data.document_type || null,
      document_number: data.document_number || null,
      address_street: data.address_street || null,
      address_city: data.address_city || null,
      address_state_province: data.address_state_province || null,
      address_postal_code: data.address_postal_code || null,
      address_country: data.address_country || undefined, // Backend default if null, or send current value
      nationality: data.nationality || undefined, // Backend default if null
      preferences: data.preferences || null,
      // is_blacklisted is part of GuestFormInputs and will be included.
      // The backend GuestUpdatePayload schema has all fields optional.
    };
    updateGuestMutation.mutate({ id: guestId, payload });
  };

  if (!guestId && !isLoadingGuest) return (
    <div className="p-4 text-red-500 text-center">
        ID de huésped no válido.
        <Link to="/dashboard/guests" className="block mt-2 text-brand-primary hover:underline">Volver</Link>
    </div>
  );
  if (isLoadingGuest) return <div className="p-6 text-center text-brand-text-secondary">Cargando datos del huésped...</div>;
  if (isError || !guest) return <div className="p-4 bg-red-100 text-red-700 rounded-md text-center">Error al cargar huésped: {guestError?.message || "No encontrado"}. <Link to="/dashboard/guests" className="block mt-2 font-semibold text-brand-primary hover:underline">Volver</Link></div>;

  // Prepare initialData for the form, ensuring all form fields are accounted for.
  // GuestForm's defaultValues and useEffect handle merging and type transformations.
  const initialFormData: Partial<GuestFormInputs> = {
     first_name: guest.first_name,
     last_name: guest.last_name,
     email: guest.email || '', // Ensure empty string for controlled input if null
     phone_number: guest.phone_number || undefined,
     document_type: guest.document_type || undefined,
     document_number: guest.document_number || undefined,
     address_street: guest.address_street || undefined,
     address_city: guest.address_city || undefined,
     address_state_province: guest.address_state_province || undefined,
     address_postal_code: guest.address_postal_code || undefined,
     address_country: guest.address_country || "Perú",
     nationality: guest.nationality || "Peruana",
     preferences: guest.preferences || undefined,
     is_blacklisted: guest.is_blacklisted,
  };


  return (
    <div className="animate-fadeIn">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold text-brand-text-primary">Editar Huésped: {guest.first_name} {guest.last_name}</h1>
        <Link
            to={`/dashboard/guests/${guest.id}/view`}
            className="text-sm text-brand-primary hover:text-brand-primary-dark hover:underline"
        >
            &larr; Volver a detalles
        </Link>
      </div>
      <Card>
        <GuestForm
          onSubmit={handleSubmitForm}
          initialData={initialFormData}
          isLoading={updateGuestMutation.isPending}
          submitButtonText="Guardar Cambios"
          isEditMode={true}
        />
      </Card>
    </div>
  );
};
export default EditGuestPage;
