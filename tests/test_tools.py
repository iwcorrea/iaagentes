"""Pruebas unitarias para las herramientas del ecosistema."""
import sys
from pathlib import Path

# Asegurar que la raíz del proyecto esté en el path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import os
import tempfile
from unittest.mock import patch, MagicMock

from tools.custom_tools import read_file, write_file, run_terminal

def test_read_file():
    # Usamos mkstemp para evitar problemas de bloqueo en Windows
    fd, path = tempfile.mkstemp(suffix='.txt', text=True)
    with os.fdopen(fd, 'w') as f:
        f.write("Hola mundo")
    try:
        result = read_file.run(path)
        assert "Hola mundo" in result
    finally:
        os.unlink(path)

def test_write_file():
    fd, path = tempfile.mkstemp(suffix='.txt', text=True)
    os.close(fd)  # cerramos el descriptor porque write_file abre el archivo por su cuenta
    try:
        write_file.run(f"{path}:::contenido de prueba")
        with open(path, 'r') as f:
            assert f.read() == "contenido de prueba"
    finally:
        os.unlink(path)

def test_run_terminal():
    result = run_terminal.run("echo test")
    assert "test" in result

from tools.memory_tools import save_memory_tool, search_memory_tool

@patch('tools.memory_tools.get_vector_memory')
def test_save_memory(mock_get_memory):
    mock_instance = MagicMock()
    mock_instance.add_document.return_value = True
    mock_get_memory.return_value = mock_instance
    result = save_memory_tool.run(content="Dato importante", metadata="{}")
    assert "guardada" in result

@patch('tools.memory_tools.get_vector_memory')
def test_search_memory(mock_get_memory):
    mock_instance = MagicMock()
    mock_instance.search.return_value = [
        {"content": "resultado 1", "score": 0.95},
        {"content": "resultado 2", "score": 0.80}
    ]
    mock_get_memory.return_value = mock_instance
    result = search_memory_tool.run(query="consulta", k=2)
    assert "resultado 1" in result
    assert "0.95" in result