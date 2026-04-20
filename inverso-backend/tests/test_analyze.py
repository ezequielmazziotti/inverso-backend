"""
Tests para los endpoints de análisis: rate limiting y verificación de plan.
"""
from unittest.mock import AsyncMock, patch


_MOCK_ASSET = {
    "ticker": "GGAL", "name": "Grupo Financiero Galicia · Merval",
    "price": 5000.0, "change_pct": 1.5, "history": [], "currency": "ARS",
}
_MOCK_MACRO   = {"usd_oficial": 1050, "tasa_politica": 35, "reservas_mm": 28500, "inflacion_mensual": 2.4, "riesgo_pais": 612}
_MOCK_MEP     = {"price": 1247.0, "change_pct": 0.3}
_MOCK_MEP_CMP = {"days_30": 10, "days_90": 30, "days_365": 150, "mep_30": 1, "mep_90": 3, "mep_365": 12}
_MOCK_ANALYSIS = {
    "score": 7.5, "score_description": "Buena oportunidad", "factors": [],
    "mep_comparison": _MOCK_MEP_CMP, "summary": "Buen activo.",
}
_MOCK_NEWS = []


def _patch_services(mock_analysis=_MOCK_ANALYSIS):
    return [
        patch("routers.analyze.get_asset_data",    new=AsyncMock(return_value=_MOCK_ASSET)),
        patch("routers.analyze.get_macro_data",    new=AsyncMock(return_value=_MOCK_MACRO)),
        patch("routers.analyze.get_mep_price",     new=AsyncMock(return_value=_MOCK_MEP)),
        patch("routers.analyze.get_mep_comparison",new=AsyncMock(return_value=_MOCK_MEP_CMP)),
        patch("routers.analyze.run_basic_analysis",new=AsyncMock(return_value=mock_analysis)),
        patch("routers.analyze.save_analysis"),
        patch("routers.analyze.count_analyses_this_month", return_value=0),
    ]


# ── Plan checks ───────────────────────────────────────────────────────────────

def test_deep_blocked_for_free_plan(client_free):
    r = client_free.post("/analyze/deep", json={"ticker": "GGAL"})
    assert r.status_code == 403
    assert "Basic o Pro" in r.json()["detail"]


def test_deep_allowed_for_basic_plan(client_basic):
    deep_analysis = {**_MOCK_ANALYSIS, "projections": {}, "peers": [], "news": [], "technical_summary": ""}
    patches = [
        patch("routers.analyze.get_asset_data",    new=AsyncMock(return_value=_MOCK_ASSET)),
        patch("routers.analyze.get_macro_data",    new=AsyncMock(return_value=_MOCK_MACRO)),
        patch("routers.analyze.get_mep_price",     new=AsyncMock(return_value=_MOCK_MEP)),
        patch("routers.analyze.get_mep_comparison",new=AsyncMock(return_value=_MOCK_MEP_CMP)),
        patch("routers.analyze.get_news",          new=AsyncMock(return_value=_MOCK_NEWS)),
        patch("routers.analyze.run_deep_analysis", new=AsyncMock(return_value=deep_analysis)),
        patch("routers.analyze.save_analysis"),
    ]
    with __builtins__["__import__"]("contextlib").ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)
        r = client_basic.post("/analyze/deep", json={"ticker": "GGAL"})
    assert r.status_code == 200


def test_deep_allowed_for_pro_plan(client_pro):
    deep_analysis = {**_MOCK_ANALYSIS, "projections": {}, "peers": [], "news": [], "technical_summary": ""}
    patches = [
        patch("routers.analyze.get_asset_data",    new=AsyncMock(return_value=_MOCK_ASSET)),
        patch("routers.analyze.get_macro_data",    new=AsyncMock(return_value=_MOCK_MACRO)),
        patch("routers.analyze.get_mep_price",     new=AsyncMock(return_value=_MOCK_MEP)),
        patch("routers.analyze.get_mep_comparison",new=AsyncMock(return_value=_MOCK_MEP_CMP)),
        patch("routers.analyze.get_news",          new=AsyncMock(return_value=_MOCK_NEWS)),
        patch("routers.analyze.run_deep_analysis", new=AsyncMock(return_value=deep_analysis)),
        patch("routers.analyze.save_analysis"),
    ]
    with __builtins__["__import__"]("contextlib").ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)
        r = client_pro.post("/analyze/deep", json={"ticker": "GGAL"})
    assert r.status_code == 200


# ── Rate limiting ─────────────────────────────────────────────────────────────

def test_free_plan_blocked_at_limit(client_free):
    with patch("routers.analyze.count_analyses_this_month", return_value=3), \
         patch("routers.analyze.get_asset_data", new=AsyncMock(return_value=_MOCK_ASSET)):
        r = client_free.post("/analyze/basic", json={"ticker": "GGAL"})
    assert r.status_code == 429
    assert "Límite" in r.json()["detail"]


def test_free_plan_allowed_under_limit(client_free):
    with patch("routers.analyze.count_analyses_this_month", return_value=2), \
         patch("routers.analyze.get_asset_data",    new=AsyncMock(return_value=_MOCK_ASSET)), \
         patch("routers.analyze.get_macro_data",    new=AsyncMock(return_value=_MOCK_MACRO)), \
         patch("routers.analyze.get_mep_price",     new=AsyncMock(return_value=_MOCK_MEP)), \
         patch("routers.analyze.get_mep_comparison",new=AsyncMock(return_value=_MOCK_MEP_CMP)), \
         patch("routers.analyze.run_basic_analysis",new=AsyncMock(return_value=_MOCK_ANALYSIS)), \
         patch("routers.analyze.save_analysis"):
        r = client_free.post("/analyze/basic", json={"ticker": "GGAL"})
    assert r.status_code == 200


def test_basic_plan_no_rate_limit(client_basic):
    """Plan Basic no tiene límite mensual en análisis básico."""
    with patch("routers.analyze.get_asset_data",    new=AsyncMock(return_value=_MOCK_ASSET)), \
         patch("routers.analyze.get_macro_data",    new=AsyncMock(return_value=_MOCK_MACRO)), \
         patch("routers.analyze.get_mep_price",     new=AsyncMock(return_value=_MOCK_MEP)), \
         patch("routers.analyze.get_mep_comparison",new=AsyncMock(return_value=_MOCK_MEP_CMP)), \
         patch("routers.analyze.run_basic_analysis",new=AsyncMock(return_value=_MOCK_ANALYSIS)), \
         patch("routers.analyze.save_analysis"):
        r = client_basic.post("/analyze/basic", json={"ticker": "GGAL"})
    assert r.status_code == 200


# ── Historial ─────────────────────────────────────────────────────────────────

def test_history_returns_list(client_free):
    mock_history = [
        {"id": "abc", "ticker": "GGAL", "plan": "basic", "score": 7.5, "created_at": "2025-04-01T10:00:00"}
    ]
    with patch("routers.analyze.get_user_analyses", return_value=mock_history):
        r = client_free.get("/analyze/history")
    assert r.status_code == 200
    assert r.json()["analyses"] == mock_history
