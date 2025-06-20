// src/types/user.ts
export interface User {
  id: string; // UUID as string
  email: string;
  first_name?: string | null;
  last_name?: string | null;
  role: string; // e.g., "ADMIN", "RECEPTIONIST" (UserRole enum from backend)
  is_active: boolean;
  // Add other fields that backend /me endpoint might return and are useful client-side
}
