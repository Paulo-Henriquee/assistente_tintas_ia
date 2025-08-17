from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.ia.embeddings import embed_texto

router = APIRouter(prefix="/busca", tags=["busca"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/recomendar")
def recomendar(q: str, limite: int = 5, db: Session = Depends(get_db)):
    # Gera embedding do texto da consulta
    v = embed_texto(q)
    # Busca por similaridade (pgvector)
    sql = text(
        """
        SELECT t.id, t.nome, t.cor, t.ambiente, t.acabamento, t.features, t.linha,
               te.conteudo,
               (1 - (te.embedding <=> :v)) AS score
        FROM tintas t
        JOIN tintas_embeddings te ON t.id = te.tinta_id
        ORDER BY te.embedding <=> :v
        LIMIT :limite
        """
    )
    res = db.execute(sql, {"v": v, "limite": limite}).mappings().all()
    return [{**r, "score": float(r["score"])} for r in res]