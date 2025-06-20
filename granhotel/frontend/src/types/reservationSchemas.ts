// src/types/reservationSchemas.ts
import { z } from 'zod';
import { ReservationStatus } from './reservation'; // Assuming ReservationStatus enum exists

export const availableReservationStatuses: [ReservationStatus, ...ReservationStatus[]] = [
    ReservationStatus.PENDING,
    ReservationStatus.CONFIRMED,
    // CHECKED_IN is typically set by a specific action, not a general form status update.
];

// For edit mode, might want a broader set of statuses if admins can change more freely
export const editableReservationStatuses: [ReservationStatus, ...ReservationStatus[]] = [
    ReservationStatus.PENDING,
    ReservationStatus.CONFIRMED,
    ReservationStatus.CHECKED_IN, // Manager might set this if needed
    ReservationStatus.NO_SHOW,
    ReservationStatus.CANCELLED, // Manager might set this directly here too
    ReservationStatus.WAITLIST,
];


export const reservationFormSchema = z.object({
  guest_id: z.string().uuid({ message: "ID de huésped debe ser un UUID válido." }),
  room_id: z.preprocess(
     (val) => (typeof val === 'string' && val.trim() !== '' ? parseInt(val, 10) : (typeof val === 'number' ? val : undefined)),
     z.number({ required_error: "ID de habitación es requerido.", invalid_type_error: "ID de habitación debe ser un número."})
      .int({ message: "ID de habitación debe ser un número entero."})
      .positive({ message: "ID de habitación debe ser positivo." })
  ),
  check_in_date: z.string()
    .min(10, { message: "Fecha de Check-in es requerida (YYYY-MM-DD)." }) // Basic check for non-empty
    .regex(/^\d{4}-\d{2}-\d{2}$/, { message: "Formato de Check-in debe ser YYYY-MM-DD."}),
  check_out_date: z.string()
    .min(10, { message: "Fecha de Check-out es requerida (YYYY-MM-DD)." })
    .regex(/^\d{4}-\d{2}-\d{2}$/, { message: "Formato de Check-out debe ser YYYY-MM-DD."}),
  status: z.nativeEnum(ReservationStatus, { errorMap: () => ({ message: "Seleccione un estado válido."}) }),
  notes: z.string().max(500, "Notas no deben exceder 500 caracteres.").optional().nullable(),
}).superRefine((data, ctx) => {
  if (data.check_in_date && data.check_out_date) {
    try {
      // Add T00:00:00 to ensure consistent parsing as local date, avoiding timezone shifts from just date string
      const checkIn = new Date(data.check_in_date + "T00:00:00");
      const checkOut = new Date(data.check_out_date + "T00:00:00");
      if (checkOut <= checkIn) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ['check_out_date'],
          message: "Fecha de Check-out debe ser posterior a la fecha de Check-in.",
        });
      }
      // Optional: Minimum stay duration (e.g., 1 day)
      const diffTime = checkOut.getTime() - checkIn.getTime(); // Difference in milliseconds
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)); // Difference in days
      if (diffDays < 1) {
         ctx.addIssue({
           code: z.ZodIssueCode.custom,
           path: ['check_out_date'],
           message: "La estadía mínima es de 1 noche.",
         });
      }
    } catch (e) {
      // If date parsing fails, individual regex checks should catch it.
      // This try-catch is a safeguard for date object operations.
       ctx.addIssue({
           code: z.ZodIssueCode.custom,
           path: ['check_in_date'], // Or a general form error
           message: "Fechas inválidas.",
         });
    }
  }
});

export type ReservationFormInputs = z.infer<typeof reservationFormSchema>;
