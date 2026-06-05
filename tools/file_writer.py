def write_file(path, content):
    with open(path, "w", encoding="utf-8") as file:
        file.write(content)

    return f"Archivo creado correctamente: {path}"