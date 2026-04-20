"""
Operaciones de base de datos con Supabase (service role key).
"""
import logging
from datetime import datetime, timezone
from config import settings

logger = logging.getLogger(__name__)


def _admin_client():
    """Cliente con service role key para operaciones server-side (bypasea RLS)."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        return None
    from supabase import create_client
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


def ensure_user_profile(user_id: str, email: str) -> None:
    """Crea el perfil del usuario si no existe."""
    client = _admin_client()
    if not client:
        return
    try:
        client.table("users").upsert(
            {"id": user_id, "email": email},
            on_conflict="id",
            ignore_duplicates=True,
        ).execute()
    except Exception as e:
        logger.warning("No se pudo crear perfil de usuario %s: %s", user_id, e)


def get_user_plan(user_id: str) -> str:
    """Devuelve el plan vigente del usuario. Default: 'free'."""
    client = _admin_client()
    if not client:
        return "free"
    try:
        res = (
            client.table("users")
            .select("plan, plan_expires_at")
            .eq("id", user_id)
            .single()
            .execute()
        )
        if not res.data:
            return "free"
        plan = res.data.get("plan", "free")
        expires = res.data.get("plan_expires_at")
        if expires:
            exp_dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
            if exp_dt < datetime.now(timezone.utc):
                return "free"
        return plan
    except Exception as e:
        logger.warning("No se pudo obtener plan de usuario %s: %s", user_id, e)
        return "free"


def count_analyses_this_month(user_id: str) -> int:
    """Cantidad de análisis generados por el usuario en el mes corriente."""
    client = _admin_client()
    if not client:
        return 0
    try:
        now = datetime.now(timezone.utc)
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
        res = (
            client.table("analyses")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .gte("created_at", start_of_month)
            .execute()
        )
        return res.count or 0
    except Exception as e:
        logger.warning("No se pudo contar análisis de usuario %s: %s", user_id, e)
        return 0


def save_analysis(user_id: str, ticker: str, analysis_type: str, score: float, result: dict) -> None:
    """Persiste un análisis en la base de datos (no bloquea si falla)."""
    client = _admin_client()
    if not client:
        return
    try:
        client.table("analyses").insert({
            "user_id": user_id,
            "ticker": ticker,
            "plan": analysis_type,
            "score": score,
            "result_json": result,
        }).execute()
    except Exception as e:
        logger.warning("No se pudo guardar análisis para %s/%s: %s", user_id, ticker, e)


def save_simulation(user_id: str, sim_type: str, config: dict, result: dict) -> None:
    """Persiste una simulación en la base de datos (no bloquea si falla)."""
    client = _admin_client()
    if not client:
        return
    try:
        client.table("simulations").insert({
            "user_id":     user_id,
            "type":        sim_type,
            "config_json": config,
            "result_json": result,
        }).execute()
    except Exception as e:
        logger.warning("No se pudo guardar simulación para %s: %s", user_id, e)


def get_user_simulations(user_id: str, limit: int = 20) -> list:
    """Historial de simulaciones del usuario."""
    client = _admin_client()
    if not client:
        return []
    try:
        res = (
            client.table("simulations")
            .select("id, type, name, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []
    except Exception as e:
        logger.warning("No se pudo obtener simulaciones de usuario %s: %s", user_id, e)
        return []


def get_user_analyses(user_id: str, limit: int = 20) -> list:
    """Historial de análisis del usuario, ordenado por fecha desc."""
    client = _admin_client()
    if not client:
        return []
    try:
        res = (
            client.table("analyses")
            .select("id, ticker, plan, score, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []
    except Exception as e:
        logger.warning("No se pudo obtener historial de usuario %s: %s", user_id, e)
        return []
