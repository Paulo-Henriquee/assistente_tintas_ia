# 🎨 Assistente Inteligente de Tintas

[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/DB-PostgreSQL%2016-336791?logo=postgresql)](https://www.postgresql.org/)
[![pgvector](https://img.shields.io/badge/Extension-pgvector-0052CC)](https://github.com/pgvector/pgvector)
[![OpenAI](https://img.shields.io/badge/AI-OpenAI%20Embeddings-412991?logo=openai)](https://platform.openai.com/)
[![pytest](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest)](https://docs.pytest.org/)
[![Docker](https://img.shields.io/badge/container-Docker-2496ED?logo=docker)](https://www.docker.com/)

Sistema de recomendação de tintas baseado em **RAG (Retrieval-Augmented Generation)**, com API em FastAPI, banco PostgreSQL + **pgvector**, autenticação JWT e ingestão de embeddings via OpenAI.

---

## 📑 Sumário
- [Stack](#-stack)
- [Arquitetura](#-arquitetura)
- [Banco de Dados](#-banco-de-dados)
- [Setup](#-setup)
- [Execução](#-execução)
- [Ingestão de Embeddings](#-ingestão-de-embeddings)
- [Testes](#-testes)
- [Endpoints Principais](#-endpoints-principais)
- [Problemas Comuns](#-problemas-comuns)
- [Decisões & Trade-offs](#-decisões--trade-offs)
- [Roadmap](#-roadmap-curto)
- [Segurança](#-segurança)
- [Licença](#-licença)

---

## 🔧 Stack

- **Linguagem:** Python 3.11
- **API:** FastAPI + Uvicorn
- **ORM/DB:** SQLAlchemy + PostgreSQL 16 + **pgvector**
- **Auth:** JWT (HS256)
- **IA:** OpenAI Embeddings (`text-embedding-3-small`, 1536 dims)
- **Container:** Docker & Docker Compose
- **Testes:** pytest + httpx
- **Doc:** Swagger/OpenAPI (`/docs`) e ReDoc (`/redoc`)

---

## 🧱 Arquitetura

```
api/
└── app/
    ├── core/                # Config (settings/.env), security (JWT)
    ├── db/                  # Session, base, init scripts (pgvector)
    ├── models/              # SQLAlchemy models
    ├── routers/             # auth, usuarios, tintas, busca
    ├── schemas/             # Pydantic (request/response)
    ├── services/
    │   └── ia/              # embeddings, recomendador
    ├── arquivos/            # CSV (amostras)
    └── main.py
tests/
└── api/                     # test_auth.py, test_usuarios.py, test_tintas.py, test_busca.py
docker-compose.yml
api/Dockerfile
```

---

## 🗃️ Banco de Dados

Enums (schema `public`):
- `ambiente_tinta`: `interno` | `externo`
- `acabamento_tinta`: `fosco` | `acetinado` | `semibrilho` | `brilho`

Tabelas principais:

```sql
-- Tintas
CREATE TABLE public.tintas (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  nome text NOT NULL,
  cor text NOT NULL,
  superficie_indicada text NOT NULL,
  ambiente public.ambiente_tinta NOT NULL,
  acabamento public.acabamento_tinta NOT NULL,
  features jsonb NULL,
  linha text NULL,
  descricao text NULL,
  rendimento_m2_litro numeric NULL,
  resistencia_uv bool NULL,
  voc_baixo bool NULL,
  criado_em timestamp DEFAULT now() NOT NULL,
  atualizado_em timestamp DEFAULT now() NOT NULL
);

-- Embeddings
CREATE TABLE public.embeddings_tintas (
  tinta_id uuid PRIMARY KEY REFERENCES public.tintas(id) ON DELETE CASCADE,
  embedding vector NOT NULL,
  conteudo text NOT NULL,
  atualizado_em timestamp DEFAULT now() NOT NULL
);
```

> Habilite a extensão **pgvector** no banco (`CREATE EXTENSION IF NOT EXISTS vector;`).

---

## ⚙️ Setup

**Pré-requisitos**
- Docker + Docker Compose
- Conta/Chave da OpenAI (opcional — existe fallback para testes)

**.env.example** (não commitar `.env` real)
```env
POSTGRES_DB=projetos
POSTGRES_USER=postgres
POSTGRES_PASSWORD=CHANGE_ME
DATABASE_URL=postgresql+psycopg://postgres:CHANGE_ME@db:5432/projetos

JWT_SECRET=CHANGE_ME
JWT_ALG=HS256
JWT_EXP_MIN=60

OPENAI_API_KEY=sk-CHANGE_ME
EMBEDDING_MODEL=text-embedding-3-small
```

> Copie para `.env` localmente e preencha os valores.

---

## ▶️ Execução

```bash
docker compose up --build
# API:     http://localhost:8000
# Swagger: http://localhost:8000/docs
# ReDoc:   http://localhost:8000/redoc
# Health:  http://localhost:8000/healthz (se implementado)
```

---

## 🤖 Ingestão de Embeddings

1. Coloque o CSV de exemplo em:
```
api/app/arquivos/Base_de_Dados_Tintas_Enriquecida.csv
```

2. Execute a indexação (dentro do container):
```bash
docker compose exec api python -c "from app.services.ia.embeddings import indexar_csv_tintas; print(indexar_csv_tintas('app/arquivos/Base_de_Dados_Tintas_Enriquecida.csv'))"
```

3. (Opcional) Verifique o mapeamento automático:
```bash
docker compose exec api python -c "from app.services.ia.embeddings import sniff_csv_columns; import json; print(json.dumps(sniff_csv_columns('app/arquivos/Base_de_Dados_Tintas_Enriquecida.csv'), ensure_ascii=False, indent=2))"
```

> Sem `OPENAI_API_KEY` você pode usar **embeddings randômicos** para testes.

---

## 🧪 Testes

```bash
pytest -v
# ou
docker compose exec api pytest -v
```

- `test_auth.py` — login (JWT)
- `test_usuarios.py` — criação/duplicado
- `test_tintas.py` — CRUD (inclui PATCH)
- `test_busca.py` — recomendação (pula se não houver `OPENAI_API_KEY`)

---

## 🔑 Endpoints Principais

- `POST /usuarios/` — criar usuário
- `POST /auth/login` — login (retorna `access_token`)
- `GET /tintas/` — listar (filtros por `ambiente`, `acabamento`, `features`, etc.)
- `POST /tintas/` — criar
- `PATCH /tintas/{id}` — atualizar
- `DELETE /tintas/{id}` — remover
- `GET /busca/recomendar?q=...&limite=3` — recomendação de tintas

**Auth:** `Authorization: Bearer <access_token>`

---

## ⚠️ Problemas Comuns
- **Dialeto SQLAlchemy**: usar `postgresql+psycopg://...`
- **bcrypt warnings**: fixar `bcrypt==4.0.1`
- **email-validator**: adicionar `pydantic[email]`
- **Python 3.13**: usar container com Python 3.11
- **pgvector**: garantir `CREATE EXTENSION vector;`

---

## 🧭 Decisões & Trade-offs
- **PostgreSQL + pgvector** para RAG direto no SQL.
- **FastAPI** pela rapidez, tipagem e docs nativas.
- **Embeddings no banco** (menos dependência de serviços externos).
- **Fallback** de embeddings para testes sem chave da OpenAI.

---

## 🗺️ Roadmap curto
- Mock/seed de embeddings nos testes
- Observabilidade (logs, métricas, traces)
- RBAC (admin/editor/leitor)
- Front simples para consulta/recomendação
- Alembic para migrações

---

## 🔒 Segurança
- Não commitar `.env` (use `.env.example`).
- Rotas sensíveis atrás de JWT; considere **rate limit** e **CORS restrito**.
- Em produção, proteger ou desabilitar `/docs`/`/redoc`.
- Usar HTTPS e secrets gerenciados (Docker secrets/Vars).

---

## 📄 Licença
Este projeto é distribuído sob a licença **MIT** (ver `LICENSE`).