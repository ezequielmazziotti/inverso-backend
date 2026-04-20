"""
Tests para el módulo services/database.py.
Mockea el cliente de Supabase para no requerir conexión real.
"""
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta


def _make_client(data=None, count=0):
    """Crea un mock de supabase client con respuestas configurables."""
    mock_res = MagicMock()
    mock_res.data = data
    mock_res.count = count

    chain = MagicMock()
    chain.execute.return_value = mock_res
    chain.eq.return_value = chain
    chain.gte.return_value = chain
    chain.order.return_value = chain
    chain.limit.return_value = chain
    chain.single.return_value = chain
    chain.upsert.return_value = chain
    chain.insert.return_value = chain
    chain.select.return_value = chain

    client = MagicMock()
    client.table.return_value = chain
    return client, chain, mock_res


def test_get_user_plan_free_when_no_service_key():
    from services.database import get_user_plan
    with patch("services.database.settings") as s:
        s.SUPABASE_URL = ""
        s.SUPABASE_SERVICE_KEY = ""
        assert get_user_plan("any-user") == "free"


def test_get_user_plan_returns_plan():
    from services.database import get_user_plan
    client, chain, res = _make_client(data={"plan": "pro", "plan_expires_at": None})
    with patch("services.database._admin_client", return_value=client):
        assert get_user_plan("user-id") == "pro"


def test_get_user_plan_expired_returns_free():
    from services.database import get_user_plan
    expired = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    client, chain, res = _make_client(data={"plan": "basic", "plan_expires_at": expired})
    with patch("services.database._admin_client", return_value=client):
        assert get_user_plan("user-id") == "free"


def test_count_analyses_this_month():
    from services.database import count_analyses_this_month
    client, chain, res = _make_client(count=2)
    with patch("services.database._admin_client", return_value=client):
        assert count_analyses_this_month("user-id") == 2


def test_count_analyses_returns_0_when_no_client():
    from services.database import count_analyses_this_month
    with patch("services.database._admin_client", return_value=None):
        assert count_analyses_this_month("user-id") == 0


def test_get_user_analyses_returns_list():
    from services.database import get_user_analyses
    mock_data = [{"id": "1", "ticker": "GGAL", "score": 7.0}]
    client, chain, res = _make_client(data=mock_data)
    with patch("services.database._admin_client", return_value=client):
        result = get_user_analyses("user-id")
    assert result == mock_data


def test_save_analysis_does_not_raise():
    from services.database import save_analysis
    client, chain, _ = _make_client()
    with patch("services.database._admin_client", return_value=client):
        save_analysis("user-id", "GGAL", "basic", 7.5, {"score": 7.5})


def test_ensure_user_profile_does_not_raise():
    from services.database import ensure_user_profile
    client, chain, _ = _make_client()
    with patch("services.database._admin_client", return_value=client):
        ensure_user_profile("user-id", "test@test.com")
