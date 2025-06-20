// src/types/authSchemas.ts
import { z } from 'zod';

export const loginSchema = z.object({
  email: z.string().email({ message: "Correo electrónico inválido" }),
  password: z.string().min(6, { message: "La contraseña debe tener al menos 6 caracteres" }),
});

export type LoginFormInputs = z.infer<typeof loginSchema>;
