from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.schemas.tinta import TintaCriar, TintaEditar, TintaSaida
from app.models.tinta import Tinta

router = APIRouter(prefix="/tintas", tags=["tintas"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=TintaSaida)
def criar_tinta(payload: TintaCriar, db: Session = Depends(get_db)):
    tinta = Tinta(**payload.model_dump())
    db.add(tinta)
    db.commit()
    db.refresh(tinta)
    return TintaSaida(id=str(tinta.id), **payload.model_dump())

@router.get("/", response_model=list[TintaSaida])
def listar_tintas(db: Session = Depends(get_db)):
    itens = db.query(Tinta).all()
    return [TintaSaida(id=str(t.id), **{k: getattr(t, k) for k in TintaSaida.model_fields if k != 'id'}) for t in itens]

@router.get("/{tinta_id}", response_model=TintaSaida)
def obter_tinta(tinta_id: str, db: Session = Depends(get_db)):
    t = db.get(Tinta, tinta_id)
    if not t:
        raise HTTPException(404, "Tinta não encontrada")
    return TintaSaida(id=str(t.id), **{k: getattr(t, k) for k in TintaSaida.model_fields if k != 'id'})

@router.patch("/{tinta_id}", response_model=TintaSaida)
def editar_tinta(tinta_id: str, payload: TintaEditar, db: Session = Depends(get_db)):
    t = db.get(Tinta, tinta_id)
    if not t:
        raise HTTPException(404, "Tinta não encontrada")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(t, k, v)
    db.add(t)
    db.commit()
    db.refresh(t)
    return TintaSaida(id=str(t.id), **{k: getattr(t, k) for k in TintaSaida.model_fields if k != 'id'})

@router.delete("/{tinta_id}")
def deletar_tinta(tinta_id: str, db: Session = Depends(get_db)):
    t = db.get(Tinta, tinta_id)
    if not t:
        raise HTTPException(404, "Tinta não encontrada")
    db.delete(t)
    db.commit()
    return {"ok": True}