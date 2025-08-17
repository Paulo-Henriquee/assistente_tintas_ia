import uuid
from sqlalchemy import String, JSON, Enum, Boolean, Numeric, text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
import enum

class Ambiente(str, enum.Enum):
    interno = "interno"
    externo = "externo"

class Acabamento(str, enum.Enum):
    fosco = "fosco",0
    acetinado = "acetinado"
    semibrilho = "semibrilho"
    brilho = "brilho"

class Tinta(Base):
    __tablename__ = "tintas"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(255), index=True)
    cor: Mapped[str] = mapped_column(String(255), index=True)
    superficie_indicada: Mapped[str] = mapped_column(String(255), index=True)
    ambiente: Mapped[Ambiente] = mapped_column(Enum(Ambiente))
    acabamento: Mapped[Acabamento] = mapped_column(Enum(Acabamento))
    features: Mapped[dict] = mapped_column(JSON, default=dict)
    linha: Mapped[str] = mapped_column(String(100), index=True)
    descricao: Mapped[str] = mapped_column(String, default="")
    rendimento_m2_litro: Mapped[float | None] = mapped_column(Numeric(10,2), nullable=True)
    resistencia_uv: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    voc_baixo: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    criado_em: Mapped[str] = mapped_column(server_default=text("NOW()"))
    atualizado_em: Mapped[str] = mapped_column(server_default=text("NOW()"))