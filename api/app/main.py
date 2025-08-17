from fastapi import FastAPI
from app.routers import auth, usuarios, tintas, busca

app = FastAPI(title="Assistente de Tintas API", version="0.1.0")

app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(tintas.router)
app.include_router(busca.router)