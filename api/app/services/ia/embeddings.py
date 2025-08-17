# app/services/ia/embeddings.py
import os, csv, json, unicodedata
from typing import Dict, Any, Iterable, Optional, List
from sqlalchemy import text
from sqlalchemy.orm import Session
from openai import OpenAI
from app.core.config import settings
from app.db.session import SessionLocal

MODEL = settings.embedding_model or "text-embedding-3-small"
DIM = int(os.getenv("EMBEDDING_DIM", "1536"))
_client: Optional[OpenAI] = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

# ---------- utils ----------
def _norm(v: Any) -> str:
    return (str(v or "").strip())

def _slug(s: str) -> str:
    s = s.replace("\ufeff", "").replace("\xa0", " ")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.strip().lower().replace("\n", " ").replace("\r", " ")
    for ch in ("  ", "   "): s = s.replace(ch, " ")
    for ch in (" ", "-", "/", "\\", "(", ")", "."): s = s.replace(ch, "_")
    while "__" in s: s = s.replace("__", "_")
    return s.strip("_")

def _ascii(v: str) -> str:
    v = str(v or "").strip().lower()
    v = unicodedata.normalize("NFKD", v)
    return "".join(ch for ch in v if not unicodedata.combining(ch))

def map_ambiente(v: str) -> str:
    x = _ascii(v).replace("-", " ")
    if x in {"interno","interior","dentro","area interna","área interna"}: return "interno"
    if x in {"externo","exterior","fora","area externa","área externa","fachada"}: return "externo"
    return "interno"

def map_acabamento(v: str) -> str:
    x = _ascii(v).replace("-", " ").replace("_", " ")
    if x in {"fosco","mate","matte","fosco completo"}: return "fosco"
    if x in {"acetinado","satin","seda"}: return "acetinado"
    if x in {"semibrilho","semi brilho","eggshell","egg shell","casca de ovo"}: return "semibrilho"
    if x in {"brilho","brilhante","alto brilho","gloss"}: return "brilho"
    return "fosco"

def _bool_from_any(v: Any) -> Optional[bool]:
    if v is None: return None
    s = str(v).strip().lower()
    if s in {"1","true","t","yes","y","sim","verdadeiro"}: return True
    if s in {"0","false","f","no","n","nao","não","falso"}: return False
    return None

def _float_or_none(v: Any) -> Optional[float]:
    try:
        return float(v) if v not in (None, "", "null", "None") else None
    except Exception:
        return None

def _to_vec_literal(vec: Iterable[float]) -> str:
    return "[" + ",".join(f"{float(x):.6f}" for x in vec) + "]"

def embed_texto(txt: str) -> list[float]:
    if not _client:
        raise RuntimeError("OPENAI_API_KEY não definido no .env")
    r = _client.embeddings.create(model=MODEL, input=txt)
    return r.data[0].embedding

# ---------- DB ----------
def _find_tinta_id(db: Session, nome: str, cor: str, linha: Optional[str]) -> Optional[str]:
    sql = text("""
        SELECT id::text FROM public.tintas
        WHERE lower(nome)=lower(:nome) AND lower(cor)=lower(:cor)
          AND COALESCE(linha,'') = COALESCE(:linha,'')
        LIMIT 1;
    """)
    return db.execute(sql, {"nome": nome, "cor": cor, "linha": linha}).scalar()

def _insert_tinta(db: Session, d: Dict[str, Any]) -> str:
    sql = text("""
        INSERT INTO public.tintas
            (nome, cor, superficie_indicada, ambiente, acabamento, features, linha, descricao,
             rendimento_m2_litro, resistencia_uv, voc_baixo, criado_em, atualizado_em)
        VALUES
            (:nome, :cor, :superficie_indicada,
             CAST(:ambiente AS public.ambiente_tinta),
             CAST(:acabamento AS public.acabamento_tinta),
             COALESCE(:features, '{}'::jsonb), :linha, :descricao,
             :rendimento_m2_litro, :resistencia_uv, :voc_baixo, NOW(), NOW())
        RETURNING id::text;
    """)
    return db.execute(sql, d).scalar()

