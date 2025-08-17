import uuid
from sqlalchemy import String, Enum, text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
import enum

class Papel(str, enum.Enum):
    admin = "admin"
    editor = "editor"
    leitor = "leitor"

class Usuario(Base):
    __tablename__ = "usuarios"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hash_senha: Mapped[str] = mapped_column(String(255))
    papel: Mapped[Papel] = mapped_column(Enum(Papel), default=Papel.leitor)
    criado_em: Mapped[str] = mapped_column(server_default=text("NOW()"))