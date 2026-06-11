const API = 'http://localhost:8000';
let activeProjectId = null;
let chatHistory = [];
let currentFileContent = '';
let currentFilePath = '';

// Tema
function toggleTheme() {
    document.documentElement.classList.toggle('dark');
    const themeBtn = document.getElementById('theme-toggle').querySelector('i');
    if (document.documentElement.classList.contains('dark')) {
        themeBtn.className = 'fas fa-sun';
    } else {
        themeBtn.className = 'fas fa-moon';
    }
}

// Navegación
function switchTab(tab) {
    document.querySelectorAll('main section').forEach(s => s.classList.add('hidden'));
    const target = document.getElementById('tab-' + tab);
    if (target) target.classList.remove('hidden');
    document.querySelectorAll('nav button').forEach(b => b.classList.remove('tab-active'));
    event.target.classList.add('tab-active');
    if (tab === 'projects') loadProjects();
    if (tab === 'improvements') loadImprovements();
    if (tab === 'preview' && activeProjectId) refreshPreview();
}

function showSidebar(projectId) {
    activeProjectId = projectId;
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.remove('hidden');
    if (window.innerWidth < 768) sidebar.classList.add('open');
    document.getElementById('current-project-badge').classList.remove('hidden');
    document.getElementById('current-project-id').textContent = projectId;
    loadFiles();
    loadChatHistory();
    document.getElementById('btn-live').classList.remove('hidden');
}

function hideSidebar() {
    activeProjectId = null;
    document.getElementById('sidebar').classList.add('hidden');
    document.getElementById('current-project-badge').classList.add('hidden');
    document.getElementById('btn-live').classList.add('hidden');
    document.getElementById('chat-messages').innerHTML = '';
    document.getElementById('chat-placeholder').classList.remove('hidden');
    chatHistory = [];
}

// Toast
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

// Modal
function viewFile(filename) {
    if (!activeProjectId) return;
    fetch(`${API}/projects/${activeProjectId}/file?path=${encodeURIComponent(filename)}`)
        .then(r => r.json())
        .then(data => {
            currentFilePath = filename;
            currentFileContent = data.content;
            document.getElementById('code-modal').classList.remove('hidden');
            document.getElementById('modal-file-name').textContent = '📄 ' + filename;
            document.getElementById('modal-code').textContent = data.content;
            document.getElementById('modal-code').classList.remove('hidden');
            document.getElementById('modal-editor').classList.add('hidden');
            document.getElementById('edit-toggle-btn').classList.remove('hidden');
            document.getElementById('save-file-btn').classList.add('hidden');
            hljs.highlightElement(document.getElementById('modal-code'));
        });
}

function closeModal() { document.getElementById('code-modal').classList.add('hidden'); }

function toggleEditMode() {
    const codeEl = document.getElementById('modal-code');
    const editorEl = document.getElementById('modal-editor');
    if (editorEl.classList.contains('hidden')) {
        editorEl.value = currentFileContent;
        codeEl.classList.add('hidden');
        editorEl.classList.remove('hidden');
        document.getElementById('edit-toggle-btn').classList.add('hidden');
        document.getElementById('save-file-btn').classList.remove('hidden');
    }
}