def _update_tinta(db: Session, tinta_id: str, d: Dict[str, Any]) -> None:
    sql = text("""
        UPDATE public.tintas SET
            superficie_indicada = :superficie_indicada,
            ambiente  = CAST(:ambiente  AS public.ambiente_tinta),
            acabamento = CAST(:acabamento AS public.acabamento_tinta),
            features = COALESCE(:features, '{}'::jsonb),
            linha = :linha,
            descricao = :descricao,
            rendimento_m2_litro = :rendimento_m2_litro,
            resistencia_uv = :resistencia_uv,
            voc_baixo = :voc_baixo,
            atualizado_em = NOW()
        WHERE id = CAST(:tinta_id AS uuid);
    """)
    db.execute(sql, {**d, "tinta_id": tinta_id})

def _upsert_embedding(db: Session, tinta_id: str, conteudo: str, emb: list[float]) -> None:
    sql = text("""
        INSERT INTO public.embeddings_tintas (tinta_id, embedding, conteudo, atualizado_em)
        VALUES (CAST(:tinta_id AS uuid), (:vec)::vector, :conteudo, NOW())
        ON CONFLICT (tinta_id) DO UPDATE
        SET embedding = EXCLUDED.embedding,
            conteudo  = EXCLUDED.conteudo,
            atualizado_em = NOW();
    """)
    db.execute(sql, {"tinta_id": tinta_id, "conteudo": conteudo, "vec": _to_vec_literal(emb)})

# ---------- CSV mapeamento ----------
ALIASES = {
    "nome": {"nome","nome_da_tinta","produto","nome_tinta","Nome da tinta"},
    "cor": {"cor","tom","cor_nome","cor_tinta","Cor"},
    "superficie_indicada": {"superficie_indicada","superficie","tipo_de_superficie","superficie_recomendada","superfície_indicada","Tipo de superfície indicada"},
    "ambiente": {"ambiente","ambiente_indicado","ambiente_(interno/externo)","uso","Ambiente"},
    "acabamento": {"acabamento","tipo_de_acabamento","Tipo de acabamento"},
    "linha": {"linha","linha_produto","segmento","Linha"},
    "descricao": {"descricao","descrição","observacoes","observações","detalhes"},
    "rendimento_m2_litro": {"rendimento","rendimento_m2_litro","rendimento_(m2/litro)","rendimento_m2_l"},
    "resistencia_uv": {"resistencia_uv","resistente_uv","resistência_uv","resistencia_ao_sol"},
    "voc_baixo": {"voc_baixo","baixo_voc","voc"},
}
FEATURES_TEXT_HEADERS = {"Features relevantes"}

def _build_map(fieldnames: list[str]) -> Dict[str, str]:
    slugs = {fn: _slug(fn) for fn in fieldnames}
    inv = {v: k for k, v in slugs.items()}

    def pick(keys:set[str]) -> Optional[str]:
        for k in keys:
            if k in inv: return inv[k]
        return None

    mapping: Dict[str, str] = {}
    for target, keys in ALIASES.items():
        mapping[target] = pick({ _slug(k) for k in keys }) or ""

    for fn in fieldnames:
        if fn in FEATURES_TEXT_HEADERS:
            mapping["_features_text_col"] = fn
            break
    return mapping

def sniff_csv_columns(caminho_csv: str) -> Dict[str, Any]:
    with open(caminho_csv, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f); fns = reader.fieldnames or []
    return {"fieldnames": fns, "mapping": _build_map(fns)}

