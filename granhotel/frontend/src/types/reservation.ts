// src/types/reservation.ts
import { Guest } from './guest';
import { Room } from './room';

// Matches backend models.reservation.ReservationStatus enum
export enum ReservationStatus {
  PENDING = "PENDING",
  CONFIRMED = "CONFIRMED",
  CHECKED_IN = "CHECKED_IN",
  CHECKED_OUT = "CHECKED_OUT",
  CANCELLED = "CANCELLED",
  NO_SHOW = "NO_SHOW",
  WAITLIST = "WAITLIST",
}

export interface Reservation {
  id: number;
  guest_id: string; // UUID string from backend Guest model
  room_id: number;
  check_in_date: string; // ISO date string (e.g., "YYYY-MM-DD")
  check_out_date: string; // ISO date string
  reservation_date: string; // ISO datetime string
  status: ReservationStatus;
  total_price?: number | null; // Backend sends Decimal, frontend might receive as number.
  notes?: string | null;
  created_at: string; // ISO datetime string
  updated_at: string; // ISO datetime string

  guest?: Guest | null;
  room?: Room | null;
}

export interface ReservationCreatePayload {
  guest_id: string; // UUID string
  room_id: number;
  check_in_date: string; // "YYYY-MM-DD"
  check_out_date: string; // "YYYY-MM-DD"
  status?: ReservationStatus;
  notes?: string | null;
}

export interface ReservationUpdatePayload {
  guest_id?: string;
  room_id?: number;
  check_in_date?: string; // "YYYY-MM-DD"
  check_out_date?: string; // "YYYY-MM-DD"
  status?: ReservationStatus;
  total_price?: number | null;
  notes?: string | null;
}

// For updating status specifically using the PATCH endpoint
// The actual payload for the PATCH request might be query parameters, not a body.
// This schema is for type safety of the status value itself.
export interface ReservationStatusUpdatePayload {
    new_status: ReservationStatus;
}