async function saveFile() {
    const newContent = document.getElementById('modal-editor').value;
    try {
        const res = await fetch(`${API}/projects/${activeProjectId}/file?path=${encodeURIComponent(currentFilePath)}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: newContent })
        });
        if (res.ok) {
            currentFileContent = newContent;
            document.getElementById('modal-code').textContent = newContent;
            document.getElementById('modal-code').classList.remove('hidden');
            document.getElementById('modal-editor').classList.add('hidden');
            document.getElementById('edit-toggle-btn').classList.remove('hidden');
            document.getElementById('save-file-btn').classList.add('hidden');
            hljs.highlightElement(document.getElementById('modal-code'));
            showToast('Archivo guardado con éxito', 'success');
        }
    } catch { showToast('Error al guardar el archivo', 'error'); }
}

// Chat
async function sendPrompt() {
    const input = document.getElementById('chat-input');
    const prompt = input.value.trim();
    if (!prompt) return;
    input.value = '';
    
    document.getElementById('agent-progress').classList.remove('hidden');
    document.getElementById('progress-text').textContent = 'Planificando arquitectura...';
    document.getElementById('send-btn').disabled = true;
    
    addMessage('user', prompt);

    const body = { messages: [{ role: 'user', content: prompt }] };
    let url = `${API}/v1/chat/completions`;
    if (activeProjectId) url += `?project_id=${activeProjectId}`;

    try {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const data = await res.json();
        const content = data.choices?.[0]?.message?.content || 'Sin respuesta';
        addMessage('assistant', content);

        const projectIdMatch = content.match(/Proyecto ID: (\w+)/);
        if (projectIdMatch && !activeProjectId) {
            showSidebar(projectIdMatch[1]);
            loadProjects();
            showToast('¡Proyecto creado con éxito, parce!', 'success');
        }

        if (activeProjectId) {
            chatHistory.push({ role: 'user', content: prompt });
            chatHistory.push({ role: 'assistant', content: content });
            saveChatHistory();
            loadFiles();
            showToast('Proyecto modificado correctamente', 'success');
        }
    } catch (e) {
        addMessage('assistant', '❌ Error de conexión con el servidor.');
        showToast('Error al comunicarse con los agentes', 'error');
    } finally {
        document.getElementById('agent-progress').classList.add('hidden');
        document.getElementById('send-btn').disabled = false;
    }
}

function addMessage(role, text) {
    const placeholder = document.getElementById('chat-placeholder');
    if (placeholder) placeholder.classList.add('hidden');
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `mb-3 ${role === 'user' ? 'text-right' : 'text-left'}`;
    div.innerHTML = role === 'user'
        ? `<span class="bg-blue-600 text-white px-4 py-2 rounded-lg inline-block max-w-2xl">${text}</span>`
        : `<span class="bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-4 py-2 rounded-lg inline-block max-w-2xl overflow-x-auto"><pre class="whitespace-pre-wrap text-sm">${text}</pre></span>`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function loadChatHistory() {
    chatHistory = [];
    const container = document.getElementById('chat-messages');
    container.innerHTML = '';
    document.getElementById('chat-placeholder').classList.add('hidden');
    if (!activeProjectId) return;
    fetch(`${API}/projects/${activeProjectId}/chat`)
        .then(r => r.json())
        .then(data => {
            if (data.messages && data.messages.length) {
                data.messages.forEach(m => addMessage(m.role, m.content));
            } else {
                document.getElementById('chat-placeholder').classList.remove('hidden');
            }
        }).catch(() => {});
}

function saveChatHistory() {
    if (!activeProjectId) return;
    fetch(`${API}/projects/${activeProjectId}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: chatHistory })
    }).catch(() => {});
}

// Proyectos
async function loadProjects() {
    try {
        const res = await fetch(`${API}/projects`);
        const data = await res.json();
        const list = document.getElementById('projects-list');
        list.innerHTML = data.projects.length
            ? data.projects.map(id => `
                <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 flex flex-col gap-3">
                    <div class="flex items-center gap-2">
                        <i class="fas fa-folder text-blue-500"></i>
                        <span class="font-mono text-blue-600 dark:text-blue-400 font-medium">${id}</span>
                    </div>
                    <p class="text-xs text-gray-500 dark:text-gray-400">📁 projects/${id}</p>
                    <div class="flex gap-2 mt-auto">
                        <button onclick="showSidebar('${id}')" class="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-sm px-3 py-1.5 rounded transition">Abrir</button>
                        <button onclick="deleteProject('${id}')" class="text-red-500 hover:text-red-700 text-sm px-3 py-1.5 rounded border border-red-200 dark:border-red-800 hover:bg-red-50 dark:hover:bg-red-900/20 transition">Eliminar</button>
                    </div>
                </div>`).join('')
            : `<div class="col-span-full text-center text-gray-500 dark:text-gray-400 py-10"><i class="fas fa-folder-open text-5xl mb-3"></i><p>Todavía no hay proyectos generados.</p><p class="text-sm mt-1">Usá el <b>Chat</b> para crear el primero.</p></div>`;
    } catch { /* */ }
}

async function deleteProject(id) {
    if (!confirm(`¿Estás seguro de eliminar el proyecto ${id}? Esta acción no se puede deshacer.`)) return;
    showToast('Funcionalidad de eliminación en desarrollo', 'info');
}

// Archivos
async function loadFiles() {
    if (!activeProjectId) return;
    try {
        const res = await fetch(`${API}/projects/${activeProjectId}/files`);
        const data = await res.json();
        const tree = document.getElementById('files-tree');
        tree.innerHTML = data.files.length
            ? data.files.map(f => `
                <div class="flex items-center gap-2 py-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded px-2 cursor-pointer transition" onclick="viewFile('${f}')">
                    <i class="fas fa-file-code text-blue-400 text-xs"></i>
                    <span class="font-mono text-xs truncate">${f}</span>
                </div>`).join('')
            : '<p class="text-gray-500 text-xs p-2">Sin archivos todavía</p>';
    } catch { /* */ }
}

