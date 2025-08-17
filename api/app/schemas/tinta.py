from pydantic import BaseModel
from enum import Enum
from typing import Optional, Dict, Any

class Ambiente(str, Enum):
    interno = "interno"
    externo = "externo"

class Acabamento(str, Enum):
    fosco = "fosco"
    acetinado = "acetinado"
    semibrilho = "semibrilho"
    brilho = "brilho"

class TintaBase(BaseModel):
    nome: str
    cor: str
    superficie_indicada: str
    ambiente: Ambiente
    acabamento: Acabamento
    features: Dict[str, Any] = {}
    linha: str
    descricao: str = ""
    rendimento_m2_litro: Optional[float] = None
    resistencia_uv: Optional[bool] = None
    voc_baixo: Optional[bool] = None

class TintaCriar(TintaBase):
    pass

class TintaEditar(BaseModel):
    nome: Optional[str] = None
    cor: Optional[str] = None
    superficie_indicada: Optional[str] = None
    ambiente: Optional[Ambiente] = None
    acabamento: Optional[Acabamento] = None
    features: Optional[Dict[str, Any]] = None
    linha: Optional[str] = None
    descricao: Optional[str] = None
    rendimento_m2_litro: Optional[float] = None
    resistencia_uv: Optional[bool] = None
    voc_baixo: Optional[bool] = None

class TintaSaida(TintaBase):
    id: str