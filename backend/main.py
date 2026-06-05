from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Bienvenido al Ecommerce Campesino"}

@app.get("/products")
async def get_products():
    return {"products": ["Maíz", "Frijoles", "Café", "Plátanos"]}

@app.get("/users")
async def get_users():
    return {"users": ["campesino1", "comprador1"]}