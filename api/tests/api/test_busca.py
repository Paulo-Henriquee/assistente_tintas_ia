import os
import httpx

BASE_URL = "http://localhost:8000"

def test_recomendacao_basica_funciona():
    if not os.getenv("OPENAI_API_KEY"):
        import pytest
        pytest.skip("Sem OPENAI_API_KEY — pulando teste de recomendação.")

    r = httpx.get(f"{BASE_URL}/busca/recomendar", params={"q": "quero tinta lavável sem odor", "limite": 3})
    assert r.status_code == 200, r.text
    itens = r.json()
    assert isinstance(itens, list)
