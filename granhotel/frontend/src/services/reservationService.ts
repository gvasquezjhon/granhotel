// src/services/reservationService.ts
import apiClient from './apiClient';
import {
  Reservation,
  ReservationCreatePayload,
  ReservationUpdatePayload,
  ReservationStatus // Import enum for parameter typing
} from '../types/reservation';
// Guest and Room types are not directly used as parameters here, but their IDs are.

const API_RESERVATIONS_URL = '/reservations'; // Relative to apiClient's baseURL

export interface GetReservationsParams {
  skip?: number;
  limit?: number;
  guest_id?: string; // UUID string
  room_id?: number;
  status?: ReservationStatus;
  date_from?: string; // "YYYY-MM-DD"
  date_to?: string;   // "YYYY-MM-DD"
}

// Fetches a list of reservations
const getReservations = async (params?: GetReservationsParams): Promise<Reservation[]> => {
  const response = await apiClient.get<Reservation[]>(API_RESERVATIONS_URL, { params });
  return response.data;
};

// Fetches a single reservation by its ID
const getReservationById = async (reservationId: number): Promise<Reservation> => {
  const response = await apiClient.get<Reservation>(`${API_RESERVATIONS_URL}/${reservationId}`);
  return response.data;
};

// Creates a new reservation
const createReservation = async (reservationData: ReservationCreatePayload): Promise<Reservation> => {
  const response = await apiClient.post<Reservation>(API_RESERVATIONS_URL, reservationData);
  return response.data;
};

// Updates an existing reservation's details (e.g., dates, notes)
const updateReservationDetails = async (reservationId: number, reservationData: ReservationUpdatePayload): Promise<Reservation> => {
  const response = await apiClient.put<Reservation>(`${API_RESERVATIONS_URL}/${reservationId}`, reservationData);
  return response.data;
};

// Updates the status of a reservation
const updateReservationStatus = async (reservationId: number, newStatus: ReservationStatus): Promise<Reservation> => {
  // Backend endpoint: PATCH /reservations/{reservation_id}/status?new_status=VALUE
  const response = await apiClient.patch<Reservation>(
    `${API_RESERVATIONS_URL}/${reservationId}/status`,
    null, // No request body for this specific PATCH if using query params
    { params: { new_status: newStatus } } // Send new_status as a query parameter
  );
  return response.data;
};

// Cancels a reservation (sets status to CANCELLED)
// Backend endpoint: POST /reservations/{reservation_id}/cancel
const cancelReservation = async (reservationId: number): Promise<Reservation> => {
  const response = await apiClient.post<Reservation>(`${API_RESERVATIONS_URL}/${reservationId}/cancel`);
  return response.data;
};


export const reservationService = {
  getReservations,
  getReservationById,
  createReservation,
  updateReservationDetails,
  updateReservationStatus,
  cancelReservation,
};
