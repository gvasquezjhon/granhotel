// src/components/ui/Input.tsx
import React from 'react';
import { UseFormRegisterReturn } from 'react-hook-form';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  id: string;
  error?: string;
  registration: UseFormRegisterReturn;
  helperText?: string;
}

const Input: React.FC<InputProps> = ({ label, id, type = 'text', error, registration, helperText, className, ...props }) => { // Added className
  return (
    <div className="mb-4">
      <label htmlFor={id} className="block text-sm font-medium text-brand-text-secondary mb-1"> {/* Use theme color */}
        {label}
      </label>
      <input
        id={id}
        type={type}
        className={`w-full px-3 py-2 border ${error ? 'border-red-500' : 'border-gray-300'} rounded-md shadow-sm focus:outline-none focus:ring-2 ${error ? 'focus:ring-red-500' : 'focus:ring-brand-primary'} focus:border-transparent transition-colors bg-brand-surface ${className || ''}`} // Use theme color
        {...registration}
        {...props}
      />
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
      {helperText && !error && <p className="mt-1 text-xs text-gray-500">{helperText}</p>}
    </div>
  );
};
export default Input;
