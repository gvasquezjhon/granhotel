// src/types/roomSchemas.ts
import { z } from 'zod';
import { RoomStatus } from './room'; // Assuming RoomStatus type from room.ts

// Available statuses for selection in a form
// Zod enum needs at least one value, and then others.
// So, if RoomStatus has "Available", "Occupied", "Maintenance", "Cleaning"
// then availableRoomStatuses should be ["Available", "Occupied", "Maintenance", "Cleaning"]
// Ensure this matches the RoomStatus type exactly for z.enum.
export const availableRoomStatuses: [RoomStatus, ...RoomStatus[]] = [
    "Available", "Occupied", "Maintenance", "Cleaning"
];

export const roomFormSchema = z.object({
  name: z.string().min(3, { message: "El nombre debe tener al menos 3 caracteres." }).max(100, { message: "El nombre no puede exceder los 100 caracteres." }),
  room_number: z.string().min(1, { message: "El número de habitación es obligatorio." }).max(10, { message: "El número no puede exceder los 10 caracteres." }),
  type: z.string().min(3, { message: "El tipo de habitación es obligatorio." }).max(50),
  price: z.preprocess(
    (val) => {
      if (typeof val === 'string') {
        const parsed = parseFloat(val.replace(',', '.')); // Handle comma as decimal separator
        return isNaN(parsed) ? undefined : parsed;
      }
      return val;
    },
    z.number({ invalid_type_error: "El precio debe ser un número." }).positive({ message: "El precio debe ser mayor que cero." })
  ),
  status: z.enum(availableRoomStatuses, {
    errorMap: (issue, ctx) => ({ message: "Seleccione un estado válido para la habitación." })
  }),
  floor: z.preprocess(
     (val) => (val === '' || val === null || val === undefined ? null : parseInt(String(val), 10)),
     z.number().int({ message: "El piso debe ser un número entero."}).positive({ message: "El piso debe ser un número positivo."}).nullable().optional()
  ).refine(val => val === null || (val !== null && !isNaN(val)), {
    message: "El piso debe ser un número entero positivo o estar vacío."
  }),
  building: z.string().max(50, {message: "Edificio no puede exceder 50 caracteres."}).optional().nullable(),
  description: z.string().max(500, {message: "Descripción no puede exceder 500 caracteres."}).optional().nullable(),
});

export type RoomFormInputs = z.infer<typeof roomFormSchema>;
