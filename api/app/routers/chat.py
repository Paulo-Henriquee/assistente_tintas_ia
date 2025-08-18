# app/routers/chat.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.db.session import SessionLocal
from app.services.ia.embeddings import recomendar_com_explicacao

router = APIRouter(prefix="/chat", tags=["chat"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Schemas
class ChatRequest(BaseModel):
    mensagem: str
    limite_produtos: int = 3

class ProdutoRecomendado(BaseModel):
    id: str
    nome: str
    cor: str
    ambiente: str
    acabamento: str
    linha: Optional[str] = None
    score: Optional[float] = None
    superficie_indicada: Optional[str] = None

class ChatResponse(BaseModel):
    resposta: str
    produtos_encontrados: List[ProdutoRecomendado]
    debug_info: Optional[Dict[str, Any]] = None

@router.post("/recomendar", response_model=ChatResponse)
def chat_recomendacao(
    request: ChatRequest, 
    debug: bool = False,
    db: Session = Depends(get_db)
):
    """🤖 Conselheiro Suvinil com IA
    
    Exemplo:
    {
        "mensagem": "preciso pintar meu quarto sem cheiro",
        "limite_produtos": 3
    }
    """
    
    if not request.mensagem.strip():
        raise HTTPException(status_code=400, detail="Mensagem não pode estar vazia")
    
    try:
        resultado = recomendar_com_explicacao(
            db=db, 
            consulta=request.mensagem.strip(), 
            limite=request.limite_produtos
        )
        
        # Converte produtos para schema
        produtos_formatados = []
        for produto in resultado["produtos_encontrados"]:
            produtos_formatados.append(ProdutoRecomendado(
                id=str(produto["id"]),
                nome=produto["nome"],
                cor=produto["cor"],
                ambiente=produto["ambiente"],
                acabamento=produto["acabamento"],
                linha=produto.get("linha"),
                score=produto.get("score"),
                superficie_indicada=produto.get("superficie_indicada")
            ))
        
        # Debug info
        debug_info = None
        if debug:
            debug_info = {
                "contexto_usado": resultado.get("contexto_usado", ""),
                "consulta_original": resultado.get("consulta_original", ""),
                "total_produtos": len(resultado["produtos_encontrados"]),
                "modelo_embedding": resultado.get("modelo_embedding", "N/A"),
                "modelo_llm": resultado.get("modelo_llm", "N/A"),
                "status": resultado.get("status", "ok")
            }
        
        return ChatResponse(
            resposta=resultado["resposta"],
            produtos_encontrados=produtos_formatados,
            debug_info=debug_info
        )
        
    except Exception as e:
        print(f"❌ ERRO no chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro no recomendador: {str(e)}")

@router.get("/health")
def health_check():
    """Verifica se o serviço está funcionando"""
    return {"status": "ok", "service": "chat-recomendador-ia"}

@router.get("/test-embeddings")
def test_embeddings_connection():
    """Testa se consegue gerar embeddings"""
    try:
        from app.services.ia.embeddings import embed_texto
        from app.core.config import settings
        
        if not settings.openai_api_key:
            return {"status": "error", "message": "OPENAI_API_KEY não configurada"}
        
        teste_embedding = embed_texto("teste de conexão")
        
        return {
            "status": "ok",
            "openai_configurado": True,
            "embedding_dimensoes": len(teste_embedding),
            "embedding_modelo": settings.embedding_model
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Erro ao testar embeddings: {str(e)}"}

@router.get("/test-db")
def test_database_connection(db: Session = Depends(get_db)):
    """Testa conexão com banco e conta embeddings"""
    try:
        from sqlalchemy import text
        
        total_tintas = db.execute(text("SELECT COUNT(*) FROM tintas")).scalar()
        
        try:
            total_embeddings = db.execute(text("SELECT COUNT(*) FROM embeddings_tintas")).scalar()
        except:
            total_embeddings = "Tabela não existe"
        
        return {
            "status": "ok",
            "total_tintas": total_tintas,
            "total_embeddings": total_embeddings,
            "database": "conectado"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no banco: {str(e)}")