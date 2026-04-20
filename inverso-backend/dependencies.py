"""
Dependencias de FastAPI reutilizables.
"""
import logging
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import settings

logger = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    if not credentials:
        raise HTTPException(status_code=401, detail="Token de autenticación requerido")

    token = credentials.credentials

    # Modo demo: permite probar sin Supabase configurado
    if token == "demo-token":
        return {"id": "demo", "email": "demo@inverso.app", "plan": "free"}

    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise HTTPException(status_code=503, detail="Autenticación no configurada en el servidor")

    try:
        from supabase import create_client
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        result = supabase.auth.get_user(token)
        user = result.user
        if not user:
            raise HTTPException(status_code=401, detail="Token inválido o expirado")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    # Asegurar perfil en DB y obtener plan vigente
    from services.database import ensure_user_profile, get_user_plan
    ensure_user_profile(user.id, user.email)
    plan = get_user_plan(user.id)

    logger.info("Auth OK — usuario %s plan=%s", user.email, plan)
    return {"id": user.id, "email": user.email, "plan": plan}
