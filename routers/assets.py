from fastapi import APIRouter
from services.market_data import search_assets, get_asset_data, get_mep_price, get_macro_data

router = APIRouter()


@router.get("/search")
async def search(q: str):
    """Búsqueda de activos por ticker o nombre."""
    return {"results": search_assets(q)}


@router.get("/market-overview")
async def market_overview():
    """Datos generales del mercado para el dashboard."""
    macro = await get_macro_data()
    mep   = await get_mep_price()
    return {
        "mep":         mep,
        "riesgo_pais": macro.get("riesgo_pais"),
        "inflacion":   macro.get("inflacion_mensual"),
        "usd_oficial": macro.get("usd_oficial"),
    }


@router.get("/{ticker}")
async def get_asset(ticker: str):
    """Datos básicos de un activo específico."""
    return await get_asset_data(ticker.upper())
@router.get("/debug/iol")
async def debug_iol():
    """Endpoint temporal para debuggear conexión IOL."""
    from config import settings
    from services.iol_client import get_token
    
    username = settings.IOL_USERNAME
    password = settings.IOL_PASSWORD
    
    if not username or not password:
        return {"error": "Credenciales no configuradas", "username": bool(username), "password": bool(password)}
    
    token = await get_token(username, password)
    return {
        "username_set": bool(username),
        "password_set": bool(password),
        "token_obtained": bool(token),
        "token_preview": token[:20] + "..." if token else None
    }
