"""
Tests para el endpoint GET /auth/me y el router de portfolio history.
"""


def test_me_returns_user_info(client_free):
    r = client_free.get("/auth/me")
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == "free@test.com"
    assert body["plan"] == "free"
    assert "id" in body


def test_me_returns_correct_plan_for_pro(client_pro):
    r = client_pro.get("/auth/me")
    assert r.status_code == 200
    assert r.json()["plan"] == "pro"


def test_me_requires_auth(client_no_auth):
    r = client_no_auth.get("/auth/me")
    assert r.status_code == 401


def test_portfolio_history_requires_auth(client_no_auth):
    r = client_no_auth.get("/portfolio/history")
    assert r.status_code == 401


def test_portfolio_history_returns_list(client_free):
    from unittest.mock import patch
    mock_sims = [{"id": "1", "type": "fixed", "name": None, "created_at": "2025-04-01T10:00:00"}]
    with patch("routers.portfolio.get_user_simulations", return_value=mock_sims):
        r = client_free.get("/portfolio/history")
    assert r.status_code == 200
    assert r.json()["simulations"] == mock_sims
