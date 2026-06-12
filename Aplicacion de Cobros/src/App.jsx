import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
const ProtectedRoute = ({ children }) => {
  const isAuthenticated = !!localStorage.getItem('token');
  return isAuthenticated ? children : <Navigate to="/login" />;
};
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
          <Route index element={<Dashboard />} />
          <Route path="payments" element={<div className="text-2xl font-bold">Módulo de Cobros (Próximamente)</div>} />
          <Route path="notifications" element={<div className="text-2xl font-bold">Notificaciones (Próximamente)</div>} />
          <Route path="profile" element={<div className="text-2xl font-bold">Perfil de Usuario</div>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
export default App;