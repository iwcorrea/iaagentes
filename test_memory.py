from memory.vector_memory import save_memory, search_memory

save_memory("El backend principal usa FastAPI y MySQL")

results = search_memory("Qué tecnología usa el backend?")

print(results)