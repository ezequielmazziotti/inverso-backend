"""
Cliente para la API de IOL (Invertir Online).
Autenticación OAuth2 + cotizaciones en tiempo real del mercado argentino.
"""
import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Optional

IOL_BASE = "https://api.invertironline.com"

# Token cache global (se renueva automáticamente)
_token_cache = {"access_token": None, "expires_at": None}


async def get_token(username: str, password: str) -> Optional[str]:
    """Obtiene o renueva el token de acceso."""
    now = datetime.now()
    
    # Si el token todavía es válido, lo devuelve
    if _token_cache["access_token"] and _token_cache["expires_at"] and now < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                f"{IOL_BASE}/token",
                data={
                    "username": username,
                    "password": password,
                    "grant_type": "password",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if r.status_code != 200:
                return None
            data = r.json()
            _token_cache["access_token"] = data.get("access_token")
            expires_in = int(data.get("expires_in", 3600))
            _token_cache["expires_at"] = now + timedelta(seconds=expires_in - 60)
            return _token_cache["access_token"]
    except Exception:
        return None


async def get_cotizacion(ticker: str, mercado: str, token: str) -> Optional[dict]:
    """Obtiene cotización actual de un activo."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{IOL_BASE}/api/v2/{mercado}/Titulos/{ticker}/cotizacion",
                headers={"Authorization": f"Bearer {token}"},
            )
            if r.status_code != 200:
                return None
            return r.json()
    except Exception:
        return None


async def get_historico(ticker: str, mercado: str, token: str, dias: int = 365) -> Optional[list]:
    """Obtiene historial de cotizaciones."""
    fecha_desde = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")
    fecha_hasta = datetime.now().strftime("%Y-%m-%d")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{IOL_BASE}/api/v2/{mercado}/Titulos/{ticker}/cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/ajustada",
                headers={"Authorization": f"Bearer {token}"},
            )
            if r.status_code != 200:
                return None
            return r.json()
    except Exception:
        return None
