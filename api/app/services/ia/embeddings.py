from app.core.config import settings
from openai import OpenAI

_client = OpenAI(api_key=settings.openai_api_key)

def embed_texto(texto: str) -> list[float]:
    resp = _client.embeddings.create(model=settings.embedding_model, input=texto)
    return resp.data[0].embedding