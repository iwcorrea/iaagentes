import os

# ==========================================
# SCAN PROJECT FILES
# ==========================================

def scan_project(root_path="workspace"):

    project_data = []

    for root, dirs, files in os.walk(root_path):

        for file in files:

            # ======================================
            # ONLY CODE FILES
            # ======================================

            if file.endswith((
                ".py",
                ".js",
                ".jsx",
                ".ts",
                ".tsx",
                ".json",
                ".sql"
            )):

                full_path = os.path.join(
                    root,
                    file
                )

                try:

                    with open(
                        full_path,
                        "r",
                        encoding="utf-8"
                    ) as f:

                        content = f.read()

                    project_data.append({

                        "path": full_path,

                        "content": content
                    })

                except Exception as e:

                    print(
                        f"Error reading {full_path}: {e}"
                    )

    return project_data