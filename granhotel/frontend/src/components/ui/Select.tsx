// src/components/ui/Select.tsx
import React from 'react';
import { UseFormRegisterReturn } from 'react-hook-form';

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  id: string;
  error?: string;
  registration: UseFormRegisterReturn;
  options: Array<{ value: string | number; label: string }>;
  placeholder?: string;
}

const Select: React.FC<SelectProps> = ({ label, id, error, registration, options, placeholder, className, ...props }) => {
  return (
    <div className="mb-4">
      <label htmlFor={id} className="block text-sm font-medium text-brand-text-secondary mb-1"> {/* Use theme color */}
        {label}
      </label>
      <select
        id={id}
        className={`w-full px-3 py-2 border ${error ? 'border-red-500' : 'border-gray-300'} rounded-md shadow-sm focus:outline-none focus:ring-2 ${error ? 'focus:ring-red-500' : 'focus:ring-brand-primary'} focus:border-transparent transition-colors bg-brand-surface ${className || ''}`} // Use theme color
        {...registration}
        {...props}
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options.map(option => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  );
};
export default Select;
