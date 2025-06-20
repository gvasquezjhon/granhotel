// src/components/reservations/ReservationForm.tsx
import React, { useEffect } from 'react';
import { useForm, SubmitHandler, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { ReservationFormInputs, reservationFormSchema, availableReservationStatuses, editableReservationStatuses } from '../../types/reservationSchemas';
import { ReservationStatus } from '../../types/reservation'; // Enum for default value
import Input from '../ui/Input';
import Button from '../ui/Button';
import Select from '../ui/Select';
import Textarea from '../ui/Textarea';
import DatePicker, { registerLocale } from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { es } from 'date-fns/locale'; // Import es directly
registerLocale('es', es);

interface ReservationFormProps {
  onSubmit: SubmitHandler<ReservationFormInputs>;
  initialData?: Partial<ReservationFormInputs>;
  isLoading?: boolean;
  submitButtonText?: string;
  isEditMode?: boolean;
}

const ReservationForm: React.FC<ReservationFormProps> = ({
  onSubmit,
  initialData,
  isLoading = false,
  submitButtonText = "Guardar Reserva",
  isEditMode = false
}) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    control,
    watch
  } = useForm<ReservationFormInputs>({
    resolver: zodResolver(reservationFormSchema),
    defaultValues: initialData || {
        status: ReservationStatus.PENDING,
        // Initialize other fields to prevent uncontrolled to controlled warning if needed
        guest_id: '',
        room_id: undefined, // Or a valid default number if that makes sense (e.g. 0, then Zod catches it)
        check_in_date: '',
        check_out_date: '',
        notes: ''
    },
  });

  useEffect(() => {
    if (initialData) {
      const transformedData = {
        ...initialData,
        // Dates in initialData are expected to be "YYYY-MM-DD" strings.
        // DatePicker's Controller will handle parsing these to Date objects for the picker.
        check_in_date: initialData.check_in_date || '',
        check_out_date: initialData.check_out_date || '',
        room_id: initialData.room_id ? Number(initialData.room_id) : undefined,
        notes: initialData.notes || '', // Ensure empty string if null/undefined for textarea
      };
      reset(transformedData);
    }
  }, [initialData, reset]);

  const statusOptionsToUse = isEditMode ? editableReservationStatuses : availableReservationStatuses;
  const statusOptions = statusOptionsToUse.map(s => ({ value: s, label: s.replace('_', ' ') }));

  const watchCheckInDateStr = watch("check_in_date");
  const minCheckoutDate = watchCheckInDateStr
    ? new Date(new Date(watchCheckInDateStr + "T00:00:00").setDate(new Date(watchCheckInDateStr + "T00:00:00").getDate() + 1))
    : new Date(new Date().setDate(new Date().getDate() + 1));


  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 md:space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2">
        <Input
          label="ID de Huésped (UUID)"
          id="guest_id"
          registration={register('guest_id')}
          error={errors.guest_id?.message}
          placeholder="ID de Huésped existente"
          helperText="Debe ser un UUID válido de un huésped registrado."
        />
        <Input
          label="ID de Habitación"
          id="room_id"
          type="number"
          registration={register('room_id')}
          error={errors.room_id?.message}
          placeholder="ID Numérico de Habitación"
          helperText="ID de una habitación existente y disponible."
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2">
         <div>
             <label htmlFor="check_in_date" className="block text-sm font-medium text-brand-text-secondary mb-1">Fecha de Check-in</label>
             <Controller
                 control={control}
                 name="check_in_date"
                 render={({ field }) => (
                     <DatePicker
                         selected={field.value ? new Date(field.value + "T00:00:00") : null}
                         onChange={(date) => field.onChange(date ? date.toISOString().split('T')[0] : '')}
                         dateFormat="dd/MM/yyyy"
                         locale="es"
                         className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-primary"
                         placeholderText="Seleccione fecha check-in"
                         minDate={new Date()}
                     />
                 )}
             />
             {errors.check_in_date && <p className="mt-1 text-xs text-red-600">{errors.check_in_date.message}</p>}
         </div>
         <div>
             <label htmlFor="check_out_date" className="block text-sm font-medium text-brand-text-secondary mb-1">Fecha de Check-out</label>
             <Controller
                 control={control}
                 name="check_out_date"
                 render={({ field }) => (
                     <DatePicker
                         selected={field.value ? new Date(field.value + "T00:00:00") : null}
                         onChange={(date) => field.onChange(date ? date.toISOString().split('T')[0] : '')}
                         dateFormat="dd/MM/yyyy"
                         locale="es"
                         className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-primary"
                         placeholderText="Seleccione fecha check-out"
                         minDate={minCheckoutDate}
                     />
                 )}
             />
             {errors.check_out_date && <p className="mt-1 text-xs text-red-600">{errors.check_out_date.message}</p>}
         </div>
      </div>

      <Select
         label="Estado de Reserva"
         id="status"
         registration={register('status')}
         options={statusOptions}
         error={errors.status?.message}
      />
      <Textarea label="Notas (Opcional)" id="notes" registration={register('notes')} error={errors.notes?.message} rows={3} placeholder="Añadir notas o pedidos especiales..."/>

      <div className="pt-2">
        <Button type="submit" isLoading={isLoading} className="w-full md:w-auto" variant="primary">
          {isLoading ? "Guardando..." : submitButtonText}
        </Button>
      </div>
    </form>
  );
};
export default ReservationForm;
