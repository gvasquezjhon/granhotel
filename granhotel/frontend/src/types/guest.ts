// src/types/guest.ts
// UserRole might not be directly relevant for Guest type itself, unless guests can also be users.
// For now, it's not imported here.

// Matches backend models.guest.DocumentType enum
export enum DocumentType {
  DNI = "DNI",
  RUC = "RUC",
  PASSPORT = "PASSPORT",
  CE = "CE", // Carné de Extranjería
}

export interface Guest {
  id: string; // UUID from backend, received as string
  first_name: string;
  last_name: string;
  document_type?: DocumentType | null;
  document_number?: string | null;
  email?: string | null;
  phone_number?: string | null;
  address_street?: string | null;
  address_city?: string | null;
  address_state_province?: string | null;
  address_postal_code?: string | null;
  address_country?: string | null;
  nationality?: string | null;
  preferences?: string | null;
  is_blacklisted: boolean;
  created_at: string; // ISO datetime string
  updated_at: string; // ISO datetime string
}

// For creating a new guest (matches backend schemas.GuestCreate)
export interface GuestCreatePayload {
  first_name: string;
  last_name: string;
  document_type?: DocumentType | null;
  document_number?: string | null;
  email?: string | null;
  phone_number?: string | null;
  address_street?: string | null;
  address_city?: string | null;
  address_state_province?: string | null;
  address_postal_code?: string | null;
  address_country?: string | null;
  nationality?: string | null;
  preferences?: string | null;
  is_blacklisted?: boolean; // Default is false in backend model, API might allow setting
}

// For updating an existing guest (matches backend schemas.GuestUpdate)
// All fields are optional.
export interface GuestUpdatePayload {
  first_name?: string;
  last_name?: string;
  document_type?: DocumentType | null;
  document_number?: string | null;
  email?: string | null;
  phone_number?: string | null;
  address_street?: string | null;
  address_city?: string | null;
  address_state_province?: string | null;
  address_postal_code?: string | null;
  address_country?: string | null;
  nationality?: string | null;
  preferences?: string | null;
  is_blacklisted?: boolean;
}

// For updating blacklist status specifically
export interface GuestBlacklistUpdatePayload {
  blacklist_status: boolean;
}
