"use client";

import React, { createContext, useContext, useState, useCallback } from "react";
import type { User } from "@/types";

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  updateProfile: (data: Partial<User>) => Promise<void>;
}

interface RegisterData {
  name: string;
  email: string;
  password: string;
  role: "comprador" | "vendedor";
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    try {
      // TODO: Implementar llamada a API real
      // const response = await api.post('/auth/login', { email, password });
      // setUser(response.data.user);
      
      // Mock temporal
      await new Promise((resolve) => setTimeout(resolve, 1000));
      setUser({
        id: "1",
        email,
        name: "María Pérez",
        role: "comprador",
        createdAt: new Date().toISOString(),
      });
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (data: RegisterData) => {
    setIsLoading(true);
    try {
      // TODO: Implementar llamada a API real
      await new Promise((resolve) => setTimeout(resolve, 1000));
      setUser({
        id: "1",
        email: data.email,
        name: data.name,
        role: data.role,
        createdAt: new Date().toISOString(),
      });
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    setUser(null);
  }, []);

  const updateProfile = useCallback(async (data: Partial<User>) => {
    setIsLoading(true);
    try {
      // TODO: Implementar llamada a API real
      await new Promise((resolve) => setTimeout(resolve, 500));
      setUser((prev) => (prev ? { ...prev, ...data } : null));
    } finally {
      setIsLoading(false);
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
        updateProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth debe usarse dentro de un AuthProvider");
  }
  return context;
}
