import { useState, useEffect } from "react";
import axios from "axios";

export default function SkillsPanel() {
  const [skills, setSkills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    axios.get("/api/skills")
      .then(res => {
        if (!cancelled) {
          // Aseguramos que skills sea siempre un array
          setSkills(res.data?.skills || []);
        }
      })
      .catch(err => {
        if (!cancelled) {
          console.error("Error cargando skills:", err);
          setError("No se pudieron cargar los skills. Verificá que el servidor esté corriendo.");
          setSkills([]);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, []);

  return (
    <div className="p-6 bg-gray-900 text-white rounded-lg h-full overflow-y-auto">
      <h2 className="text-xl font-bold mb-4">🧠 Skills Disponibles</h2>

      {loading && (
        <div className="flex items-center gap-2 text-gray-400">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-400"></div>
          Cargando skills...
        </div>
      )}

      {error && !loading && (
        <div className="p-3 bg-red-900/30 border border-red-700 rounded text-red-300 text-sm">
          {error}
        </div>
      )}

      {!loading && !error && skills.length === 0 && (
        <p className="text-gray-400">No hay skills cargados.</p>
      )}

      {!loading && !error && skills.map(skill => (
        <div key={skill.name} className="mb-3 p-3 bg-gray-800 rounded">
          <h3 className="font-semibold">{skill.name}</h3>
          <p className="text-sm text-gray-300">{skill.role}</p>
          <p className="text-xs text-gray-500">{skill.goal}</p>
          {skill.tags && skill.tags.length > 0 && (
            <p className="text-xs text-blue-400">{skill.tags.join(", ")}</p>
          )}
        </div>
      ))}
    </div>
  );
}