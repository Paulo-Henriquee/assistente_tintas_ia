import os
import uuid
import pytest
import httpx

BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")
DEFAULT_PASSWORD = "senha123"


def _unique_email(prefix: str = "tester") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}@exemplo.com"


@pytest.fixture()
def client():
    """Novo client HTTP por teste (evita estado compartilhado)."""
    return httpx.Client(base_url=BASE_URL, timeout=20.0)


@pytest.fixture()
def user_data():
    """Gera dados únicos de usuário para cada teste."""
    return {
        "nome": f"Tester {uuid.uuid4().hex[:4]}",
        "email": _unique_email(),
        "senha": DEFAULT_PASSWORD,
        "papel": "editor",
    }


@pytest.fixture()
def token(client, user_data):
    """
    Cria um usuário único e retorna um token JWT válido.
    Evita colisão com e-mails existentes.
    """
    # tenta criar; se colidir (improvável), gera outro e-mail e tenta de novo
    for _ in range(3):
        r = client.post("/usuarios/", json=user_data)
        if r.status_code in (200, 201):
            break
        # e-mail já existe (400) -> regere e tenta novamente
        if r.status_code == 400:
            user_data["email"] = _unique_email("retry")
            continue
        # qualquer outro erro deve falhar o teste com mensagem clara
        assert False, f"Falha ao criar usuário: {r.status_code} {r.text}"

    r = client.post("/auth/login", json={"email": user_data["email"], "senha": user_data["senha"]})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture()
def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# ---------- TINTAS ----------

def _tinta_payload_base():
    """Payload mínimo válido para criação de tinta, com campos exigidos pelo schema."""
    return {
        "nome": f"Tinta {uuid.uuid4().hex[:6]}",
        "cor": "cinza",
        "superficie_indicada": "alvenaria",
        "ambiente": "interno",
        "acabamento": "fosco",
        "linha": "Premium",
        "descricao": "Tinta de testes",
        "rendimento_m2_litro": 12.5,
        "resistencia_uv": False,
        "voc_baixo": True,
        "features": {"lavavel": True, "sem_odor": True},
    }


@pytest.fixture()
def tinta_payload():
    """Fornece um payload pronto e idempotente para criação de tinta."""
    return _tinta_payload_base()


@pytest.fixture()
def tinta_criada(client, tinta_payload):
    """
    Cria uma tinta antes do teste e apaga após o teste.
    Retorna o dicionário da tinta criada.
    """
    r = client.post("/tintas/", json=tinta_payload)
    assert r.status_code == 200, r.text
    tinta = r.json()

    # cleanup depois do teste
    yield tinta

    # tenta deletar; se já foi deletada no teste, ignora erro 404
    dr = client.delete(f"/tintas/{tinta['id']}")
    if dr.status_code not in (200, 404):
        raise AssertionError(f"Falha ao limpar tinta {tinta['id']}: {dr.status_code} {dr.text}")
