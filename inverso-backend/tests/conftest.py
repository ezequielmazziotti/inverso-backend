"""
Fixtures compartidos para todos los tests.
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from dependencies import get_current_user

# ── Usuarios de prueba ────────────────────────────────────────────────────────

FREE_USER  = {"id": "user-free",  "email": "free@test.com",  "plan": "free"}
BASIC_USER = {"id": "user-basic", "email": "basic@test.com", "plan": "basic"}
PRO_USER   = {"id": "user-pro",   "email": "pro@test.com",   "plan": "pro"}


def _override_auth(user: dict):
    async def _dep():
        return user
    return _dep


@pytest.fixture
def client_free():
    app.dependency_overrides[get_current_user] = _override_auth(FREE_USER)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def client_basic():
    app.dependency_overrides[get_current_user] = _override_auth(BASIC_USER)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def client_pro():
    app.dependency_overrides[get_current_user] = _override_auth(PRO_USER)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def client_no_auth():
    """Cliente sin override de auth (usa auth real → falla sin token)."""
    with TestClient(app) as c:
        yield c
