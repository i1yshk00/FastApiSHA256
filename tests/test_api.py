from uuid import uuid4

import pytest
from httpx import AsyncClient

USER_EMAIL = "user@example.com"
USER_PASSWORD = "user12345"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin12345"


async def login(
    client: AsyncClient,
    *,
    username: str,
    password: str,
) -> str:
    """Authenticate through API and return Bearer access token."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    return payload["access_token"]


async def build_signature(
    client: AsyncClient,
    payload: dict,
) -> str:
    """Request webhook signature from API for a transaction payload."""
    response = await client.post("/api/v1/transactions/signature", json=payload)
    assert response.status_code == 200
    return response.json()["signature"]


def transaction_payload(
    *,
    user_id: int,
    account_id: int,
    amount: int,
) -> dict:
    """Build unsigned transaction webhook payload with random UUID id."""
    return {
        "transaction_id": str(uuid4()),
        "account_id": account_id,
        "user_id": user_id,
        "amount": amount,
    }


@pytest.mark.asyncio
async def test_user_auth_and_profile_routes(client: AsyncClient) -> None:
    """Verify user authentication and current-user route responses."""
    user_token = await login(
        client,
        username=USER_EMAIL,
        password=USER_PASSWORD,
    )
    headers = {"Authorization": f"Bearer {user_token}"}

    me_response = await client.get("/api/v1/users/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json() == {
        "id": 1,
        "email": USER_EMAIL,
        "full_name": "Test User",
    }

    accounts_response = await client.get("/api/v1/users/me/accounts", headers=headers)
    assert accounts_response.status_code == 200
    assert accounts_response.json() == [{"id": 1, "balance": 0.0}]

    transactions_response = await client.get(
        "/api/v1/users/me/transactions",
        headers=headers,
    )
    assert transactions_response.status_code == 200
    assert transactions_response.json() == []

    admin_check_response = await client.get("/api/v1/auth/is-admin", headers=headers)
    assert admin_check_response.status_code == 200
    assert admin_check_response.json() == {
        "user_id": 1,
        "email": USER_EMAIL,
        "is_admin": False,
    }

    unauthorized_response = await client.get("/api/v1/users/me")
    assert unauthorized_response.status_code == 401


@pytest.mark.asyncio
async def test_admin_user_crud_and_permissions(client: AsyncClient) -> None:
    """Verify admin-only user CRUD and regular-user access denial."""
    user_token = await login(
        client,
        username=USER_EMAIL,
        password=USER_PASSWORD,
    )
    admin_token = await login(
        client,
        username=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
    )
    user_headers = {"Authorization": f"Bearer {user_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    forbidden_response = await client.get("/api/v1/admin/users", headers=user_headers)
    assert forbidden_response.status_code == 403

    users_response = await client.get("/api/v1/admin/users", headers=admin_headers)
    assert users_response.status_code == 200
    assert users_response.json()[0]["accounts"] == [{"id": 1, "balance": 0.0}]

    create_response = await client.post(
        "/api/v1/admin/users",
        headers=admin_headers,
        json={
            "email": "created@example.com",
            "full_name": "Created User",
            "password": "created12345",
        },
    )
    assert create_response.status_code == 201
    created_user = create_response.json()
    assert created_user["email"] == "created@example.com"
    assert created_user["is_admin"] is False

    duplicate_response = await client.post(
        "/api/v1/admin/users",
        headers=admin_headers,
        json={
            "email": "created@example.com",
            "full_name": "Duplicate User",
            "password": "created12345",
        },
    )
    assert duplicate_response.status_code == 409

    update_response = await client.patch(
        f"/api/v1/admin/users/{created_user['id']}",
        headers=admin_headers,
        json={"full_name": "Updated User", "is_admin": True},
    )
    assert update_response.status_code == 200
    assert update_response.json()["full_name"] == "Updated User"
    assert update_response.json()["is_admin"] is True

    delete_response = await client.delete(
        f"/api/v1/admin/users/{created_user['id']}",
        headers=admin_headers,
    )
    assert delete_response.status_code == 204

    missing_delete_response = await client.delete(
        f"/api/v1/admin/users/{created_user['id']}",
        headers=admin_headers,
    )
    assert missing_delete_response.status_code == 404


@pytest.mark.asyncio
async def test_transaction_signature_matches_assignment_example(
    client: AsyncClient,
) -> None:
    """Verify signature generation against the example from the assignment."""
    response = await client.post(
        "/api/v1/transactions/signature",
        json={
            "transaction_id": "5eae174f-7cd0-472c-bd36-35660f00132b",
            "user_id": 1,
            "account_id": 1,
            "amount": 100,
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "signature": (
            "7b47e41efe564a062029da3367bde8844bea0fb049f894687cee5d57f2858bc8"
        ),
    }


@pytest.mark.asyncio
async def test_transaction_webhook_idempotency_and_balance_rules(
    client: AsyncClient,
) -> None:
    """Verify webhook idempotency, debits, validation, and balance limits."""
    first_payload = transaction_payload(user_id=1, account_id=10, amount=100)
    first_payload["signature"] = await build_signature(client, first_payload)

    first_response = await client.post(
        "/api/v1/transactions/webhook",
        json=first_payload,
    )
    assert first_response.status_code == 200
    assert first_response.json()["status"] == "processed"
    assert first_response.json()["balance"] == 100.0

    repeated_response = await client.post(
        "/api/v1/transactions/webhook",
        json=first_payload,
    )
    assert repeated_response.status_code == 200
    assert repeated_response.json()["status"] == "already_processed"
    assert repeated_response.json()["balance"] == 100.0

    debit_payload = transaction_payload(user_id=1, account_id=10, amount=-40)
    debit_payload["signature"] = await build_signature(client, debit_payload)
    debit_response = await client.post(
        "/api/v1/transactions/webhook",
        json=debit_payload,
    )
    assert debit_response.status_code == 200
    assert debit_response.json()["balance"] == 60.0

    zero_balance_payload = transaction_payload(user_id=1, account_id=10, amount=-60)
    zero_balance_payload["signature"] = await build_signature(
        client,
        zero_balance_payload,
    )
    zero_balance_response = await client.post(
        "/api/v1/transactions/webhook",
        json=zero_balance_payload,
    )
    assert zero_balance_response.status_code == 409
    assert zero_balance_response.json() == {
        "detail": "Account balance must remain positive",
    }

    invalid_signature_payload = transaction_payload(user_id=1, account_id=10, amount=1)
    invalid_signature_payload["signature"] = "bad"
    invalid_signature_response = await client.post(
        "/api/v1/transactions/webhook",
        json=invalid_signature_payload,
    )
    assert invalid_signature_response.status_code == 400

    zero_amount_response = await client.post(
        "/api/v1/transactions/signature",
        json=transaction_payload(user_id=1, account_id=10, amount=0),
    )
    assert zero_amount_response.status_code == 422
