import uuid
import httpx

BASE_URL = "http://localhost:8000"

def test_criar_usuario():
    email = f"user_{uuid.uuid4().hex[:8]}@teste.com"
    r = httpx.post(f"{BASE_URL}/usuarios/", json={"nome": "Usuário Teste", "email": email, "senha": "123456"})
    assert r.status_code in (200, 201), r.text
    assert r.json()["email"] == email

def test_criar_usuario_duplicado():
    email = f"dup_{uuid.uuid4().hex[:8]}@teste.com"
    payload = {"nome": "Duplicado", "email": email, "senha": "123456"}

    r1 = httpx.post(f"{BASE_URL}/usuarios/", json=payload)
    assert r1.status_code in (200, 201), r1.text

    r2 = httpx.post(f"{BASE_URL}/usuarios/", json=payload)
    assert r2.status_code == 400  # já existe
