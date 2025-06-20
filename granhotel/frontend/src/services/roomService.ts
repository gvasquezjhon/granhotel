// src/services/roomService.ts
import apiClient from './apiClient';
import { Room, RoomCreatePayload, RoomUpdatePayload } from '../types/room';
// PaginatedRoomsResponse is not used for now as backend returns List[Room]

const API_ROOMS_URL = '/rooms'; // Relative to apiClient's baseURL

interface GetRoomsParams {
  skip?: number;
  limit?: number;
  // Future filter params for backend:
  // type?: string;
  // status?: RoomStatus;
  // min_price?: number;
  // max_price?: number;
}

// Fetches a list of rooms
const getRooms = async (params?: GetRoomsParams): Promise<Room[]> => {
  const response = await apiClient.get<Room[]>(API_ROOMS_URL, { params });
  return response.data;
};

// Fetches a single room by its ID
const getRoomById = async (roomId: number): Promise<Room> => {
  const response = await apiClient.get<Room>(`${API_ROOMS_URL}/${roomId}`);
  return response.data;
};

// Creates a new room (Admin/Manager role typically)
const createRoom = async (roomData: RoomCreatePayload): Promise<Room> => {
  const response = await apiClient.post<Room>(API_ROOMS_URL, roomData);
  return response.data;
};

// Updates an existing room (Admin/Manager role typically)
const updateRoom = async (roomId: number, roomData: RoomUpdatePayload): Promise<Room> => {
  const response = await apiClient.put<Room>(`${API_ROOMS_URL}/${roomId}`, roomData);
  return response.data;
};

// Deletes a room (Admin/Manager role typically)
const deleteRoom = async (roomId: number): Promise<Room> => { // Backend returns deleted room object
  const response = await apiClient.delete<Room>(`${API_ROOMS_URL}/${roomId}`);
  return response.data;
};

export const roomService = {
  getRooms,
  getRoomById,
  createRoom,
  updateRoom,
  deleteRoom,
};
