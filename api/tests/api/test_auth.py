import uuid
import httpx

BASE_URL = "http://localhost:8000"

def test_login():
    email = f"login_{uuid.uuid4().hex[:8]}@teste.com"
    user = {"nome": "Teste Login", "email": email, "senha": "123456"}

    r = httpx.post(f"{BASE_URL}/usuarios/", json=user)
    assert r.status_code in (200, 201), r.text

    r = httpx.post(f"{BASE_URL}/auth/login", json={"email": email, "senha": "123456"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert "access_token" in body and body["token_type"] == "bearer"
