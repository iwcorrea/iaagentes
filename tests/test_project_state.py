"""
Pruebas unitarias para la persistencia del estado del proyecto.
"""
import tempfile
import os
from pathlib import Path
from core.project_state import ProjectState


def test_project_state_creation():
    with tempfile.TemporaryDirectory() as tmpdir:
        state = ProjectState(tmpdir)
        assert state.state_file.exists()
        data = state.to_dict()
        assert "phases_completed" in data
        assert data["phases_completed"] == []


def test_mark_phase_completed():
    with tempfile.TemporaryDirectory() as tmpdir:
        state = ProjectState(tmpdir)
        state.mark_phase_completed("generation")
        assert state.is_phase_completed("generation") is True
        assert state.is_phase_completed("audit") is False


def test_file_manifest():
    with tempfile.TemporaryDirectory() as tmpdir:
        state = ProjectState(tmpdir)
        # Simular archivo guardado
        (Path(tmpdir) / "main.py").write_text("print('hello')")
        state.add_file_manifest_entry("main.py", "Punto de entrada", size=14)
        manifest = state.get_files_manifest()
        assert len(manifest) == 1
        assert manifest[0]["path"] == "main.py"

        # Contexto
        ctx = state.get_manifest_as_context()
        assert "main.py" in ctx
        assert "Punto de entrada" in ctx


def test_summary():
    with tempfile.TemporaryDirectory() as tmpdir:
        state = ProjectState(tmpdir)
        state.mark_phase_completed("generation")
        state.add_file_manifest_entry("a.py", "archivo a")
        summary = state.get_summary()
        assert summary["phases_completed"] == 1
        assert summary["files_generated"] == 1
        assert summary["can_resume"] is True