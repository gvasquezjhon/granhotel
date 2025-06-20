// src/pages/LoginPage.tsx
import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate } from 'react-router-dom';
import { loginSchema, LoginFormInputs } from '../types/authSchemas';
import { useAuth } from '../contexts/AuthContext';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import { authService } from '../services/authService';
import Card from '../components/ui/Card'; // Import Card
import { User } from '../types/user'; // Ensure User is imported if used for mockUser

const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [localIsLoading, setLocalIsLoading] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormInputs>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormInputs) => {
    setLocalIsLoading(true);
    setLocalError(null);
    try {
      // This section will be replaced by actual API call to authService.login
      // For now, using the placeholder logic.
      if (data.email === "test@example.com" && data.password === "password") {
        console.log("Simulating successful login with:", data);
        await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate delay
        const mockToken = "fake-jwt-token-simulated";
        const mockUser: User = {
          id: "mock-user-id-simulated",
          email: data.email,
          first_name: "Test",
          last_name: "UserSim",
          role: "RECEPTIONIST",
          is_active: true
        };
        login(mockToken, mockUser, "fake-refresh-token-simulated");
        navigate('/dashboard', { replace: true });
      } else {
        // Simulate backend error for incorrect credentials
        console.log("Simulating failed login with:", data);
        await new Promise(resolve => setTimeout(resolve, 500)); // Simulate delay
        setLocalError("Credenciales incorrectas. (Pruebe test@example.com / password)");
      }
    } catch (err: any) {
      // This catch block would be for actual authService errors in future
      localStorage.removeItem('authToken');
      localStorage.removeItem('refreshToken');
      const errorMessage = err.response?.data?.detail || err.message || "Error al iniciar sesión.";
      setLocalError(errorMessage);
    } finally {
      setLocalIsLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-sm">
      <div className="text-center mb-6">
        <h2 className="text-3xl font-bold text-brand-text-primary">
          Bienvenido de Nuevo
        </h2>
        <p className="mt-2 text-sm text-brand-text-secondary">
          Ingrese sus credenciales para acceder al sistema.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <Input
          label="Correo Electrónico"
          id="email"
          type="email"
          registration={register('email')}
          error={errors.email?.message}
          placeholder="usuario@example.com"
        />
        <Input
          label="Contraseña"
          id="password"
          type="password"
          registration={register('password')}
          error={errors.password?.message}
          placeholder="••••••••"
        />

        {localError && (
          <p className="text-sm text-red-600 text-center">{localError}</p>
        )}

        <Button type="submit" isLoading={localIsLoading} className="w-full" variant="primary">
          {localIsLoading ? 'Ingresando...' : 'Ingresar'}
        </Button>
      </form>
    </Card>
  );
};
export default LoginPage;
