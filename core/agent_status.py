import threading

_status_lock = threading.Lock()
_agent_status = {
    "Director IA": {"status": "idle", "emoji": "🧠", "current_task": ""},
    "Code Generator": {"status": "idle", "emoji": "💻", "current_task": ""},
    "Frontend Designer": {"status": "idle", "emoji": "🎨", "current_task": ""},
    "QA Auditor": {"status": "idle", "emoji": "🔍", "current_task": ""},
    "Repair Agent": {"status": "idle", "emoji": "🔧", "current_task": ""},
    "Dependency Manager": {"status": "idle", "emoji": "📦", "current_task": ""},
}

# Progreso general (0 a 100)
_progress = 0

def set_agent_status(agent_name, status, current_task=""):
    with _status_lock:
        if agent_name in _agent_status:
            _agent_status[agent_name]["status"] = status
            _agent_status[agent_name]["current_task"] = current_task

def set_all_status(status, current_task=""):
    with _status_lock:
        for agent in _agent_status.values():
            agent["status"] = status
            agent["current_task"] = current_task

def set_progress(value):
    global _progress
    with _status_lock:
        _progress = max(0, min(100, value))

def get_status():
    with _status_lock:
        return dict(_agent_status)

def get_progress():
    with _status_lock:
        return _progress