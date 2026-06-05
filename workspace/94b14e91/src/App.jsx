import React, { useEffect, useState } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import AuthForm from './components/AuthForm';
import DashboardMaestro from './components/DashboardMaestro';
import DashboardCliente from './components/DashboardCliente';
function ProtectedRoute({ children, role }) {
  const location = useLocation();
  const user = JSON.parse(localStorage.getItem('user'));
  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  if (role && user.role !== role) {
    // Redirect to appropriate dashboard based on role
    const redirectTo = user.role === 'maestro' ? '/maestro/dashboard' : '/cliente/dashboard';
    return <Navigate to={redirectTo} replace />;
  }
  return children;
}
function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Routes>
        <Route path="/login" element={<AuthForm />} />
        <Route path="/register" element={<AuthForm />} />
        <Route
          path="/maestro/dashboard"
          element={
            <ProtectedRoute role="maestro">
              <DashboardMaestro />
            </ProtectedRoute>
          }
        >
        </Route>
        <Route
          path="/cliente/dashboard"
          element={
            <ProtectedRoute role="cliente">
              <DashboardCliente />
            </ProtectedRoute>
          }
        >
        </Route>
        <Route
          path="/"
          element={
            <ProtectedRoute>
              {() => {
                const user = JSON.parse(localStorage.getItem('user'));
                return user.role === 'maestro' ? (
                  <Navigate to="/maestro/dashboard" replace />
                ) : (
                  <Navigate to="/cliente/dashboard" replace />
                );
              }}
            </ProtectedRoute>
          }
        >
        </Route>
        <Route path="*" element={<div className="p-6 text-red-500">Page not found</div>} />
      </Routes>
    </div>
  );
}
export default App;