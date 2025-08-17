from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class TintaEmbedding(Base):
    __tablename__ = "embeddings_tintas"
    tinta_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("tintas.id"), primary_key=True)
    embedding: Mapped[list[float]] = mapped_column("embedding", type_="vector(1536)")
    conteudo: Mapped[str] = mapped_column()
    atualizado_em: Mapped[str] = mapped_column(server_default=text("NOW()"))