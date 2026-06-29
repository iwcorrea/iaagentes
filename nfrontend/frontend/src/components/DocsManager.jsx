import { useState, useEffect, useCallback } from "react";
import api from "../api/axios";

export default function DocsManager({ projectId }) {
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [content, setContent] = useState("");
  const [newFileName, setNewFileName] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);

  const showMessage = (text, type = "info") => {
    setMessage({ text, type });
    setTimeout(() => setMessage(null), 3000);
  };

  const loadFileList = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      const res = await api.get(`/api/projects/${projectId}/docs`);
      setFiles(res.data.files || []);
    } catch (err) {
      showMessage("No se pudieron cargar los documentos.", "error");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => { loadFileList(); }, [loadFileList]);

  const loadFile = async (filename) => {
    try {
      const res = await api.get(`/api/projects/${projectId}/file`, { params: { path: `docs/${filename}` } });
      setContent(res.data.content);
      setSelectedFile(filename);
    } catch { showMessage("Error al cargar el archivo.", "error"); }
  };

  const saveFile = async () => {
    if (!selectedFile) return;
    setSaving(true);
    try {
      await api.put(`/api/projects/${projectId}/file`, { content }, { params: { path: `docs/${selectedFile}` } });
      showMessage("Guardado.", "success");
    } catch { showMessage("Error al guardar.", "error"); }
    finally { setSaving(false); }
  };

  const createFile = async () => {
    const name = newFileName.trim();
    if (!name) return;
    if (!name.endsWith(".md")) { showMessage("El nombre debe terminar en .md", "error"); return; }
    setSaving(true);
    try {
      await api.put(`/api/projects/${projectId}/file`, { content: "# Nuevo documento\n" }, { params: { path: `docs/${name}` } });
      setFiles(prev => [...prev, name]);
      setNewFileName("");
      showMessage("Archivo creado.", "success");
    } catch { showMessage("Error al crear.", "error"); }
    finally { setSaving(false); }
  };

  const deleteFile = async (filename) => {
    if (!confirm(`¿Eliminar ${filename}?`)) return;
    setSaving(true);
    try {
      await api.put(`/api/projects/${projectId}/file`, { content: "" }, { params: { path: `docs/${filename}` } });
      setFiles(prev => prev.filter(f => f !== filename));
      if (selectedFile === filename) { setSelectedFile(null); setContent(""); }
      showMessage("Eliminado.", "success");
    } catch { showMessage("Error al eliminar.", "error"); }
    finally { setSaving(false); }
  };

  if (!projectId) return <p className="p-4 text-gray-500">Seleccioná un proyecto.</p>;

  return (
    <div className="p-4 bg-gray-900 text-white rounded-lg h-full flex flex-col">
      <h2 className="text-xl font-bold mb-4">📚 Documentos del Proyecto</h2>
      {message && <div className={`mb-3 px-3 py-2 rounded text-sm ${message.type === "error" ? "bg-red-900/50 text-red-300" : "bg-green-900/50 text-green-300"}`}>{message.text}</div>}
      <div className="flex gap-4 flex-1 overflow-hidden">
        <div className="w-1/3 overflow-y-auto">
          <h3 className="font-semibold mb-2">Archivos</h3>
          {loading && <p className="text-gray-400 text-sm">Cargando...</p>}
          {!loading && files.length === 0 && <p className="text-gray-500 text-sm">No hay documentos aún.</p>}
          {files.map(f => (
            <div key={f} className={`flex justify-between items-center p-2 rounded cursor-pointer hover:bg-gray-800 ${selectedFile === f ? "bg-gray-700" : ""}`} onClick={() => loadFile(f)}>
              <span className="text-sm truncate">{f}</span>
              <button onClick={(e) => { e.stopPropagation(); deleteFile(f); }} className="text-red-400 hover:text-red-300 ml-2">🗑️</button>
            </div>
          ))}
          <div className="mt-3 flex gap-2">
            <input type="text" placeholder="nuevo.md" value={newFileName} onChange={e => setNewFileName(e.target.value)} className="flex-1 bg-gray-800 text-white p-1 rounded text-sm" />
            <button onClick={createFile} disabled={saving} className="bg-blue-600 px-3 py-1 rounded text-sm">+</button>
          </div>
        </div>
        <div className="w-2/3 flex flex-col">
          {selectedFile ? (
            <>
              <div className="flex justify-between items-center mb-2">
                <h3 className="font-semibold text-sm">Editando: {selectedFile}</h3>
                <button onClick={saveFile} disabled={saving} className="bg-green-600 px-4 py-1 rounded text-sm">{saving ? "Guardando..." : "💾 Guardar"}</button>
              </div>
              <textarea value={content} onChange={e => setContent(e.target.value)} className="flex-1 bg-gray-800 text-white p-3 rounded font-mono text-sm resize-none" />
            </>
          ) : <p className="text-gray-500">Seleccioná un archivo para editar.</p>}
        </div>
      </div>
    </div>
  );
}