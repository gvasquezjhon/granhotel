// src/components/guests/GuestForm.tsx
import React, { useEffect } from 'react';
import { useForm, SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { GuestFormInputs, guestFormSchema, documentTypesArray } from '../../types/guestSchemas';
import { DocumentType } from '../../types/guest'; // Enum for values
import Input from '../ui/Input';
import Button from '../ui/Button';
import Select from '../ui/Select';
import Textarea from '../ui/Textarea';
import Checkbox from '../ui/Checkbox';

interface GuestFormProps {
  onSubmit: SubmitHandler<GuestFormInputs>;
  initialData?: Partial<GuestFormInputs>;
  isLoading?: boolean;
  submitButtonText?: string;
  isEditMode?: boolean;
}

const GuestForm: React.FC<GuestFormProps> = ({
  onSubmit,
  initialData,
  isLoading = false,
  submitButtonText = "Guardar Huésped",
  isEditMode = false
}) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch
  } = useForm<GuestFormInputs>({
    resolver: zodResolver(guestFormSchema),
    defaultValues: initialData ?
      { // Ensure all fields are present, even if undefined, for controlled components
        first_name: initialData.first_name || "",
        last_name: initialData.last_name || "",
        email: initialData.email || "", // Default to empty string for controlled input
        phone_number: initialData.phone_number || undefined,
        document_type: initialData.document_type || undefined, // Keep undefined if null/empty
        document_number: initialData.document_number || undefined,
        address_street: initialData.address_street || undefined,
        address_city: initialData.address_city || undefined,
        address_state_province: initialData.address_state_province || undefined,
        address_postal_code: initialData.address_postal_code || undefined,
        address_country: initialData.address_country || "Perú",
        nationality: initialData.nationality || "Peruana",
        preferences: initialData.preferences || undefined,
        is_blacklisted: initialData.is_blacklisted || false,
      }
      : {
          is_blacklisted: false,
          address_country: "Perú",
          nationality: "Peruana",
          // Set other optionals to empty string or undefined for controlled inputs
          email: "",
          phone_number: undefined,
          document_type: undefined,
          document_number: undefined,
          address_street: undefined,
          address_city: undefined,
          address_state_province: undefined,
          address_postal_code: undefined,
          preferences: undefined,
      },
  });

  useEffect(() => {
    if (initialData) {
      const transformedInitialData = {
         ...initialData,
         email: initialData.email || '', // Default to empty string for input
         phone_number: initialData.phone_number ?? undefined,
         document_type: initialData.document_type ?? undefined,
         document_number: initialData.document_number ?? undefined,
         address_street: initialData.address_street ?? undefined,
         address_city: initialData.address_city ?? undefined,
         address_state_province: initialData.address_state_province ?? undefined,
         address_postal_code: initialData.address_postal_code ?? undefined,
         address_country: initialData.address_country || "Perú",
         nationality: initialData.nationality || "Peruana",
         preferences: initialData.preferences ?? undefined,
         is_blacklisted: initialData.is_blacklisted || false,
      };
      reset(transformedInitialData);
    }
  }, [initialData, reset]);

  const docTypeOptions = documentTypesArray.map(dt => ({ value: dt, label: dt }));
  // Add a "none" option for document_type
  const docTypeOptionsWithNone = [{ value: "", label: "No especificar" }, ...docTypeOptions];


  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 md:space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2"> {/* Reduced y-gap */}
        <Input label="Nombres" id="first_name" registration={register('first_name')} error={errors.first_name?.message} placeholder="Juan"/>
        <Input label="Apellidos" id="last_name" registration={register('last_name')} error={errors.last_name?.message} placeholder="Pérez"/>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2">
        <Input label="Correo Electrónico (Opcional)" id="email" type="email" registration={register('email')} error={errors.email?.message} placeholder="juan.perez@example.com"/>
        <Input label="Teléfono (Opcional)" id="phone_number" registration={register('phone_number')} error={errors.phone_number?.message} placeholder="+51 987654321"/>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2">
         <Select
             label="Tipo de Documento (Opcional)"
             id="document_type"
             registration={register('document_type')}
             options={docTypeOptionsWithNone}
             error={errors.document_type?.message}
             // placeholder="Seleccione un tipo" // Using "No especificar" option instead
         />
        <Input label="Número de Documento (Opcional)" id="document_number" registration={register('document_number')} error={errors.document_number?.message} placeholder="Ej: 12345678"/>
      </div>
      <h3 className="text-md font-semibold text-brand-text-primary pt-3 border-b pb-1 mb-3">Dirección (Opcional)</h3> {/* Added margin bottom */}
      <Input label="Calle / Avenida" id="address_street" registration={register('address_street')} error={errors.address_street?.message} placeholder="Av. Principal 123"/>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-x-4 gap-y-2">
         <Input label="Ciudad" id="address_city" registration={register('address_city')} error={errors.address_city?.message} placeholder="Lima"/>
         <Input label="Región/Provincia" id="address_state_province" registration={register('address_state_province')} error={errors.address_state_province?.message} placeholder="Lima"/>
         <Input label="Código Postal" id="address_postal_code" registration={register('address_postal_code')} error={errors.address_postal_code?.message} placeholder="Lima 01"/>
      </div>
      <Input label="País" id="address_country" registration={register('address_country')} error={errors.address_country?.message} />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2 pt-2">
         <Input label="Nacionalidad (Opcional)" id="nationality" registration={register('nationality')} error={errors.nationality?.message} />
         {isEditMode && (
             <Checkbox label="En Lista Negra" id="is_blacklisted" registration={register('is_blacklisted')} error={errors.is_blacklisted?.message} />
         )}
      </div>
      <Textarea label="Preferencias (Opcional)" id="preferences" registration={register('preferences')} error={errors.preferences?.message} rows={3} placeholder="Ej: Habitación tranquila, piso alto..."/>

      <div className="pt-2">
        <Button type="submit" isLoading={isLoading} className="w-full md:w-auto" variant="primary">
          {isLoading ? "Guardando..." : submitButtonText}
        </Button>
      </div>
    </form>
  );
};
export default GuestForm;
