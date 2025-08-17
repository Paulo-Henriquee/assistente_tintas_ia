from pydantic import BaseModel, EmailStr

class LoginEntrada(BaseModel):
    email: EmailStr
    senha: str

class TokenSaida(BaseModel):
    access_token: str
    token_type: str = "bearer"