CODIGO_COMPLETO
import React from 'react';

const App = () => {
  return (
    <div className="min-h-screen bg-gray-100">
      {/* Navbar */}
      <nav className="bg-white shadow-lg">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex justify-between">
            <div className="flex space-x-7">
              <div>
                <a href="#" className="flex items-center py-4 px-2">
                  <span className="font-semibold text-gray-500 text-lg">MiApp</span>
                </a>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="bg-blue-600 text-white py-20">
        <div className="container mx-auto px-6 text-center">
          <h1 className="text-4xl font-bold mb-6">Bienvenido a MiApp</h1>
          <p className="text-lg mb-8">Una aplicación moderna con React y TailwindCSS</p>
          <button className="bg-white text-blue-600 font-semibold py-2 px-4 rounded-lg shadow-lg hover:bg-blue-100 transition duration-300">Comienza ahora</button>
        </div>
      </section>

      {/* Contenido adicional */}
      <div className="container mx-auto px-6 py-10">
        <h2 className="text-2xl font-bold text-gray-800 mb-6">Características</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-lg shadow-lg">
            <h3 className="text-xl font-bold mb-2">Seguridad</h3>
            <p className="text-gray-600">Autenticación JWT para máxima seguridad.</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-lg">
            <h3 className="text-xl font-bold mb-2">Rendimiento</h3>
            <p className="text-gray-600">Diseño optimizado para máxima velocidad.</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-lg">
            <h3 className="text-xl font-bold mb-2">Responsive</h3>
            <p className="text-gray-600">Diseño adaptable a cualquier dispositivo.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;