import pytest


@pytest.mark.asyncio
async def test_register_attorney(client, attorney_payload):
    response = await client.post("/api/v1/auth/register", json=attorney_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == attorney_payload["email"]
    assert data["name"] == attorney_payload["name"]
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client, attorney_payload):
    await client.post("/api/v1/auth/register", json=attorney_payload)
    response = await client.post("/api/v1/auth/register", json=attorney_payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client, attorney_payload):
    await client.post("/api/v1/auth/register", json=attorney_payload)
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": attorney_payload["email"], "password": attorney_payload["password"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client, attorney_payload):
    await client.post("/api/v1/auth/register", json=attorney_payload)
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": attorney_payload["email"], "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@test.com", "password": "pass"},
    )
    assert response.status_code == 401
