import threading

_status_lock = threading.Lock()
_agent_status = {
    "Director IA": {"status": "idle", "emoji": "🧠"},
    "Code Generator": {"status": "idle", "emoji": "💻"},
    "Frontend Designer": {"status": "idle", "emoji": "🎨"},
    "QA Auditor": {"status": "idle", "emoji": "🔍"},
    "Repair Agent": {"status": "idle", "emoji": "🔧"},
    "Dependency Manager": {"status": "idle", "emoji": "📦"},
}

def set_agent_status(agent_name, status):
    with _status_lock:
        if agent_name in _agent_status:
            _agent_status[agent_name]["status"] = status

def set_all_status(status):
    with _status_lock:
        for agent in _agent_status.values():
            agent["status"] = status

def get_status():
    with _status_lock:
        return dict(_agent_status)