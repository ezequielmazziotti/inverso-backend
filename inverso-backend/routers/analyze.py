"""
Router de análisis. Orquesta todos los servicios para producir el análisis final.
"""
import logging
import asyncio
from fastapi import APIRouter, HTTPException, Depends
from models.schemas import AnalysisRequest
from services.market_data import get_asset_data, get_macro_data, get_mep_price, get_mep_comparison
from services.news import get_news
from services.ai_analysis import run_basic_analysis, run_deep_analysis
from services.database import count_analyses_this_month, save_analysis, get_user_analyses
from dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

FREE_MONTHLY_LIMIT = 3


@router.post("/basic")
async def analyze_basic(req: AnalysisRequest, current_user: dict = Depends(get_current_user)):
    """
    Análisis básico: score, factores, comparación MEP y resumen.
    Plan Free: hasta 3 por mes. Basic/Pro: ilimitado.
    """
    user_id = current_user["id"]
    plan = current_user.get("plan", "free")
    ticker = req.ticker.upper()

    if plan == "free" and user_id != "demo":
        used = count_analyses_this_month(user_id)
        if used >= FREE_MONTHLY_LIMIT:
            raise HTTPException(
                status_code=429,
                detail=f"Límite de {FREE_MONTHLY_LIMIT} análisis/mes alcanzado en el plan Free. Mejorá tu plan para continuar.",
            )

    asset_data, macro_data, mep_data, mep_comparison = await asyncio.gather(
        get_asset_data(ticker),
        get_macro_data(),
        get_mep_price(),
        get_mep_comparison(ticker),
    )

    if "error" in asset_data and not asset_data.get("price"):
        raise HTTPException(status_code=404, detail=f"No se encontraron datos para el ticker {ticker}")

    analysis = await run_basic_analysis(asset_data, macro_data, mep_data, mep_comparison)
    result = {**asset_data, **analysis}

    if user_id != "demo":
        save_analysis(user_id, ticker, "basic", analysis.get("score", 0), result)

    logger.info("Análisis básico completado — ticker=%s user=%s", ticker, current_user["email"])
    return result


@router.post("/deep")
async def analyze_deep(req: AnalysisRequest, current_user: dict = Depends(get_current_user)):
    """
    Análisis profundo: todo lo básico + proyecciones, pares, noticias y análisis técnico.
    Requiere plan Basic o Pro.
    """
    plan = current_user.get("plan", "free")
    if plan == "free":
        raise HTTPException(
            status_code=403,
            detail="El análisis profundo requiere plan Basic o Pro.",
        )

    ticker = req.ticker.upper()
    user_id = current_user["id"]

    asset_data, macro_data, mep_data, mep_comparison, news = await asyncio.gather(
        get_asset_data(ticker),
        get_macro_data(),
        get_mep_price(),
        get_mep_comparison(ticker),
        get_news(ticker, limit=5),
    )

    if "error" in asset_data and not asset_data.get("price"):
        raise HTTPException(status_code=404, detail=f"No se encontraron datos para el ticker {ticker}")

    analysis = await run_deep_analysis(asset_data, macro_data, mep_data, mep_comparison, news)
    result = {**asset_data, **analysis}

    if user_id != "demo":
        save_analysis(user_id, ticker, "deep", analysis.get("score", 0), result)

    logger.info("Análisis profundo completado — ticker=%s user=%s", ticker, current_user["email"])
    return result


@router.get("/history")
async def analyze_history(current_user: dict = Depends(get_current_user)):
    """
    Historial de análisis del usuario autenticado (últimos 20).
    """
    analyses = get_user_analyses(current_user["id"])
    return {"analyses": analyses}
