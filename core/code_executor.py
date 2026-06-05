import subprocess
import os

# ==========================================
# RUN PYTHON FILE
# ==========================================

def run_python_file(file_path):

    try:

        result = subprocess.run(

            ["python", file_path],

            capture_output=True,
            text=True,
            timeout=30
        )

        return {

            "success": result.returncode == 0,

            "stdout": result.stdout,

            "stderr": result.stderr
        }

    except Exception as e:

        return {

            "success": False,

            "stdout": "",

            "stderr": str(e)
        }