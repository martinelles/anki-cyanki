import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    response = await client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "testpassword", "name": "Test User"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

@pytest.mark.asyncio
async def test_register_existing_user(client: AsyncClient):
    # Register first time
    await client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "testpassword", "name": "Test User"}
    )
    # A partir da segunda conta o convite e exigido antes do e-mail duplicado,
    # entao a tentativa precisa de um codigo valido para chegar ao 400.
    login = await client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": "testpassword"},
    )
    token = login.json()["access_token"]
    convite = await client.post(
        "/api/auth/invites", headers={"Authorization": f"Bearer {token}"}
    )
    # Register second time
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpassword",
            "name": "Test User",
            "invite_code": convite.json()["code"],
        },
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]

@pytest.mark.asyncio
async def test_login_user(client: AsyncClient):
    # Register first
    await client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "testpassword", "name": "Test User"}
    )
    
    # Login
    response = await client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": "testpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    # Register first
    await client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "testpassword", "name": "Test User"}
    )
    
    # Login with wrong password
    response = await client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401


async def _registrar_dono(client: AsyncClient) -> str:
    """Cria a primeira conta (que dispensa convite) e devolve o token dela."""
    await client.post(
        "/api/auth/register",
        json={"email": "dono@example.com", "password": "testpassword"},
    )
    resposta = await client.post(
        "/api/auth/login",
        data={"username": "dono@example.com", "password": "testpassword"},
    )
    return resposta.json()["access_token"]


@pytest.mark.asyncio
async def test_segunda_conta_exige_convite(client: AsyncClient):
    await _registrar_dono(client)
    resposta = await client.post(
        "/api/auth/register",
        json={"email": "intruso@example.com", "password": "testpassword"},
    )
    assert resposta.status_code == 403


@pytest.mark.asyncio
async def test_convite_invalido_e_recusado(client: AsyncClient):
    await _registrar_dono(client)
    resposta = await client.post(
        "/api/auth/register",
        json={
            "email": "intruso@example.com",
            "password": "testpassword",
            "invite_code": "codigo-que-nao-existe",
        },
    )
    assert resposta.status_code == 403


@pytest.mark.asyncio
async def test_convite_vale_uma_vez_so(client: AsyncClient):
    token = await _registrar_dono(client)
    convite = await client.post(
        "/api/auth/invites", headers={"Authorization": f"Bearer {token}"}
    )
    assert convite.status_code == 201
    codigo = convite.json()["code"]

    primeira = await client.post(
        "/api/auth/register",
        json={
            "email": "convidado@example.com",
            "password": "testpassword",
            "invite_code": codigo,
        },
    )
    assert primeira.status_code == 201

    segunda = await client.post(
        "/api/auth/register",
        json={
            "email": "outro@example.com",
            "password": "testpassword",
            "invite_code": codigo,
        },
    )
    assert segunda.status_code == 403


@pytest.mark.asyncio
async def test_gerar_convite_exige_login(client: AsyncClient):
    resposta = await client.post("/api/auth/invites")
    assert resposta.status_code == 401
