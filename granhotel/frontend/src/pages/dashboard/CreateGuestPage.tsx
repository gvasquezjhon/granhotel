// src/pages/dashboard/CreateGuestPage.tsx
import React from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate, Link }  from 'react-router-dom';
import { guestService } from '../../services/guestService';
import { GuestFormInputs } from '../../types/guestSchemas';
import { GuestCreatePayload } from '../../types/guest'; // For payload type
import GuestForm from '../../components/guests/GuestForm';
import Card from '../../components/ui/Card';
import { useToast } from '../../contexts/ToastContext';
import { useAuth } from '../../contexts/AuthContext';
import { UserRole } from '../../types/user';

const CreateGuestPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  const { user } = useAuth();

  // Basic permission check, primarily route protection should handle this
  if (!user || ![UserRole.ADMIN, UserRole.MANAGER, UserRole.RECEPTIONIST].includes(user.role)) {
     return (
        <div className="p-6 text-red-600">
            No tiene los permisos necesarios para registrar nuevos huéspedes.
            <Link to="/dashboard" className="block mt-2 text-brand-primary hover:underline">Volver al panel</Link>
        </div>
     );
  }

  const createGuestMutation = useMutation({
    mutationFn: (payload: GuestCreatePayload) => guestService.createGuest(payload),
    onSuccess: (newGuest) => {
      queryClient.invalidateQueries({ queryKey: ['guests'] });
      addToast(`Huésped "${newGuest.first_name} ${newGuest.last_name}" registrado con éxito.`, 'success');
      navigate('/dashboard/guests');
    },
    onError: (error: any) => {
      const errorMsg = error.response?.data?.detail || error.message || "Ocurrió un error desconocido.";
      addToast(`Error al registrar huésped: ${errorMsg}`, 'error');
    },
  });

  const handleSubmitForm = (data: GuestFormInputs) => {
    // Transform form data to match GuestCreatePayload, especially for nulls/undefined
    const payload: GuestCreatePayload = {
      ...data,
      email: data.email === '' ? null : data.email,
      phone_number: data.phone_number || null,
      document_type: data.document_type || null,
      document_number: data.document_number || null,
      address_street: data.address_street || null,
      address_city: data.address_city || null,
      address_state_province: data.address_state_province || null,
      address_postal_code: data.address_postal_code || null,
      address_country: data.address_country || "Perú", // Default if empty, though schema defaults it
      nationality: data.nationality || "Peruana", // Default if empty
      preferences: data.preferences || null,
      is_blacklisted: data.is_blacklisted || false, // Default from schema
    };
    createGuestMutation.mutate(payload);
  };

  return (
    <div className="animate-fadeIn">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold text-brand-text-primary">Registrar Nuevo Huésped</h1>
        <Link
            to="/dashboard/guests"
            className="text-sm text-brand-primary hover:text-brand-primary-dark hover:underline"
        >
            &larr; Volver a la lista
        </Link>
      </div>
      <Card>
        <GuestForm
          onSubmit={handleSubmitForm}
          isLoading={createGuestMutation.isPending}
          submitButtonText="Registrar Huésped"
          isEditMode={false}
        />
      </Card>
    </div>
  );
};
export default CreateGuestPage;
