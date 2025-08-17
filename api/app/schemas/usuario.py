from pydantic import BaseModel, EmailStr
from enum import Enum

class Papel(str, Enum):
    admin = "admin"
    editor = "editor"
    leitor = "leitor"

class UsuarioBase(BaseModel):
    nome: str
    email: EmailStr
    papel: Papel = Papel.leitor

class UsuarioCriar(UsuarioBase):
    senha: str

class UsuarioSaida(UsuarioBase):
    id: str