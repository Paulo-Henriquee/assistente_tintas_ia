# app/services/ia/recomendador_agente.py - VERSÃO COMPLETA COM LLM

from app.services.ia.embeddings import embed_texto
from sqlalchemy.orm import Session
from sqlalchemy import text
from openai import OpenAI
from app.core.config import settings
import json
from typing import List, Dict, Any

# Cliente OpenAI
client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

def buscar_produtos_similares(db: Session, consulta: str, limite: int = 3) -> List[Dict]:
    """
    PASSO 1: Busca produtos similares usando embeddings + pgvector
    """
    if not client:
        raise RuntimeError("OPENAI_API_KEY não configurada")
    
    # Gera embedding da consulta
    embedding_consulta = embed_texto(consulta)
    
    # Busca por similaridade usando pgvector
    sql = text("""
        SELECT 
            t.id, t.nome, t.cor, t.ambiente, t.acabamento, 
            t.features, t.linha, t.descricao, t.superficie_indicada,
            te.conteudo,
            (1 - (te.embedding <=> :embedding::vector)) as score
        FROM tintas t 
        JOIN embeddings_tintas te ON t.id = te.tinta_id
        ORDER BY te.embedding <=> :embedding::vector
        LIMIT :limite
    """)
    
    # Formato correto para pgvector
    embedding_str = f"[{','.join(f'{x:.6f}' for x in embedding_consulta)}]"
    
    resultados = db.execute(sql, {
        "embedding": embedding_str,
        "limite": limite
    }).mappings().all()
    
    return [dict(item) for item in resultados]

def montar_contexto_produtos(produtos: List[Dict]) -> str:
    """
    PASSO 2: Formata produtos encontrados para o LLM
    """
    if not produtos:
        return "Nenhum produto encontrado na base de dados."
    
    contexto_produtos = []
    for i, produto in enumerate(produtos, 1):
        # Processa features JSON
        features_str = ""
        if produto.get('features'):
            try:
                features = json.loads(produto['features']) if isinstance(produto['features'], str) else produto['features']
                if isinstance(features, dict):
                    features_list = [k.replace('_', ' ').title() for k, v in features.items() if v]
                    features_str = ", ".join(features_list) if features_list else "N/A"
                else:
                    features_str = str(features)
            except:
                features_str = str(produto.get('features', 'N/A'))
        
        score = produto.get('score', 0)
        
        produto_info = f"""
PRODUTO {i}: {produto['nome']}
- Cor: {produto['cor']}
- Linha: {produto.get('linha', 'N/A')}
- Superfície: {produto.get('superficie_indicada', 'N/A')}
- Ambiente: {produto['ambiente']}
- Acabamento: {produto['acabamento']}
- Features: {features_str}
- Descrição: {produto.get('descricao', 'N/A')}
- Score de Similaridade: {score:.3f}
        """.strip()
        
        contexto_produtos.append(produto_info)
    
    return "\n\n".join(contexto_produtos)

def criar_prompt_suvinil() -> str:
    """
    PASSO 3: Cria o prompt baseado no prompt.txt do projeto
    """
    return """
Você é o Conselheiro Suvinil, especialista em tintas que ajuda clientes via chat com respostas DIRETAS e ÚTEIS.

REGRAS DE OURO:
✅ Responda em até 6 linhas + bullets (máximo)
✅ Mencione o nome EXATO do produto da base
✅ Seja específico mas conciso
✅ Use tom conversacional amigável
✅ Termine com pergunta ou dica

FORMATO IDEAL:
[Recomendação direta com o produto]
[1 linha explicando por que funciona]

• [Benefício 1]
• [Benefício 2] 
• [Benefício 3]

[Pergunta de continuidade ou dica rápida]

EXEMPLO:
"Para quartos, recomendo a **Suvinil Toque de Seda**.
Tem tecnologia sem odor e é perfeita para ambientes internos.

• Totalmente sem cheiro
• Lavável e fácil de limpar
• Acabamento acetinado suave

💡 Já escolheu a cor ou quer sugestões?"

IMPORTANTE:
- Use APENAS produtos da base fornecida
- Se não houver produto exato, adapte o mais próximo
- Seja sempre útil, nunca diga apenas "não temos"
- Use emojis com moderação (💡 para dicas, 🎨 para cores)
    """.strip()

