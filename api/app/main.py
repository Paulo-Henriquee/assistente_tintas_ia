from fastapi import FastAPI
from app.routers import auth, usuarios, tintas, busca
from app.routers import chat  # ← IMPORT SEPARADO PARA EVITAR CONFLITO

app = FastAPI(
    title="Assistente de Tintas API", 
    version="0.1.0",
    description="API com IA para recomendação de tintas usando busca semântica"
)

# Routers existentes
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(tintas.router)
app.include_router(busca.router)

# 🤖 NOVO: Router do chat com IA
app.include_router(chat.router)

@app.get("/")
def root():
    return {
        "message": "🎨 Assistente de Tintas API",
        "endpoints": {
            "docs": "/docs",
            "chat": "/chat/recomendar",
            "health": "/chat/health",
            "busca": "/busca/recomendar"
        }
    }