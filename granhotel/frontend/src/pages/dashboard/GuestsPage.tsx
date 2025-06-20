// src/pages/dashboard/GuestsPage.tsx
import React, { useState, useMemo, useCallback } from 'react'; // Added useCallback
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import { guestService, GetGuestsParams } from '../../services/guestService';
import { Guest, DocumentType } from '../../types/guest';
import { useAuth } from '../../contexts/AuthContext';
import { UserRole } from '../../types/user';
import Button from '../../components/ui/Button';
import Card from '../../components/ui/Card';
import Input from '../../components/ui/Input';
import Select from '../../components/ui/Select';
import { useToast } from '../../contexts/ToastContext';
import { debounce } from 'lodash';

const GUESTS_QUERY_KEY = 'guests';

const GuestsPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  const [filters, setFilters] = useState<GetGuestsParams>({ skip: 0, limit: 25 });

  const debouncedSetFilters = useMemo(
     () => debounce((newFilterPart: Partial<GetGuestsParams>) => { // Accept partial updates
        setFilters(prev => ({ ...prev, ...newFilterPart, skip: 0 }));
     }, 500),
     []
  );

  const { data: guests, isLoading, error, isError } = useQuery<Guest[], Error>({
    queryKey: [GUESTS_QUERY_KEY, filters],
    queryFn: () => guestService.getGuests(filters),
    // keepPreviousData: true, // Consider for better UX on pagination/filtering
  });

  const blacklistMutation = useMutation({
     mutationFn: (data: { guestId: string; blacklistStatus: boolean }) =>
         guestService.updateGuestBlacklistStatus(data.guestId, { blacklist_status: data.blacklistStatus }),
     onSuccess: (updatedGuest) => {
       queryClient.invalidateQueries({ queryKey: [GUESTS_QUERY_KEY, filters] });
       queryClient.invalidateQueries({ queryKey: ['guest', updatedGuest.id]});
       addToast(`Estado de lista negra para ${updatedGuest.first_name} ${updatedGuest.last_name} actualizado.`, 'success');
     },
     onError: (err: Error) => {
       addToast(`Error al actualizar lista negra: ${err.message}`, 'error');
     }
  });

  const handleFilterInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    debouncedSetFilters({ [name]: value || undefined }); // Send undefined if empty for clearing filter
  }, [debouncedSetFilters]);

  const handleFilterSelectChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    const { name, value } = e.target;
    let processedValue: boolean | undefined = undefined;
    if (value === "true") processedValue = true;
    else if (value === "false") processedValue = false;
    // For "any" or empty string, it becomes undefined, effectively clearing the filter
    debouncedSetFilters({ [name]: processedValue });
  }, [debouncedSetFilters]);

  const handleBlacklistToggle = (guest: Guest) => {
     const newStatus = !guest.is_blacklisted;
     const action = newStatus ? "agregar a" : "quitar de";
     if (window.confirm(`¿Está seguro de que desea ${action} la lista negra a ${guest.first_name} ${guest.last_name}?`)) {
         blacklistMutation.mutate({ guestId: guest.id, blacklistStatus: newStatus });
     }
  };

  const canManageGuests = user?.role === UserRole.ADMIN || user?.role === UserRole.MANAGER;
  const canRegisterGuests = canManageGuests || user?.role === UserRole.RECEPTIONIST;

  const renderTable = () => (
     <div className="overflow-x-auto bg-brand-surface shadow-md rounded-lg">
       <table className="min-w-full divide-y divide-gray-200">
         <thead className="bg-gray-50">
           <tr>
             <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-brand-text-secondary uppercase tracking-wider">Nombre</th>
             <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-brand-text-secondary uppercase tracking-wider">Documento</th>
             <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-brand-text-secondary uppercase tracking-wider">Email / Teléfono</th>
             <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-brand-text-secondary uppercase tracking-wider">Lista Negra</th>
             <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-brand-text-secondary uppercase tracking-wider">Acciones</th>
           </tr>
         </thead>
         <tbody className="bg-white divide-y divide-gray-200">
           {(guests || []).map((guest) => (
             <tr key={guest.id} className="hover:bg-gray-50">
               <td className="px-6 py-4 whitespace-nowrap">
                 <div className="text-sm font-medium text-brand-text-primary">{guest.first_name} {guest.last_name}</div>
                 <div className="text-xs text-brand-text-secondary">{guest.nationality || ''}</div>
               </td>
               <td className="px-6 py-4 whitespace-nowrap">
                 <div className="text-sm text-brand-text-primary">{guest.document_type ? `${guest.document_type}: ${guest.document_number || ''}` : (guest.document_number || 'N/A')}</div>
               </td>
               <td className="px-6 py-4 whitespace-nowrap">
                 <div className="text-sm text-brand-text-primary">{guest.email || ''}</div>
                 <div className="text-xs text-brand-text-secondary">{guest.phone_number || ''}</div>
               </td>
               <td className="px-6 py-4 whitespace-nowrap">
                 <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                     guest.is_blacklisted ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                 }`}>
                   {guest.is_blacklisted ? 'Sí' : 'No'}
                 </span>
               </td>
               <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                 <Button variant="secondary" className="w-auto text-xs px-2 py-1" onClick={() => navigate(`/dashboard/guests/${guest.id}/view`)}>Ver</Button>
                 {canManageGuests && (
                   <>
                     <Button variant="primary" className="w-auto text-xs px-2 py-1" onClick={() => navigate(`/dashboard/guests/${guest.id}/edit`)}>Editar</Button>
                     <Button
                         variant={guest.is_blacklisted ? "secondary" : "danger"}
                         className="w-auto text-xs px-2 py-1"
                         onClick={() => handleBlacklistToggle(guest)}
                         isLoading={blacklistMutation.isPending && blacklistMutation.variables?.guestId === guest.id}
                     >
                       {guest.is_blacklisted ? 'Quitar de L.N.' : 'Añadir a L.N.'}
                     </Button>
                   </>
                 )}
               </td>
             </tr>
           ))}
         </tbody>
       </table>
     </div>
  );

  if (isLoading) return <div className="text-center py-10 text-brand-text-secondary">Cargando huéspedes...</div>;
  if (isError) return <div className="p-4 bg-red-100 text-red-700 rounded-md">Error al cargar huéspedes: {error?.message}</div>;

  return (
    <div className="animate-fadeIn">
      <div className="flex flex-wrap justify-between items-center mb-6 gap-4">
        <h1 className="text-3xl font-semibold text-brand-text-primary">Gestión de Huéspedes</h1>
        {canRegisterGuests && (
          <Button onClick={() => navigate('/dashboard/guests/new')} variant="primary" className="w-full sm:w-auto">
            Registrar Nuevo Huésped
          </Button>
        )}
      </div>

      <Card className="mb-6">
         <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 items-end">
             <Input label="Nombre" id="first_name_filter" name="first_name" placeholder="Filtrar por nombre..." onChange={handleFilterInputChange} />
             <Input label="Apellido" id="last_name_filter" name="last_name" placeholder="Filtrar por apellido..." onChange={handleFilterInputChange} />
             <Input label="Nº Documento" id="document_number_filter" name="document_number" placeholder="Filtrar por documento..." onChange={handleFilterInputChange} />
             <Input label="Email" id="email_filter" name="email" type="email" placeholder="Filtrar por email..." onChange={handleFilterInputChange} />
             <Select
                 label="Estado Lista Negra"
                 id="is_blacklisted_filter"
                 name="is_blacklisted"
                 registration={{} as any} // Not using react-hook-form register here
                 value={filters.is_blacklisted === undefined ? "any" : String(filters.is_blacklisted)}
                 onChange={handleFilterSelectChange}
                 options={[
                     {value: "any", label: "Todos"},
                     {value: "true", label: "Sí (En Lista Negra)"},
                     {value: "false", label: "No (No en Lista Negra)"}
                 ]}
             />
         </div>
      </Card>

      {(guests || []).length > 0 ? renderTable() : (
        <div className="text-center py-10">
          <p className="text-brand-text-secondary">
            {Object.values(filters).some(val => val !== undefined && (typeof val !== 'object' || Object.keys(val).length > 2)) // Check if any filter is active besides skip/limit
                ? "No se encontraron huéspedes con los filtros actuales."
                : "No hay huéspedes registrados."
            }
          </p>
          {canRegisterGuests && (
             <p className="mt-2 text-sm">Puede empezar <Link to="/dashboard/guests/new" className="text-brand-primary hover:underline">registrando un nuevo huésped</Link>.</p>
          )}
        </div>
      )}
      {/* TODO: Add Pagination controls if backend supports total count and pages */}
    </div>
  );
};

export default GuestsPage;