def chamar_llm_para_recomendacao(consulta_usuario: str, contexto_produtos: str) -> str:
    """
    PASSO 4: Chama OpenAI para gerar resposta natural do Conselheiro Suvinil
    """
    if not client:
        return "Erro: OpenAI não configurado. Configure OPENAI_API_KEY no .env"
    
    prompt_sistema = criar_prompt_suvinil()
    
    prompt_usuario = f"""
CONSULTA DO CLIENTE: "{consulta_usuario}"

PRODUTOS ENCONTRADOS NA BASE SUVINIL:
{contexto_produtos}

Como Conselheiro Suvinil, recomende o melhor produto seguindo EXATAMENTE o formato especificado.
Seja direto, útil e conversacional.
    """.strip()
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario}
            ],
            max_tokens=400,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        return f"Erro ao gerar recomendação: {str(e)}"

def recomendar_com_explicacao(db: Session, consulta: str, limite: int = 3) -> Dict[str, Any]:
    """
    FUNÇÃO PRINCIPAL: Orquestra todo o processo de recomendação
    """
    
    try:
        # Passo 1: Buscar produtos similares usando embeddings
        produtos = buscar_produtos_similares(db, consulta, limite)
        
        # Passo 2: Montar contexto formatado
        contexto = montar_contexto_produtos(produtos)
        
        # Passo 3: Gerar resposta com LLM usando prompt Suvinil
        resposta_llm = chamar_llm_para_recomendacao(consulta, contexto)
        
        # Passo 4: Retorna resultado estruturado
        return {
            "resposta": resposta_llm,
            "produtos_encontrados": produtos,
            "contexto_usado": contexto,
            "consulta_original": consulta,
            "modelo_embedding": "text-embedding-3-small",
            "modelo_llm": "gpt-4o-mini"
        }
        
    except Exception as e:
        # Fallback para busca simples se embeddings falharem
        print(f"⚠️  Erro em embeddings, usando busca simples: {str(e)}")
        return busca_simples_fallback(db, consulta, limite)

def busca_simples_fallback(db: Session, consulta: str, limite: int) -> Dict[str, Any]:
    """
    FALLBACK: Busca simples caso embeddings falhem
    """
    try:
        sql = text("""
            SELECT id, nome, cor, ambiente, acabamento, linha, descricao
            FROM tintas 
            WHERE LOWER(nome) LIKE :busca 
               OR LOWER(cor) LIKE :busca
               OR LOWER(descricao) LIKE :busca
            LIMIT :limite
        """)
        
        busca_termo = f"%{consulta.lower()}%"
        resultados = db.execute(sql, {
            "busca": busca_termo,
            "limite": limite
        }).mappings().all()
        
        produtos = [dict(item) for item in resultados]
        
        # Resposta simples sem LLM
        if produtos:
            primeiro = produtos[0]
            resposta = f"Encontrei {len(produtos)} produto(s) para '{consulta}'\n\n"
            resposta += f"Recomendo: **{primeiro['nome']}** - {primeiro['cor']}\n"
            resposta += f"• Ambiente: {primeiro['ambiente']}\n"
            resposta += f"• Acabamento: {primeiro['acabamento']}"
        else:
            resposta = f"Não encontrei produtos específicos para '{consulta}'. Pode ser mais específico sobre o que precisa?"
        
        return {
            "resposta": resposta,
            "produtos_encontrados": produtos,
            "contexto_usado": f"Busca simples por: {consulta}",
            "consulta_original": consulta,
            "status": "fallback_busca_simples"
        }
        
    except Exception as e:
        return {
            "resposta": f"Erro no sistema de recomendação: {str(e)}",
            "produtos_encontrados": [],
            "contexto_usado": "",
            "consulta_original": consulta,
            "status": "erro"
        }

# EXEMPLO DE USO:
# from app.db.session import SessionLocal
# db = SessionLocal()
# resultado = recomendar_com_explicacao(db, "preciso pintar meu quarto sem cheiro")
# print(resultado["resposta"])