// src/components/rooms/RoomForm.tsx
import React, { useEffect } from 'react';
import { useForm, SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { RoomFormInputs, roomFormSchema, availableRoomStatuses } from '../../types/roomSchemas';
import Input from '../ui/Input';
import Button from '../ui/Button';
import Select from '../ui/Select';
import Textarea from '../ui/Textarea';

interface RoomFormProps {
  onSubmit: SubmitHandler<RoomFormInputs>;
  initialData?: Partial<RoomFormInputs>;
  isLoading?: boolean;
  submitButtonText?: string;
  existingRoomNumber?: string; // To compare for changes if needed for validation (though Zod handles it)
}

const RoomForm: React.FC<RoomFormProps> = ({
  onSubmit,
  initialData,
  isLoading = false,
  submitButtonText = "Guardar Habitación"
  // existingRoomNumber // Not used directly here, Zod schema handles validation
}) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setValue,
  } = useForm<RoomFormInputs>({
    resolver: zodResolver(roomFormSchema),
    defaultValues: initialData ?
      { // Ensure all fields are present, even if undefined, for controlled components
        name: initialData.name || "",
        room_number: initialData.room_number || "",
        type: initialData.type || "",
        price: initialData.price ? Number(initialData.price) : 0.00,
        status: initialData.status || "Available",
        floor: initialData.floor ? Number(initialData.floor) : undefined, // Keep as undefined if null/empty
        building: initialData.building || "",
        description: initialData.description || "",
      }
      : { status: "Available", price: 0.00, floor: undefined, building: "", description: "" },
  });

  useEffect(() => {
    if (initialData) {
      // Reset form with initialData when it changes (e.g., after fetching data for edit)
      // Ensure numeric fields are numbers. Zod preprocess helps, but direct reset is good.
      const transformedInitialData = {
        ...initialData,
        price: initialData.price ? parseFloat(String(initialData.price)) : 0.00,
        floor: initialData.floor ? parseInt(String(initialData.floor), 10) : undefined,
        // Ensure optional fields that might be null/undefined are handled if `reset` expects them
        building: initialData.building || undefined, // or null if schema allows
        description: initialData.description || undefined, // or null
      };
      reset(transformedInitialData);
    }
  }, [initialData, reset]);

  const statusOptions = availableRoomStatuses.map(status => ({ value: status, label: status }));

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 md:space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input label="Nombre de Habitación" id="name" registration={register('name')} error={errors.name?.message} placeholder="Ej: Suite Presidencial, Habitación 201 Deluxe"/>
        <Input label="Número de Habitación" id="room_number" registration={register('room_number')} error={errors.room_number?.message} placeholder="Ej: 101, A203"/>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input label="Tipo (Ej: Simple, Doble, Suite)" id="type" registration={register('type')} error={errors.type?.message} placeholder="Ej: Doble Matrimonial"/>
        <Input
          label="Precio por Noche (PEN)"
          id="price"
          type="number" // HTML5 number input
          registration={register('price')}
          error={errors.price?.message}
          step="0.01" // For decimal values
          placeholder="Ej: 150.00"
        />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
         <Select
             label="Estado"
             id="status"
             registration={register('status')}
             options={statusOptions}
             error={errors.status?.message}
         />
        <Input
          label="Piso (Opcional)"
          id="floor"
          type="number"
          registration={register('floor')}
          error={errors.floor?.message}
          placeholder="Ej: 1, 10"
        />
      </div>
      <Input label="Edificio/Sección (Opcional)" id="building" registration={register('building')} error={errors.building?.message} placeholder="Ej: Torre A, Ala Norte"/>
      <Textarea label="Descripción (Opcional)" id="description" registration={register('description')} error={errors.description?.message} rows={4} placeholder="Detalles adicionales de la habitación..."/>

      <div className="pt-2">
        <Button type="submit" isLoading={isLoading} className="w-full md:w-auto" variant="primary">
          {isLoading ? "Guardando..." : submitButtonText}
        </Button>
      </div>
    </form>
  );
};
export default RoomForm;
