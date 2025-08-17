import uuid
import httpx

BASE_URL = "http://localhost:8000"

def _payload_tinta():
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

def test_criar_listar_tinta():
    r = httpx.post(f"{BASE_URL}/tintas/", json=_payload_tinta())
    assert r.status_code == 200, r.text
    tinta_id = r.json()["id"]

    r_list = httpx.get(f"{BASE_URL}/tintas/")
    assert r_list.status_code == 200
    assert any(t["id"] == tinta_id for t in r_list.json())

def test_editar_deletar_tinta():
    r = httpx.post(f"{BASE_URL}/tintas/", json=_payload_tinta())
    assert r.status_code == 200, r.text
    tinta_id = r.json()["id"]

    # sua API expõe PATCH (não PUT)
    r_edit = httpx.patch(f"{BASE_URL}/tintas/{tinta_id}", json={"descricao": "Atualizada"})
    assert r_edit.status_code == 200, r_edit.text
    assert r_edit.json()["descricao"] == "Atualizada"

    r_del = httpx.delete(f"{BASE_URL}/tintas/{tinta_id}")
    assert r_del.status_code == 200
