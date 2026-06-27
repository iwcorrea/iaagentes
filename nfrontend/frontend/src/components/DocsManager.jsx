import { useState, useEffect } from "react";
import axios from "axios";

export default function DocsManager({ projectId }) {
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [content, setContent] = useState("");
  const [newFileName, setNewFileName] = useState("");

  useEffect(() => {
    if (projectId) {
      axios.get(`/api/projects/${projectId}/docs`).then(res => setFiles(res.data.files)).catch(() => {});
    }
  }, [projectId]);

  const loadFile = async (filename) => {
    const res = await axios.get(`/api/projects/${projectId}/file?path=docs/${filename}`);
    setContent(res.data.content);
    setSelectedFile(filename);
  };

  const saveFile = async () => {
    if (!selectedFile) return;
    await axios.put(`/api/projects/${projectId}/file?path=docs/${selectedFile}`, { content });
    alert("Guardado");
  };

  const createFile = async () => {
    if (!newFileName.endsWith(".md")) {
      alert("El nombre debe terminar en .md");
      return;
    }
    await axios.put(`/api/projects/${projectId}/file?path=docs/${newFileName}`, { content: "# Instrucciones\n" });
    setFiles(prev => [...prev, newFileName]);
    setNewFileName("");
  };

  const deleteFile = async (filename) => {
    if (!confirm(`¿Eliminar ${filename}?`)) return;
    await axios.put(`/api/projects/${projectId}/file?path=docs/${filename}`, { content: "" });
    setFiles(prev => prev.filter(f => f !== filename));
    if (selectedFile === filename) {
      setSelectedFile(null);
      setContent("");
    }
  };

  return (
    <div className="p-4 bg-gray-900 text-white rounded-lg">
      <h2 className="text-xl font-bold mb-4">📚 Documentos del Proyecto</h2>
      <div className="flex gap-4">
        <div className="w-1/3">
          <h3 className="font-semibold mb-2">Archivos</h3>
          {files.map(f => (
            <div key={f} className="flex justify-between p-1 hover:bg-gray-800 cursor-pointer" onClick={() => loadFile(f)}>
              <span>{f}</span>
              <button onClick={(e) => { e.stopPropagation(); deleteFile(f); }} className="text-red-400">🗑️</button>
            </div>
          ))}
          <div className="mt-2 flex gap-2">
            <input
              type="text"
              placeholder="nuevo.md"
              value={newFileName}
              onChange={e => setNewFileName(e.target.value)}
              className="bg-gray-800 text-white p-1 rounded w-2/3"
            />
            <button onClick={createFile} className="bg-blue-600 px-2 rounded">+</button>
          </div>
        </div>
        <div className="w-2/3">
          {selectedFile ? (
            <>
              <h3 className="font-semibold mb-2">Editando: {selectedFile}</h3>
              <textarea
                value={content}
                onChange={e => setContent(e.target.value)}
                className="w-full h-64 bg-gray-800 text-white p-2 rounded"
              />
              <button onClick={saveFile} className="mt-2 bg-green-600 px-4 py-1 rounded">Guardar</button>
            </>
          ) : (
            <p className="text-gray-400">Selecciona un archivo para editar</p>
          )}
        </div>
      </div>
    </div>
  );
}