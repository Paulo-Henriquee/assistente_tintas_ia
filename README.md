# 🤖 Assistente Inteligente de Tintas Suvinil

> **Desafio Back IA - Loomi | Time Node AI**
> Conselheiro virtual especializado em recomendação de tintas usando IA e busca semântica

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-blue)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-orange)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)

## 📋 Índice

- [🎯 Sobre o Projeto](#-sobre-o-projeto)
- [✨ Funcionalidades Implementadas](#-funcionalidades-implementadas)
- [🏗️ Arquitetura](#️-arquitetura)
- [🚀 Como Executar](#-como-executar)
- [🧪 Testando a API](#-testando-a-api)
- [🤖 Stack de IA](#-stack-de-ia)
- [📊 Base de Dados](#-base-de-dados)
- [🛠️ Ferramentas de IA Utilizadas](#️-ferramentas-de-ia-utilizadas)
- [🔍 Decisões Técnicas](#-decisões-técnicas)
- [📈 Performance Observada](#-performance-observada)
- [🎨 Próximos Passos](#-próximos-passos)

## 🎯 Sobre o Projeto

Este projeto implementa um **Assistente Inteligente** que atua como especialista virtual em tintas Suvinil, desenvolvido como solução para o Desafio Back IA da Loomi. O sistema combina busca semântica com IA conversacional para oferecer recomendações personalizadas de tintas.

### Problema Resolvido
- Consulta inteligente de catálogo de tintas baseada em linguagem natural
- Recomendações contextualizadas considerando ambiente, superfície e necessidades
- Interface conversacional que simula atendimento especializado

### Abordagem Técnica
- **RAG (Retrieval-Augmented Generation)** para busca semântica em base de produtos
- **LLM** para geração de respostas conversacionais no tom Suvinil
- **Sistema híbrido** com fallback para garantir sempre uma resposta

## ✅ Funcionalidades Implementadas

### 🧠 **Sistema de Recomendação com IA**
- ✅ Busca semântica usando OpenAI embeddings + pgvector
- ✅ Similarity search com scoring de relevância
- ✅ Sistema de fallback para busca tradicional SQL
- ✅ Tratamento robusto de erros e edge cases

### 💬 **Chat Conversacional**
- ✅ GPT-4o-mini integrado para respostas naturais
- ✅ Prompt engineering específico para tom Suvinil
- ✅ Formato estruturado: recomendação + benefícios + pergunta
- ✅ Contexto dos produtos encontrados enviado ao LLM

### 🎯 **API Completa**
- ✅ CRUD para tintas e usuários (implementado previamente)
- ✅ Sistema de autenticação JWT com RBAC
- ✅ Documentação automática com Swagger
- ✅ Endpoints específicos para chat com IA
- ✅ Health checks e testes de conectividade

## 🏗️ Arquitetura

### Stack Implementado
- **Backend**: Python 3.11 + FastAPI
- **Banco de Dados**: PostgreSQL 16 + extensão pgvector
- **IA**: OpenAI GPT-4o-mini + Embeddings API
- **Deploy**: Docker + Docker Compose
- **Autenticação**: JWT implementado em rotas existentes

### Fluxo de Processamento Real
```
Usuário → FastAPI → Chat Router → Recomendador Agent
                                       ↓
                   OpenAI Embeddings → pgvector Search
                                       ↓
                   Produtos Relevantes → GPT-4o-mini → Resposta
```

## 🚀 Como Executar

### Pré-requisitos
- Docker & Docker Compose
- Chave da OpenAI API

### 1. Clone e configure
```bash
git clone <repo-url>
cd tintas
cp .env.example .env
# Configure OPENAI_API_KEY no .env
```

### 2. Execute
```bash
docker compose up --build
```

### 3. Acesse
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Chat**: POST `/chat/recomendar`

## 🧪 Testando a API

### Endpoints Funcionais

#### Health Checks
```bash
# Serviço básico
curl http://localhost:8000/chat/health

# Conexão com banco (confirma 100 tintas)
curl http://localhost:8000/chat/test-db

# Conexão OpenAI (testa embeddings)
curl http://localhost:8000/chat/test-embeddings
```

#### Chat Principal
```bash
curl -X POST "http://localhost:8000/chat/recomendar" \
     -H "Content-Type: application/json" \
     -d '{
       "mensagem": "tinta para cozinha resistente a gordura",
       "limite_produtos": 3
     }'
```

### Resposta Real Observada
```json
{
  "resposta": "Para a cozinha, recomendo a **Suvinil Clássica**.\nÉ resistente ao calor e ideal para ambientes internos.\n\n• Acabamento acetinado que facilita a limpeza\n• Resistente à manchas\n• Secagem rápida, ideal para reformas\n\n💡 Você já pensou na cor que gostaria de usar?",
  "produtos_encontrados": [
    {
      "id": "2257b48c-848c-419e-a472-b253f1318cf0",
      "nome": "Suvinil Criativa",
      "cor": "Cinza Urbano",
      "ambiente": "interno", 
      "acabamento": "fosco",
      "linha": "Econômica",
      "score": 0.626
    }
  ]
}
```

## 🤖 Stack de IA

### Componentes Reais

#### 🔍 **RAG Implementado**
- **Embeddings**: OpenAI `text-embedding-3-small` (1536 dimensões)
- **Vector Store**: pgvector no PostgreSQL
- **Retrieval**: Busca por similaridade coseno com `<=>` operator
- **Augmentation**: Contexto estruturado enviado ao LLM

#### 🧠 **LLM Integration**
- **Modelo**: GPT-4o-mini da OpenAI
- **Input**: Prompt do sistema + contexto dos produtos + query do usuário
- **Output**: Resposta conversacional formatada

#### 🛠️ **Agente Inteligente**
- **Orquestração**: Função `recomendar_com_explicacao()` 
- **Ferramentas**: Busca semântica + busca SQL (fallback)
- **Decisão**: Automática baseada em disponibilidade de embeddings

### Fluxo Técnico Real
1. **Input**: Query do usuário via `/chat/recomendar`
2. **Embedding**: Conversão para vetor 1536D via OpenAI
3. **Search**: pgvector similarity search com score
4. **Context**: Formatação dos produtos para prompt do LLM
5. **LLM**: GPT-4o-mini gera resposta seguindo template Suvinil
6. **Output**: JSON com resposta + produtos + debug info (opcional)

## 📊 Base de Dados

### Dados Confirmados
- **Fonte**: CSV `Base_de_Dados_Tintas_Enriquecida.csv`
- **Total**: 100 produtos Suvinil (confirmado via `/chat/test-db`)
- **Embeddings**: Tabela `embeddings_tintas` populada e funcional

### Schema Implementado
```sql
-- Tabela principal (já existia)
CREATE TABLE tintas (
    id UUID PRIMARY KEY,
    nome VARCHAR(255),
    cor VARCHAR(255), 
    superficie_indicada VARCHAR(255),
    ambiente ambiente_enum, -- interno/externo
    acabamento acabamento_enum, -- fosco/acetinado/semibrilho/brilho
    features JSONB,
    linha VARCHAR(100),
    descricao TEXT
);

-- Embeddings para busca semântica (adicionada)
CREATE TABLE embeddings_tintas (
    tinta_id UUID PRIMARY KEY REFERENCES tintas(id),
    embedding VECTOR(1536),
    conteudo TEXT,
    atualizado_em TIMESTAMP
);
```

## 🛠️ Ferramentas de IA Utilizadas

### Desenvolvimento Assistido por IA

#### **Claude (Anthropic)** - Principal ⭐
- **Uso**: 90% do desenvolvimento da funcionalidade de IA
- **Aplicações**:
  - Arquitetura do sistema RAG
  - Implementação das funções de busca semântica
  - Estruturação do agente inteligente
  - Criação do endpoint `/chat/recomendar`
  - Debugging e otimizações

#### **ChatGPT/OpenAI** - Secundário
- **Uso**: 10% - Principalmente para banco de dados e API base
- **Aplicações**:
  - Estruturação inicial da API FastAPI
  - Configuração do PostgreSQL + pgvector
  - Geração de dados de teste

### Prompts Reais Utilizados

#### **📋 [Documentação Completa de Prompts](https://drive.google.com/drive/folders/1pm7rh2d2Exgv04R2ougGF3SPddV2mwpF?usp=sharing)**

**Prompts disponíveis na documentação:**

1. **Especialista em Tintas Suvinil** - Prompt principal do sistema
   - Função, público-alvo e comportamento do assistente
   - Estilo de linguagem e formato de respostas
   - Exemplos de interações ideais
   - **Uso**: Base para o sistema de prompts do GPT-4o-mini

2. **Desenvolvimento com Claude** - Prompts técnicos
   - Arquitetura do sistema RAG
   - Implementação de busca semântica
   - Integração OpenAI + pgvector
   - **Resultado**: Estrutura modular implementada

3. **Iterações e Refinamentos** - Processo de desenvolvimento
   - Debugging e otimizações
   - Ajustes de performance
   - Tratamento de edge cases

## 🔍 Decisões Técnicas

### Escolhas Arquiteturais Reais

#### **RAG vs. Fine-tuning**
- **Decisão**: RAG com embeddings + retrieval
- **Motivo**: Flexibilidade para atualizações da base sem retreinar
- **Implementação**: OpenAI embeddings + pgvector

#### **Agente Único vs. Multi-Agentes**
- **Decisão**: Agente único com ferramentas múltiplas
- **Motivo**: Simplicidade de implementação e manutenção
- **Resultado**: Uma função orquestradora com fallbacks

#### **pgvector vs. Vector DBs externos**
- **Decisão**: pgvector integrado ao PostgreSQL existente
- **Motivo**: Aproveitamento da infraestrutura existente
- **Benefício**: Zero configuração adicional de serviços

#### **GPT-4o-mini vs. GPT-4**
- **Decisão**: GPT-4o-mini para produção
- **Motivo**: Custo-benefício adequado para o caso de uso
- **Validação**: Qualidade das respostas atendeu expectativas

### Sistema de Fallback Implementado
```python
try:
    # Tentativa 1: Busca semântica
    produtos = buscar_produtos_similares(db, consulta, limite)
    resposta = chamar_llm_para_recomendacao(consulta, produtos)
except Exception:
    # Fallback: Busca SQL tradicional
    produtos = busca_sql_like(db, consulta, limite)
    resposta = resposta_estruturada_simples(produtos)
```

## 📈 Performance Observada

### Métricas Reais (Postman)
- **Response Time Total**: ~2.6s
- **Status Code**: 200 OK (funcionando)
- **Relevância**: Score 0.626 para "cozinha" (boa relevância)
- **Disponibilidade**: 100% durante testes

### Componentes de Latência (estimados)
- Embedding generation: ~300ms
- Vector search: ~100ms  
- LLM generation: ~2000ms
- Processing overhead: ~200ms

### Custos Estimados
- ~$0.0003 por embedding (1 vez por produto)
- ~$0.001 por resposta LLM
- **Total por consulta**: ~$0.001 USD

## 🎨 Próximos Passos

### Funcionalidades Não Implementadas

#### **1. Histórico de Conversa** 
- **Status**: Não implementado
- **Complexidade**: Média
- **Benefício**: Contexto contínuo em sessões

#### **2. Geração Visual (DALL-E)**
- **Status**: Não implementado  
- **Complexidade**: Alta
- **Benefício**: Visualização de ambientes pintados

#### **3. Sistema Multi-Agentes**
- **Status**: Arquitetura para futuro
- **Complexidade**: Alta
- **Benefício**: Especialização por domínio

### Melhorias Técnicas Identificadas

#### **Performance**
- [ ] Cache de embeddings frequentes
- [ ] Otimização de tokens no prompt
- [ ] Paralelização de embedding + LLM

#### **Robustez**  
- [ ] Testes automatizados (pytest)
- [ ] Logging estruturado das decisões
- [ ] Métricas de qualidade das respostas

#### **Observabilidade**
- [ ] Rastreamento do raciocínio do agente
- [ ] Dashboard de performance
- [ ] Análise de satisfação do usuário

---

## 📧 Sobre o Desenvolvimento

**Desafio Back IA - Loomi**
- **Desenvolvedor**: Paulo Amaral
- **Time**: Node AI  
- **Período**: Agosto 2025
- **IA Assistente Principal**: Claude (Anthropic)

### Uso Estratégico de IA no Desenvolvimento
Este projeto demonstra uso prático de IA como ferramenta de desenvolvimento:
- **90% do código de IA** desenvolvido com assistência do Claude
- **Prompts específicos** para cada etapa da implementação
- **Iteração rápida** permitindo foco na arquitetura e lógica de negócio
- **Qualidade de código** mantida através de revisão e teste manual

---

*"IA conversacional aplicada ao varejo, desenvolvida com IA"* 🤖✨