// Ejecución
async function executeProject() {
    if (!activeProjectId) return;
    document.getElementById('tab-console').classList.remove('hidden');
    switchTab('console');
    const consoleEl = document.getElementById('console-output');
    consoleEl.textContent = '🔄 Instalando dependencias y ejecutando...\n';
    try {
        const res = await fetch(`${API}/projects/${activeProjectId}/execute`, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            consoleEl.textContent += '✅ Proyecto iniciado en http://localhost:8001\n';
            consoleEl.textContent += '📤 Salida:\n' + data.stdout + '\n';
            document.getElementById('btn-live').classList.remove('hidden');
            refreshPreview();
            showToast('Proyecto ejecutándose. Revisá la Vista previa.', 'success');
        } else {
            consoleEl.textContent += '❌ Falló la ejecución:\n' + (data.stderr || data.stdout || 'Error desconocido') + '\n';
            showToast('Error al ejecutar el proyecto', 'error');
        }
    } catch (e) {
        consoleEl.textContent += '❌ Error de conexión al ejecutar.\n';
        showToast('Error de conexión', 'error');
    }
}

function refreshPreview() {
    const iframe = document.getElementById('preview-iframe');
    iframe.src = 'http://localhost:8001';
}

function openLivePreview() {
    if (activeProjectId) window.open('http://localhost:8001', '_blank');
}

// Mejoras
async function loadImprovements() {
    const status = document.getElementById('improvement-filter')?.value || 'pending';
    try {
        const res = await fetch(`${API}/system/improvements?status=${status}`);
        const data = await res.json();
        const list = document.getElementById('improvements-list');
        list.innerHTML = data.proposals.length
            ? data.proposals.map(p => `
                <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                    <div class="flex justify-between items-start">
                        <div class="flex-1">
                            <h4 class="font-bold">${p.title}</h4>
                            <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">${p.description}</p>
                            <span class="text-xs text-gray-500">Archivo: ${p.target_file}</span>
                            ${p.suggested_code ? `<pre class="code-block text-xs mt-2 max-h-32 overflow-y-auto">${p.suggested_code}</pre>` : ''}
                        </div>
                        <div class="flex gap-2 ml-4">
                            ${p.status === 'pending' ? `
                                <button onclick="applyImprovement('${p.id}')" class="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-xs transition">Aplicar</button>
                                <button onclick="rejectImprovement('${p.id}')" class="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-xs transition">Rechazar</button>
                            ` : `<span class="text-xs px-3 py-1 rounded bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400">${p.status}</span>`}
                        </div>
                    </div>
                </div>`).join('')
            : `<div class="text-center text-gray-500 dark:text-gray-400 py-10"><i class="fas fa-check-circle text-5xl mb-3 text-green-500"></i><p>No hay propuestas con estado "${status}".</p></div>`;
    } catch { /* */ }
}

function applyImprovement(id) {
    fetch(`${API}/system/apply-improvement/${id}`, { method: 'POST' })
        .then(() => {
            loadImprovements();
            showToast('Mejora aplicada con éxito', 'success');
        });
}
function rejectImprovement(id) {
    fetch(`${API}/system/reject-improvement/${id}`, { method: 'POST' })
        .then(() => {
            loadImprovements();
            showToast('Mejora rechazada', 'info');
        });
}
function runMetaAgentOnCurrent() {
    if (!activeProjectId) return;
    fetch(`${API}/system/run-meta-agent?project_id=${activeProjectId}`, { method: 'POST' })
        .then(() => {
            loadImprovements();
            showToast('MetaAgent ejecutado', 'success');
        });
}

// Status
async function checkStatus() {
    try {
        const res = await fetch(`${API}/`);
        const data = await res.json();
        const badge = document.getElementById('status-badge');
        badge.className = data.status === 'ok' 
            ? 'px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
            : 'px-3 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
        badge.textContent = data.status === 'ok' ? 'Conectado' : 'Desconectado';
    } catch {
        const badge = document.getElementById('status-badge');
        badge.className = 'px-3 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
        badge.textContent = 'Sin conexión';
    }
}

// Atajos
document.addEventListener('keydown', e => {
    if (e.ctrlKey && e.key === 'Enter') sendPrompt();
    if (e.ctrlKey && e.key === 's') { e.preventDefault(); if (!document.getElementById('save-file-btn').classList.contains('hidden')) saveFile(); }
});

checkStatus();
setInterval(checkStatus, 30000);