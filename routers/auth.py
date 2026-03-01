"""
Router de autenticación via Supabase.
"""
from fastapi import APIRouter, HTTPException
from models.schemas import UserRegister, UserLogin
from config import settings

router = APIRouter()

def get_supabase():
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        return None
    from supabase import create_client
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


@router.post("/register")
async def register(user: UserRegister):
    supabase = get_supabase()
    if not supabase:
        return {"message": "Auth no configurada. Configurá SUPABASE_URL y SUPABASE_KEY en .env", "user": {"email": user.email}}
    try:
        res = supabase.auth.sign_up({"email": user.email, "password": user.password})
        return {"message": "Usuario registrado", "user": {"email": user.email}}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(user: UserLogin):
    supabase = get_supabase()
    if not supabase:
        return {"access_token": "demo-token", "message": "Modo demo - configurá Supabase para auth real"}
    try:
        res = supabase.auth.sign_in_with_password({"email": user.email, "password": user.password})
        return {"access_token": res.session.access_token, "user": {"email": user.email}}
    except Exception as e:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