# ---------- Pipeline ----------
def indexar_csv_tintas(caminho_csv: str) -> dict:
    db: Session = SessionLocal()
    lidas = ok = ignoradas = 0
    try:
        with open(caminho_csv, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            mapping = _build_map(fieldnames)

            for row in reader:
                lidas += 1
                def get_mapped(key: str, default: str = "") -> str:
                    src = mapping.get(key) or ""
                    return _norm(row.get(src)) if src else default

                nome = get_mapped("nome")
                cor = get_mapped("cor")
                if not nome or not cor:
                    ignoradas += 1
                    continue

                superficie = get_mapped("superficie_indicada", "alvenaria")
                ambiente = map_ambiente(get_mapped("ambiente", "interno"))
                acabamento = map_acabamento(get_mapped("acabamento", "fosco"))
                linha = get_mapped("linha") or None
                descricao = get_mapped("descricao")
                rendimento = _float_or_none(get_mapped("rendimento_m2_litro"))
                res_uv = _bool_from_any(get_mapped("resistencia_uv"))
                voc_baixo = _bool_from_any(get_mapped("voc_baixo"))

                feats = {}
                ft_col = mapping.get("_features_text_col")
                if ft_col:
                    raw = _norm(row.get(ft_col))
                    if raw:
                        for tok in [t.strip() for t in raw.replace(";", ",").split(",") if t.strip()]:
                            feats[_slug(tok)] = True
                features_json = json.dumps(feats) if feats else None

                dados = {
                    "nome": nome, "cor": cor, "superficie_indicada": superficie,
                    "ambiente": ambiente, "acabamento": acabamento,
                    "features": features_json, "linha": linha, "descricao": descricao,
                    "rendimento_m2_litro": rendimento, "resistencia_uv": res_uv, "voc_baixo": voc_baixo,
                }

                tinta_id = _find_tinta_id(db, nome, cor, linha)
                if tinta_id: _update_tinta(db, tinta_id, dados)
                else: tinta_id = _insert_tinta(db, dados)

                conteudo = " ".join(s for s in [nome, cor, superficie, ambiente, acabamento, (linha or ""), descricao] if s).strip()
                emb = embed_texto(conteudo)
                _upsert_embedding(db, tinta_id, conteudo, emb)
                ok += 1

        db.commit()
        return {"linhas_lidas": lidas, "linhas_indexadas": ok, "linhas_ignoradas": ignoradas, "modelo": MODEL, "dim": DIM, "mapping": mapping}
    finally:
        db.close()

# ==========================================
# 🤖 FUNÇÕES DE RECOMENDAÇÃO COM IA
# ==========================================

def buscar_produtos_similares(db: Session, consulta: str, limite: int = 3) -> List[Dict]:
    """
    Busca produtos similares usando embeddings + pgvector
    """
    if not _client:
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
    embedding_str = _to_vec_literal(embedding_consulta)
    
    resultados = db.execute(sql, {
        "embedding": embedding_str,
        "limite": limite
    }).mappings().all()
    
    return [dict(item) for item in resultados]

def montar_contexto_produtos(produtos: List[Dict]) -> str:
    """
    Formata produtos encontrados para o LLM
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
- Score: {score:.3f}
        """.strip()
        
        contexto_produtos.append(produto_info)
    
    return "\n\n".join(contexto_produtos)

def criar_prompt_suvinil() -> str:
    """
    Cria o prompt baseado no prompt.txt do projeto
    """
    return """
Você é o Conselheiro Suvinil, especialista em tintas que ajuda clientes via chat com respostas DIRETAS e ÚTEIS.

REGRAS:
✅ Responda em até 6 linhas + bullets (máximo)
✅ Mencione o nome EXATO do produto da base
✅ Seja específico mas conciso
✅ Use tom conversacional amigável
✅ Termine com pergunta ou dica

FORMATO:
[Recomendação direta com produto]
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
    """.strip()

def chamar_llm_para_recomendacao(consulta_usuario: str, contexto_produtos: str) -> str:
    """
    Chama OpenAI para gerar resposta natural do Conselheiro Suvinil
    """
    if not _client:
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
        response = _client.chat.completions.create(
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
            "modelo_embedding": MODEL,
            "modelo_llm": "gpt-4o-mini"
        }
        
    except Exception as e:
        print(f"⚠️  Erro em embeddings: {str(e)}")
        # Fallback para busca simples
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
        
        if produtos:
            primeiro = produtos[0]
            resposta = f"Encontrei {len(produtos)} produto(s) para '{consulta}'\n\n"
            resposta += f"Recomendo: **{primeiro['nome']}** - {primeiro['cor']}\n"
            resposta += f"• Ambiente: {primeiro['ambiente']}\n"
            resposta += f"• Acabamento: {primeiro['acabamento']}"
        else:
            resposta = f"Não encontrei produtos específicos para '{consulta}'. Pode ser mais específico?"
        
        return {
            "resposta": resposta,
            "produtos_encontrados": produtos,
            "contexto_usado": f"Busca simples por: {consulta}",
            "consulta_original": consulta,
            "status": "fallback_busca_simples"
        }
        
    except Exception as e:
        return {
            "resposta": f"Erro no sistema: {str(e)}",
            "produtos_encontrados": [],
            "contexto_usado": "",
            "consulta_original": consulta,
            "status": "erro"
        }

if __name__ == "__main__":
    caminho = "app/arquivos/Base_de_Dados_Tintas_Enriquecida.csv"
    print(sniff_csv_columns(caminho))
    print(indexar_csv_tintas(caminho))