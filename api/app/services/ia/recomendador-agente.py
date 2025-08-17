from app.services.ia.embeddings import embed_texto
from sqlalchemy.orm import Session
from sqlalchemy import text

PROMPT_BASE = (
    "Você é um especialista em tintas. Use o contexto de produtos e as preferências do usuário "
    "para recomendar tintas. Responda em português, de forma objetiva."
)

def recomendar_com_explicacao(db: Session, consulta: str, limite: int = 3) -> dict:
    v = embed_texto(consulta)
    sql = text(
        """
        SELECT t.id, t.nome, t.cor, t.ambiente, t.acabamento, t.features, t.linha, te.conteudo
        FROM tintas t JOIN tintas_embeddings te ON t.id = te.tinta_id
        ORDER BY te.embedding <=> :v
        LIMIT :limite
        """
    )
    itens = db.execute(sql, {"v": v, "limite": limite}).mappings().all()
    contexto = "\n\n".join([f"Produto: {i['nome']} | Linha: {i['linha']} | Features: {i['features']}" for i in itens])
    # Aqui você pode chamar um LLM (OpenAI/Anthropic) para gerar a resposta final usando PROMPT_BASE + contexto
    resposta = {
        "sugestoes": [
            {"id": str(i["id"]), "nome": i["nome"], "ambiente": i["ambiente"], "acabamento": i["acabamento"]}
            for i in itens
        ],
        "explicacao": f"{PROMPT_BASE}\n\nContexto:\n{contexto}\n\nConsulta do usuário: {consulta}",
    }
    return resposta