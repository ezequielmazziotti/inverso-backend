import asyncio
from fastapi import APIRouter
from services.market_data import search_assets, get_asset_data, get_mep_price, get_macro_data, POPULAR_TICKERS

router = APIRouter()


@router.get("/search")
async def search(q: str):
    """Búsqueda de activos por ticker o nombre."""
    return {"results": search_assets(q)}


@router.get("/popular")
async def popular_assets():
    """Los activos más consultados con precio y variación del día."""
    assets = await asyncio.gather(*[get_asset_data(t) for t in POPULAR_TICKERS])
    return {
        "assets": [
            {
                "ticker":     a["ticker"],
                "name":       a["name"],
                "price":      a["price"],
                "change_pct": a["change_pct"],
            }
            for a in assets
        ]
    }


@router.get("/market-overview")
async def market_overview():
    """Datos generales del mercado para el dashboard."""
    macro, mep = await asyncio.gather(get_macro_data(), get_mep_price())
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
