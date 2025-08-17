from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.schemas.usuario import UsuarioCriar, UsuarioSaida
from app.models.usuario import Usuario, Papel
from app.core.security import gerar_hash_senha

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=UsuarioSaida)
def criar_usuario(payload: UsuarioCriar, db: Session = Depends(get_db)):
    if db.query(Usuario).filter(Usuario.email == payload.email).first():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")
    usuario = Usuario(
        nome=payload.nome,
        email=payload.email,
        hash_senha=gerar_hash_senha(payload.senha),
        papel=payload.papel.value,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return UsuarioSaida(id=str(usuario.id), nome=usuario.nome, email=usuario.email, papel=usuario.papel)