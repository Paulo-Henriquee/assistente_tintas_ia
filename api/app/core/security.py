from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def gerar_hash_senha(senha: str) -> str:
    return pwd_context.hash(senha)

def verificar_senha(senha: str, hash_senha: str) -> bool:
    return pwd_context.verify(senha, hash_senha)

def criar_token_jwt(sub: str, papel: str, exp_min: Optional[int] = None) -> str:
    expira = datetime.now(timezone.utc) + timedelta(minutes=exp_min or settings.jwt_exp_min)
    to_encode = {"sub": sub, "papel": papel, "exp": expira}
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_alg)

def decodificar_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])