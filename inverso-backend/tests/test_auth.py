"""
Tests para autenticación y protección de rutas.
"""


def test_analyze_basic_requires_auth(client_no_auth):
    r = client_no_auth.post("/analyze/basic", json={"ticker": "GGAL"})
    assert r.status_code == 401


def test_analyze_deep_requires_auth(client_no_auth):
    r = client_no_auth.post("/analyze/deep", json={"ticker": "GGAL"})
    assert r.status_code == 401


def test_portfolio_fixed_requires_auth(client_no_auth):
    r = client_no_auth.post("/portfolio/fixed", json={
        "amount": 100000,
        "currency": "ars",
        "start_date": "2024-01-01",
        "allocations": [{"ticker": "GGAL", "percentage": 100}],
    })
    assert r.status_code == 401


def test_portfolio_dynamic_requires_auth(client_no_auth):
    r = client_no_auth.post("/portfolio/dynamic", json={"operations": [], "currency": "ars"})
    assert r.status_code == 401


def test_export_pdf_requires_auth(client_no_auth):
    r = client_no_auth.post("/export/pdf", json={"ticker": "GGAL", "score": 7})
    assert r.status_code == 401


def test_history_requires_auth(client_no_auth):
    r = client_no_auth.get("/analyze/history")
    assert r.status_code == 401


def test_assets_are_public(client_no_auth):
    """Los endpoints de assets no requieren auth."""
    r = client_no_auth.get("/assets/search?q=YPF")
    assert r.status_code == 200

    r = client_no_auth.get("/assets/market-overview")
    assert r.status_code == 200
