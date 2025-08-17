from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.auth import LoginEntrada, TokenSaida
from app.core.security import criar_token_jwt, verificar_senha
from app.db.session import SessionLocal
from app.models.usuario import Usuario

router = APIRouter(prefix="/auth", tags=["auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/login", response_model=TokenSaida)
def login(dados: LoginEntrada, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.email == dados.email).first()
    if not user or not verificar_senha(dados.senha, user.hash_senha):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    token = criar_token_jwt(str(user.id), user.papel.value)
    return TokenSaida(access_token=token)