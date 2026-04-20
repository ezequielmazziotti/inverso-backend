"""
Router de autenticación via Supabase.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from models.schemas import UserRegister, UserLogin
from dependencies import get_current_user
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_supabase():
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        return None
    from supabase import create_client
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


@router.post("/register")
async def register(user: UserRegister):
    supabase = _get_supabase()
    if not supabase:
        return {"message": "Auth no configurada. Configurá SUPABASE_URL y SUPABASE_KEY en .env", "user": {"email": user.email}}
    try:
        res = supabase.auth.sign_up({"email": user.email, "password": user.password})
        # Crear perfil en tabla users (plan free por defecto)
        if res.user:
            from services.database import ensure_user_profile
            ensure_user_profile(res.user.id, user.email)
        logger.info("Usuario registrado: %s", user.email)
        return {"message": "Usuario registrado", "user": {"email": user.email}}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(user: UserLogin):
    supabase = _get_supabase()
    if not supabase:
        return {"access_token": "demo-token", "message": "Modo demo - configurá Supabase para auth real"}
    try:
        res = supabase.auth.sign_in_with_password({"email": user.email, "password": user.password})
        logger.info("Login exitoso: %s", user.email)
        return {"access_token": res.session.access_token, "user": {"email": user.email}}
    except Exception:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    """Devuelve el perfil y plan del usuario autenticado."""
    return {
        "id":    current_user["id"],
        "email": current_user["email"],
        "plan":  current_user.get("plan", "free"),
    }
