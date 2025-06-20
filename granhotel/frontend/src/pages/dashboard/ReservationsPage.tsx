// src/pages/dashboard/ReservationsPage.tsx
import React, { useState, useMemo, useEffect, useCallback } from 'react'; // Added useCallback
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import { reservationService, GetReservationsParams } from '../../services/reservationService';
import { Reservation, ReservationStatus } from '../../types/reservation';
import { useAuth } from '../../contexts/AuthContext';
import { UserRole } from '../../types/user';
import Button from '../../components/ui/Button';
import Card from '../../components/ui/Card';
import Input from '../../components/ui/Input';
import Select from '../../components/ui/Select';
import { useToast } from '../../contexts/ToastContext';
import { debounce } from 'lodash';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { es } from 'date-fns/locale'; // Import Spanish locale

const RESERVATIONS_QUERY_KEY = 'reservations';

// Convert enum to array for Select options
const statusOptions = Object.entries(ReservationStatus).map(([key, value]) => ({ value: value, label: key.replace("_", " ") }));
// Example: [{value: "PENDING", label: "PENDING"}, ...]
// For better labels, map them:
const formattedStatusOptions = Object.values(ReservationStatus).map(status => {
    let label = status.toString().replace("_", " ").toLowerCase();
    label = label.charAt(0).toUpperCase() + label.slice(1); // Capitalize first letter
    return { value: status, label: label };
});


const ReservationsPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  const [filters, setFilters] = useState<GetReservationsParams>({
    skip: 0,
    limit: 15,
    date_from: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0], // First day of current month
    date_to: new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).toISOString().split('T')[0],   // Last day of current month
  });

  const debouncedSetFilters = useMemo(
     () => debounce((newFilterValues: Partial<GetReservationsParams>) => {
         setFilters(prev => ({ ...prev, ...newFilterValues, skip: 0 }));
     }, 700),
     [] // No dependencies, so it's created once
  );

  const { data: reservations, isLoading, error, isError, refetch } = useQuery<Reservation[], Error>({
    queryKey: [RESERVATIONS_QUERY_KEY, filters],
    queryFn: () => reservationService.getReservations(filters),
    // keepPreviousData: true, // Good for pagination UX
  });

  const cancelReservationMutation = useMutation({
     mutationFn: reservationService.cancelReservation,
     onSuccess: (cancelledReservation) => {
       queryClient.invalidateQueries({ queryKey: [RESERVATIONS_QUERY_KEY, filters] });
       queryClient.invalidateQueries({ queryKey: ['reservation', cancelledReservation.id]});
       addToast(`Reserva ID ${cancelledReservation.id} cancelada con éxito.`, 'success');
     },
     onError: (err: Error) => {
       addToast(`Error al cancelar reserva: ${err.message}`, 'error');
     }
  });

  const handleFilterInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    debouncedSetFilters({ [name]: value === "" ? undefined : value });
  }, [debouncedSetFilters]);

  const handleFilterSelectChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    const { name, value } = e.target;
    debouncedSetFilters({ [name]: value === "" || value === "ALL" ? undefined : value as ReservationStatus });
  }, [debouncedSetFilters]);

  const handleDateChange = useCallback((field: 'date_from' | 'date_to', dateValue: Date | null) => {
     debouncedSetFilters({ [field]: dateValue ? dateValue.toISOString().split('T')[0] : undefined });
  }, [debouncedSetFilters]);

  const handleCancelReservation = (reservation: Reservation) => {
     if (window.confirm(`¿Está seguro de que desea cancelar la reserva ID ${reservation.id} para ${reservation.guest?.first_name} ${reservation.guest?.last_name}?`)) {
         cancelReservationMutation.mutate(reservation.id);
     }
  };

  const canManageReservations = user?.role === UserRole.ADMIN || user?.role === UserRole.MANAGER;
  const canCreateReservations = canManageReservations || user?.role === UserRole.RECEPTIONIST;

  useEffect(() => {
     // This useEffect for refetch might be redundant if filters in queryKey correctly trigger refetches.
     // However, explicit refetch can be useful if debouncedSetFilters doesn't immediately change 'filters' instance for queryKey.
     // React Query typically shallow compares queryKey. If filter object reference changes, it refetches.
     // debouncedSetFilters creates a new object, so this should work automatically.
     // Keeping refetch() for manual refresh button for now.
     // refetch();
  }, [filters]); // Removed refetch from dependencies as it can cause loop if not careful


  const renderTable = () => (
     <div className="overflow-x-auto bg-brand-surface shadow-md rounded-lg mt-4">
       <table className="min-w-full divide-y divide-gray-200">
         <thead className="bg-gray-50">
           <tr>
             {['ID', 'Huésped', 'Habitación', 'Check-in', 'Check-out', 'Estado', 'Precio Total', 'Acciones'].map(header => (
                 <th key={header} scope="col" className="px-4 py-3 text-left text-xs font-medium text-brand-text-secondary uppercase tracking-wider">{header}</th>
             ))}
           </tr>
         </thead>
         <tbody className="bg-white divide-y divide-gray-200">
           {(reservations || []).map((res) => (
             <tr key={res.id} className="hover:bg-gray-50">
               <td className="px-4 py-3 whitespace-nowrap text-sm text-brand-text-primary">{res.id}</td>
               <td className="px-4 py-3 whitespace-nowrap">
                 <div className="text-sm font-medium text-brand-text-primary">{res.guest ? `${res.guest.first_name} ${res.guest.last_name}` : 'N/A'}</div>
                 {res.guest?.email && <div className="text-xs text-brand-text-secondary">{res.guest.email}</div>}
               </td>
               <td className="px-4 py-3 whitespace-nowrap text-sm text-brand-text-primary">{res.room ? `${res.room.name} (#${res.room.room_number})` : 'N/A'}</td>
               <td className="px-4 py-3 whitespace-nowrap text-sm text-brand-text-primary">{new Date(res.check_in_date + 'T00:00:00').toLocaleDateString('es-PE')}</td>
               <td className="px-4 py-3 whitespace-nowrap text-sm text-brand-text-primary">{new Date(res.check_out_date + 'T00:00:00').toLocaleDateString('es-PE')}</td>
               <td className="px-4 py-3 whitespace-nowrap">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                     res.status === ReservationStatus.CONFIRMED ? 'bg-green-100 text-green-800' :
                     res.status === ReservationStatus.PENDING ? 'bg-yellow-100 text-yellow-800' :
                     res.status === ReservationStatus.CHECKED_IN ? 'bg-blue-100 text-blue-800' :
                     res.status === ReservationStatus.CHECKED_OUT ? 'bg-slate-100 text-slate-600' : // Changed to slate for more neutral final state
                     res.status === ReservationStatus.CANCELLED ? 'bg-red-100 text-red-800' :
                     res.status === ReservationStatus.NO_SHOW ? 'bg-orange-100 text-orange-800' : // Added NO_SHOW color
                     res.status === ReservationStatus.WAITLIST ? 'bg-purple-100 text-purple-800' : // Added WAITLIST color
                     'bg-gray-100 text-gray-600' // Default/fallback
                  }`}>
                    {formattedStatusOptions.find(opt => opt.value === res.status)?.label || res.status}
                  </span>
               </td>
               <td className="px-4 py-3 whitespace-nowrap text-sm text-brand-text-primary">S/ {res.total_price ? Number(res.total_price).toFixed(2) : 'N/A'}</td>
               <td className="px-4 py-3 whitespace-nowrap text-sm font-medium space-x-1">
                 <Button variant="secondary" className="w-auto text-xs px-2 py-1" onClick={() => navigate(`/dashboard/reservations/${res.id}/view`)}>Ver</Button>
                 {canManageReservations && res.status !== ReservationStatus.CANCELLED && res.status !== ReservationStatus.CHECKED_OUT && (
                     <Button variant="primary" className="w-auto text-xs px-2 py-1" onClick={() => navigate(`/dashboard/reservations/${res.id}/edit`)}>Editar</Button>
                 )}
                 {canManageReservations && res.status !== ReservationStatus.CANCELLED && res.status !== ReservationStatus.CHECKED_OUT && res.status !== ReservationStatus.CHECKED_IN && (
                     <Button
                         variant="danger"
                         className="w-auto text-xs px-2 py-1"
                         onClick={() => handleCancelReservation(res)}
                         isLoading={cancelReservationMutation.isPending && cancelReservationMutation.variables === res.id}
                     >
                       Cancelar
                     </Button>
                 )}
               </td>
             </tr>
           ))}
         </tbody>
       </table>
     </div>
  );

  if (isLoading) return <div className="text-center py-10 text-brand-text-secondary">Cargando reservas...</div>;
  if (isError) return <div className="p-4 bg-red-100 text-red-700 rounded-md">Error al cargar reservas: {error?.message}</div>;

  return (
    <div className="animate-fadeIn">
      <div className="flex flex-wrap justify-between items-center mb-6 gap-4">
        <h1 className="text-3xl font-semibold text-brand-text-primary">Gestión de Reservas</h1>
        {canCreateReservations && (
          <Button onClick={() => navigate('/dashboard/reservations/new')} variant="primary" className="w-full sm:w-auto">
            Crear Nueva Reserva
          </Button>
        )}
      </div>

      <Card className="mb-6 p-4">
         <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 items-end">
             <Input label="ID de Huésped (UUID)" id="guest_id_filter" name="guest_id" placeholder="Filtrar por ID de huésped..." onChange={handleFilterInputChange} />
             <Input label="ID de Habitación" id="room_id_filter" name="room_id" type="number" placeholder="Filtrar por ID de habitación..." onChange={handleFilterInputChange} />
             <Select
                 label="Estado de Reserva"
                 id="status_filter"
                 name="status"
                 registration={{} as any}
                 value={filters.status || "ALL"}
                 onChange={handleFilterSelectChange}
                 options={[{value: "ALL", label: "Todos los Estados"}, ...formattedStatusOptions]}
             />
             <div className="flex flex-col">
                 <label htmlFor="date_from_filter" className="block text-sm font-medium text-brand-text-secondary mb-1">Inicio del Periodo (Reserva)</label>
                 <DatePicker
                     selected={filters.date_from ? new Date(filters.date_from + "T00:00:00") : null}
                     onChange={(date) => handleDateChange('date_from', date)}
                     dateFormat="dd/MM/yyyy"
                     locale={es}
                     className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-primary"
                     placeholderText="dd/mm/aaaa"
                     id="date_from_filter"
                 />
             </div>
              <div className="flex flex-col">
                 <label htmlFor="date_to_filter" className="block text-sm font-medium text-brand-text-secondary mb-1">Fin del Periodo (Reserva)</label>
                 <DatePicker
                     selected={filters.date_to ? new Date(filters.date_to + "T00:00:00") : null}
                     onChange={(date) => handleDateChange('date_to', date)}
                     dateFormat="dd/MM/yyyy"
                     locale={es}
                     className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-primary"
                     placeholderText="dd/mm/aaaa"
                     id="date_to_filter"
                 />
             </div>
             <Button onClick={() => refetch()} variant="secondary" className="w-full md:w-auto" isLoading={isLoading}>Aplicar Filtros/Refrescar</Button>
         </div>
      </Card>

      {(reservations || []).length > 0 ? renderTable() : (
        <div className="text-center py-10">
          <p className="text-brand-text-secondary">
            {Object.values(filters).some(val => val !== undefined && (typeof val !== 'object' || Object.keys(val).length > 2))
                ? "No se encontraron reservas con los filtros actuales."
                : "No hay reservas registradas."
            }
          </p>
          {canCreateReservations && (
             <p className="mt-2 text-sm">Puede empezar <Link to="/dashboard/reservations/new" className="text-brand-primary hover:underline">creando una nueva reserva</Link>.</p>
          )}
        </div>
      )}
      {/* TODO: Add Pagination component */}
    </div>
  );
};

export default ReservationsPage;
