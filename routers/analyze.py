"""
Router de análisis. Orquesta todos los servicios para producir el análisis final.
"""
from fastapi import APIRouter, HTTPException
from models.schemas import AnalysisRequest
from services.market_data import get_asset_data, get_macro_data, get_mep_price, get_mep_comparison
from services.news import get_news
from services.ai_analysis import run_basic_analysis, run_deep_analysis
import asyncio

router = APIRouter()


@router.post("/basic")
async def analyze_basic(req: AnalysisRequest):
    """
    Análisis básico: score, factores, comparación MEP y resumen.
    Disponible en todos los planes.
    """
    ticker = req.ticker.upper()

    # Obtener todos los datos en paralelo
    asset_data, macro_data, mep_data, mep_comparison = await asyncio.gather(
        get_asset_data(ticker),
        get_macro_data(),
        get_mep_price(),
        get_mep_comparison(ticker),
    )

    if "error" in asset_data and not asset_data.get("price"):
        raise HTTPException(status_code=404, detail=f"No se encontraron datos para el ticker {ticker}")

    # Generar análisis con Claude
    analysis = await run_basic_analysis(asset_data, macro_data, mep_data, mep_comparison)

    return {
        **asset_data,
        **analysis,
    }


@router.post("/deep")
async def analyze_deep(req: AnalysisRequest):
    """
    Análisis profundo: todo lo básico + proyecciones, pares, noticias y análisis técnico.
    Solo disponible en plan Pro.
    """
    ticker = req.ticker.upper()

    # Obtener todos los datos en paralelo (incluyendo noticias)
    asset_data, macro_data, mep_data, mep_comparison, news = await asyncio.gather(
        get_asset_data(ticker),
        get_macro_data(),
        get_mep_price(),
        get_mep_comparison(ticker),
        get_news(ticker, limit=5),
    )

    if "error" in asset_data and not asset_data.get("price"):
        raise HTTPException(status_code=404, detail=f"No se encontraron datos para el ticker {ticker}")

    # Generar análisis profundo con Claude
    analysis = await run_deep_analysis(asset_data, macro_data, mep_data, mep_comparison, news)

    return {
        **asset_data,
        **analysis,
    }
