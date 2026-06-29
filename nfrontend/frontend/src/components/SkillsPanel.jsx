import { useState, useEffect } from "react";
import api from "../api/axios";

export default function SkillsPanel() {
  const [skills, setSkills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    api.get("/api/skills")
      .then(res => {
        if (!cancelled) {
          const data = res.data?.skills;
          setSkills(Array.isArray(data) ? data : []);
        }
      })
      .catch(err => {
        if (!cancelled) {
          console.error("Error cargando skills:", err);
          setError("No se pudieron cargar los skills.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  if (loading) return <div className="p-4 text-gray-400">Cargando skills...</div>;
  if (error) return <div className="p-4 text-red-400">{error}</div>;

  return (
    <div className="p-6 text-white">
      <h2 className="text-xl font-bold mb-4">🧠 Skills Disponibles</h2>
      {skills.length === 0 && <p>No hay skills cargados.</p>}
      {skills.map(skill => (
        <div key={skill.name} className="mb-3 p-3 bg-gray-800 rounded">
          <h3 className="font-semibold">{skill.name}</h3>
          <p className="text-sm text-gray-300">{skill.role}</p>
          <p className="text-xs text-gray-500">{skill.goal}</p>
        </div>
      ))}
    </div>
  );
}