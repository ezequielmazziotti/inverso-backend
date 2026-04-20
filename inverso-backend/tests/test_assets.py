"""
Tests para los endpoints de activos (públicos, no requieren auth).
"""
from services.market_data import search_assets, POPULAR_TICKERS, ASSET_NAMES


def test_search_by_ticker():
    results = search_assets("GGAL")
    assert any(r["ticker"] == "GGAL" for r in results)


def test_search_by_name():
    results = search_assets("galicia")
    assert any(r["ticker"] == "GGAL" for r in results)


def test_search_no_results():
    results = search_assets("ZZZZNOTEXIST")
    assert results == []


def test_search_max_8_results():
    # Búsqueda muy amplia no debe devolver más de 8
    results = search_assets("A")
    assert len(results) <= 8


def test_popular_tickers_are_known():
    for ticker in POPULAR_TICKERS:
        assert ticker in ASSET_NAMES, f"{ticker} no está en ASSET_NAMES"


def test_market_overview_endpoint(client_no_auth):
    r = client_no_auth.get("/assets/market-overview")
    assert r.status_code == 200
    body = r.json()
    assert "mep" in body
    assert "riesgo_pais" in body
    assert "inflacion" in body
    assert "usd_oficial" in body


def test_search_endpoint(client_no_auth):
    r = client_no_auth.get("/assets/search?q=YPF")
    assert r.status_code == 200
    assert "results" in r.json()
