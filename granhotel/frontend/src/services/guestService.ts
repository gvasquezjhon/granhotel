// src/services/guestService.ts
import apiClient from './apiClient';
import {
  Guest,
  GuestCreatePayload,
  GuestUpdatePayload,
  GuestBlacklistUpdatePayload,
  DocumentType // Import DocumentType if needed for params, though not directly here
} from '../types/guest';

const API_GUESTS_URL = '/guests'; // Relative to apiClient's baseURL

export interface GetGuestsParams {
  skip?: number;
  limit?: number;
  first_name?: string;
  last_name?: string;
  document_number?: string;
  email?: string;
  is_blacklisted?: boolean;
}

// Fetches a list of guests
const getGuests = async (params?: GetGuestsParams): Promise<Guest[]> => {
  const response = await apiClient.get<Guest[]>(API_GUESTS_URL, { params });
  return response.data;
};

// Fetches a single guest by their ID (UUID string)
const getGuestById = async (guestId: string): Promise<Guest> => {
  const response = await apiClient.get<Guest>(`${API_GUESTS_URL}/${guestId}`);
  return response.data;
};

// Creates a new guest
const createGuest = async (guestData: GuestCreatePayload): Promise<Guest> => {
  const response = await apiClient.post<Guest>(API_GUESTS_URL, guestData);
  return response.data;
};

// Updates an existing guest
const updateGuest = async (guestId: string, guestData: GuestUpdatePayload): Promise<Guest> => {
  const response = await apiClient.put<Guest>(`${API_GUESTS_URL}/${guestId}`, guestData);
  return response.data;
};

// Updates a guest's blacklist status
const updateGuestBlacklistStatus = async (guestId: string, payload: GuestBlacklistUpdatePayload): Promise<Guest> => {
  // Backend endpoint: PATCH /guests/{guest_id}/blacklist?blacklist_status=true/false
  // Axios' PATCH method sends data in the body by default.
  // To send as query params for a PATCH request:
  const response = await apiClient.patch<Guest>(
    `${API_GUESTS_URL}/${guestId}/blacklist`,
    null, // No request body for this specific PATCH if using query params
    { params: { blacklist_status: payload.blacklist_status } }
  );
  return response.data;
};

// Delete guest - backend has this, but not explicitly requested for frontend service yet.
// If needed, it would look like:
// const deleteGuest = async (guestId: string): Promise<Guest> => { // Assuming backend returns deleted guest
//   const response = await apiClient.delete<Guest>(`${API_GUESTS_URL}/${guestId}`);
//   return response.data;
// };


export const guestService = {
  getGuests,
  getGuestById,
  createGuest,
  updateGuest,
  updateGuestBlacklistStatus,
  // deleteGuest, // Uncomment if/when implemented
};
