// src/components/ui/Textarea.tsx
import React from 'react';
import { UseFormRegisterReturn } from 'react-hook-form';

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
  id: string;
  error?: string;
  registration: UseFormRegisterReturn;
}

const Textarea: React.FC<TextareaProps> = ({ label, id, error, registration, className, ...props }) => (
  <div className="mb-4">
    <label htmlFor={id} className="block text-sm font-medium text-brand-text-secondary mb-1"> {/* Use theme color */}
      {label}
    </label>
    <textarea
      id={id}
      {...registration}
      {...props}
      className={`w-full px-3 py-2 border ${error ? 'border-red-500' : 'border-gray-300'} rounded-md shadow-sm focus:outline-none focus:ring-2 ${error ? 'focus:ring-red-500' : 'focus:ring-brand-primary'} focus:border-transparent transition-colors bg-brand-surface ${className || ''}`} // Use theme color
    />
    {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
  </div>
);
export default Textarea;
