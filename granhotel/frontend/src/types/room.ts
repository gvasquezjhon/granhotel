// src/types/room.ts

// Matches backend app.models.room.RoomStatus (if it existed as enum)
// For now, based on common string values used in backend schemas/models.
// It's good practice for backend to expose these possible enum values via an options/meta endpoint.
export type RoomStatus = "Available" | "Occupied" | "Maintenance" | "Cleaning";

export interface Room {
  id: number;
  room_number: string;
  name: string;
  description?: string | null;
  price: number; // Axios typically converts JSON numbers to JS numbers. Decimals from backend might become numbers.
  type: string; // e.g., Single, Double, Suite
  status: RoomStatus;
  floor?: number | null;
  building?: string | null;
  created_at: string; // ISO string format from backend (FastAPI encodes datetime to string)
  updated_at: string; // ISO string format from backend
}

// For creating a new room (matches backend schemas.RoomCreate)
export interface RoomCreatePayload {
  room_number: string;
  name: string;
  description?: string | null;
  price: number; // Frontend might send number, backend Pydantic handles Decimal conversion
  type: string;
  status?: RoomStatus; // Optional, backend might have default (e.g., "Available")
  floor?: number | null;
  building?: string |null;
}

// For updating an existing room (matches backend schemas.RoomUpdate)
// All fields are optional.
export interface RoomUpdatePayload {
  room_number?: string;
  name?: string;
  description?: string | null;
  price?: number;
  type?: string;
  status?: RoomStatus;
  floor?: number | null;
  building?: string | null;
}

// For paginated room list responses (if backend provides pagination info in future)
// Not used currently as backend returns List[Room].
export interface PaginatedRoomsResponse {
  items: Room[];
  total: number;
  page: number;
  limit: number;
  // Add other pagination fields if backend sends them (e.g., pages, has_next, has_prev)
}
