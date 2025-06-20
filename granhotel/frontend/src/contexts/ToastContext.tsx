// src/contexts/ToastContext.tsx
import React, { createContext, useContext, useState, ReactNode, useCallback, useEffect } from 'react'; // Added useEffect
import { ToastMessage, ToastContextType, ToastType } from '../types/toast';

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const useToast = (): ToastContextType => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

const Toast: React.FC<ToastMessage & { onDismiss: () => void }> = ({ message, type, onDismiss }) => {
  const baseClasses = "max-w-sm w-full bg-white shadow-lg rounded-lg pointer-events-auto ring-1 ring-black ring-opacity-5 overflow-hidden";
  const typeClasses = {
    success: "bg-green-50 text-green-700 border-green-500", // Ensure border color is also distinct
    error: "bg-red-50 text-red-700 border-red-500",
    info: "bg-blue-50 text-blue-700 border-blue-500",
    warning: "bg-yellow-50 text-yellow-700 border-yellow-500",
  };
  // Simple icons (could be replaced with SVGs)
  const icons = { success: '✓', error: '✕', info: 'ℹ', warning: '⚠' };

  useEffect(() => {
    const timer = setTimeout(onDismiss, 5000); // Auto-dismiss after 5 seconds
    return () => clearTimeout(timer);
  }, [onDismiss]);

  return (
    <div className={`${baseClasses} ${typeClasses[type]} border-l-4 p-4 mb-3 animate-fadeIn`}> {/* Added animate-fadeIn */}
      <div className="flex items-start">
        <div className="flex-shrink-0 text-xl mr-3">{icons[type]}</div> {/* Added margin to icon */}
        <div className="ml-0 w-0 flex-1 pt-0.5"> {/* Removed ml-3 from here */}
          <p className="text-sm font-medium">{message}</p>
        </div>
        <div className="ml-4 flex-shrink-0 flex">
          <button
            onClick={onDismiss}
            className="inline-flex rounded-md text-current opacity-70 hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-current" // Adjusted focus ring
          >
            <span className="sr-only">Cerrar</span>
            &times; {/* Simple 'x' close icon */}
          </button>
        </div>
      </div>
    </div>
  );
};

export const ToastProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const addToast = useCallback((message: string, type: ToastType) => {
    const id = Math.random().toString(36).substring(2, 9); // Corrected unique ID generation
    setToasts((prevToasts) => [...prevToasts, { id, message, type }]);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prevToasts) => prevToasts.filter(toast => toast.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      {/* Toast Container */}
      <div className="fixed bottom-4 right-4 z-50 w-full max-w-xs sm:max-w-sm space-y-3"> {/* Made responsive */}
        {toasts.map((toast) => (
          <Toast key={toast.id} {...toast} onDismiss={() => removeToast(toast.id)} />
        ))}
      </div>
    </ToastContext.Provider>
  );
};
