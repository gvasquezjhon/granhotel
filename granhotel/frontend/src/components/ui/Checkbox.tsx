// src/components/ui/Checkbox.tsx
import React from 'react';
import { UseFormRegisterReturn } from 'react-hook-form';

interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  id: string;
  error?: string;
  registration: UseFormRegisterReturn;
  labelClassName?: string; // To allow custom styling for label if needed
}

const Checkbox: React.FC<CheckboxProps> = ({ label, id, error, registration, className, labelClassName, ...props }) => (
  <div className={`flex items-center ${className || ''}`}>
    <input
      id={id}
      type="checkbox"
      {...registration}
      {...props}
      className="h-4 w-4 text-brand-primary border-gray-300 rounded focus:ring-brand-primary-light" // Use theme colors
    />
    <label htmlFor={id} className={`ml-2 block text-sm text-brand-text-primary ${labelClassName || ''}`}> {/* Use theme color */}
      {label}
    </label>
    {/* Error display for checkbox might be different, often shown globally for form or below a group */}
    {error && <p className="mt-1 text-xs text-red-600 sm:col-span-3 sm:ml-[calc(25%+0.5rem)]">{error}</p>}
  </div>
);
export default Checkbox;
