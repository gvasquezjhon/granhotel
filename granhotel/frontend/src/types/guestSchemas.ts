// src/types/guestSchemas.ts
import { z } from 'zod';
import { DocumentType } from './guest'; // Assuming DocumentType enum is in guest.ts

export const documentTypesArray: [DocumentType, ...DocumentType[]] = [
    DocumentType.DNI,
    DocumentType.RUC,
    DocumentType.PASSPORT,
    DocumentType.CE
]; // This ensures Zod's enum has at least one value.

export const guestFormSchema = z.object({
  first_name: z.string().min(2, { message: "El nombre debe tener al menos 2 caracteres." }).max(100, { message: "El nombre no puede exceder los 100 caracteres."}),
  last_name: z.string().min(2, { message: "El apellido debe tener al menos 2 caracteres." }).max(100, { message: "El apellido no puede exceder los 100 caracteres."}),

  email: z.string().email({ message: "Correo electrónico inválido." }).optional().or(z.literal('')),
  phone_number: z.string().max(30, { message: "Teléfono no puede exceder los 30 caracteres."}).optional().nullable(),

  document_type: z.nativeEnum(DocumentType, { errorMap: () => ({ message: "Seleccione un tipo de documento válido."}) }).optional().nullable(),
  document_number: z.string().max(20, { message: "Número de documento no puede exceder los 20 caracteres."}).optional().nullable(),

  address_street: z.string().max(200, { message: "Dirección no puede exceder los 200 caracteres."}).optional().nullable(),
  address_city: z.string().max(100, { message: "Ciudad no puede exceder los 100 caracteres."}).optional().nullable(),
  address_state_province: z.string().max(100, { message: "Región/Provincia no puede exceder los 100 caracteres."}).optional().nullable(),
  address_postal_code: z.string().max(20, { message: "Código postal no puede exceder los 20 caracteres."}).optional().nullable(),
  address_country: z.string().max(100, { message: "País no puede exceder los 100 caracteres."}).optional().nullable().default("Perú"),

  nationality: z.string().max(100, { message: "Nacionalidad no puede exceder los 100 caracteres."}).optional().nullable().default("Peruana"),
  preferences: z.string().max(500, { message: "Preferencias no pueden exceder los 500 caracteres."}).optional().nullable(), // Assuming Text in DB can be large
  is_blacklisted: z.boolean().default(false),
}).superRefine((data, ctx) => {
     if (data.document_type && !data.document_number) {
         ctx.addIssue({
             code: z.ZodIssueCode.custom,
             path: ['document_number'],
             message: "El número de documento es obligatorio si se selecciona un tipo de documento.",
         });
     }
     if (!data.document_type && data.document_number) {
         ctx.addIssue({
             code: z.ZodIssueCode.custom,
             path: ['document_type'],
             message: "Seleccione un tipo de documento si ingresa un número.",
         });
     }
     if (data.document_type === DocumentType.DNI && data.document_number && data.document_number.length !== 8) {
          ctx.addIssue({ code: z.ZodIssueCode.custom, path: ['document_number'], message: "DNI debe tener 8 dígitos." });
     }
     if (data.document_type === DocumentType.RUC && data.document_number && data.document_number.length !== 11) {
          ctx.addIssue({ code: z.ZodIssueCode.custom, path: ['document_number'], message: "RUC debe tener 11 dígitos." });
     }
     // Add more specific validations for CE, PASSPORT length/format if known
});

export type GuestFormInputs = z.infer<typeof guestFormSchema>;
