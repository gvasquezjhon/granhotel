// src/types/user.ts
export enum UserRole { // Using enum for stronger typing on frontend
  ADMIN = "ADMIN",
  MANAGER = "MANAGER",
  RECEPTIONIST = "RECEPTIONIST",
  HOUSEKEEPER = "HOUSEKEEPER",
  // GUEST_USER = "GUEST_USER", // If you add this role
}

export interface User {
  id: string; // UUID as string
  email: string;
  first_name?: string | null;
  last_name?: string | null;
  role: UserRole; // Use the enum. Backend sends string, AuthContext should map to this.
  is_active: boolean;
  // Add other fields that backend /me endpoint might return and are useful client-side
}
