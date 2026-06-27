import io
import pytest


async def _register_and_login(client, attorney_payload) -> str:
    await client.post("/api/v1/auth/register", json=attorney_payload)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": attorney_payload["email"], "password": attorney_payload["password"]},
    )
    return resp.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _lead_data(first_name="Alice", last_name="Smith", email="alice@example.com") -> dict:
    return {"first_name": first_name, "last_name": last_name, "email": email}


def _resume_file() -> tuple:
    return ("resume.pdf", io.BytesIO(b"%PDF-1.4 fake resume content"), "application/pdf")


@pytest.mark.asyncio
async def test_create_lead_success(client):
    response = await client.post(
        "/api/v1/leads",
        data=_lead_data(),
        files={"resume": _resume_file()},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["state"] == "PENDING"
    assert data["email"] == "alice@example.com"


@pytest.mark.asyncio
async def test_create_lead_invalid_mime(client):
    response = await client.post(
        "/api/v1/leads",
        data=_lead_data(),
        files={"resume": ("resume.txt", io.BytesIO(b"not a pdf"), "text/plain")},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_leads_requires_auth(client):
    response = await client.get("/api/v1/leads")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_list_leads_paginated(client, attorney_payload):
    token = await _register_and_login(client, attorney_payload)

    for i in range(3):
        await client.post(
            "/api/v1/leads",
            data=_lead_data(email=f"user{i}@example.com"),
            files={"resume": _resume_file()},
        )

    response = await client.get(
        "/api/v1/leads?page=1&page_size=2", headers=_auth_headers(token)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["total_pages"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_get_lead_by_id(client, attorney_payload):
    token = await _register_and_login(client, attorney_payload)

    create_resp = await client.post(
        "/api/v1/leads",
        data=_lead_data(),
        files={"resume": _resume_file()},
    )
    lead_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/leads/{lead_id}", headers=_auth_headers(token))
    assert response.status_code == 200
    assert response.json()["id"] == lead_id


@pytest.mark.asyncio
async def test_mark_lead_reached_out(client, attorney_payload):
    token = await _register_and_login(client, attorney_payload)

    create_resp = await client.post(
        "/api/v1/leads",
        data=_lead_data(),
        files={"resume": _resume_file()},
    )
    lead_id = create_resp.json()["id"]

    response = await client.patch(
        f"/api/v1/leads/{lead_id}/state",
        json={"state": "REACHED_OUT"},
        headers=_auth_headers(token),
    )
    assert response.status_code == 200
    assert response.json()["state"] == "REACHED_OUT"


@pytest.mark.asyncio
async def test_mark_reached_out_twice_returns_conflict(client, attorney_payload):
    token = await _register_and_login(client, attorney_payload)

    create_resp = await client.post(
        "/api/v1/leads",
        data=_lead_data(),
        files={"resume": _resume_file()},
    )
    lead_id = create_resp.json()["id"]
    headers = _auth_headers(token)

    await client.patch(
        f"/api/v1/leads/{lead_id}/state", json={"state": "REACHED_OUT"}, headers=headers
    )
    response = await client.patch(
        f"/api/v1/leads/{lead_id}/state", json={"state": "REACHED_OUT"}, headers=headers
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_filter_leads_by_state(client, attorney_payload):
    token = await _register_and_login(client, attorney_payload)
    headers = _auth_headers(token)

    for i in range(2):
        resp = await client.post(
            "/api/v1/leads",
            data=_lead_data(email=f"pending{i}@example.com"),
            files={"resume": _resume_file()},
        )
        if i == 0:
            lead_id = resp.json()["id"]
            await client.patch(
                f"/api/v1/leads/{lead_id}/state",
                json={"state": "REACHED_OUT"},
                headers=headers,
            )

    pending_resp = await client.get("/api/v1/leads?state=PENDING", headers=headers)
    assert pending_resp.json()["total"] == 1

    reached_resp = await client.get("/api/v1/leads?state=REACHED_OUT", headers=headers)
    assert reached_resp.json()["total"] == 1
