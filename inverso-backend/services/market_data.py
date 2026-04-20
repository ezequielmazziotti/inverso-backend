"""
Servicio de datos de mercado.
Obtiene precios históricos (yfinance), datos macro del BCRA y tipo de cambio.
"""
import time
import logging
import yfinance as yf
import httpx
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ── Caché TTL ─────────────────────────────────────────────────────────────────
_cache: dict[str, tuple] = {}  # key -> (value, expires_at_monotonic)


def _cache_get(key: str):
    entry = _cache.get(key)
    if entry and entry[1] > time.monotonic():
        return entry[0]
    return None


def _cache_set(key: str, value, ttl: int) -> None:
    _cache[key] = (value, time.monotonic() + ttl)


# ── Mapeos ────────────────────────────────────────────────────────────────────
TICKER_MAP = {
    "GGAL": "GGAL.BA",
    "YPF":  "YPF.BA",
    "PAMP": "PAMP.BA",
    "BMA":  "BMA.BA",
    "SUPV": "SUPV.BA",
    "VIST": "VIST.BA",
    "MELI": "MELI",
    "AMZN": "AMZN",
    "AAPL": "AAPL",
    "TSLA": "TSLA",
    "AL30": "AL30.BA",
    "GD30": "GD30.BA",
    "AE38": "AE38.BA",
    "AL35": "AL35.BA",
}

ASSET_NAMES = {
    "GGAL": "Grupo Financiero Galicia · Merval",
    "YPF":  "YPF S.A. · Merval",
    "PAMP": "Pampa Energía · Merval",
    "BMA":  "Banco Macro · Merval",
    "SUPV": "Supervielle · Merval",
    "VIST": "Vista Energy · Merval",
    "MELI": "MercadoLibre · CEDEAR",
    "AMZN": "Amazon · CEDEAR",
    "AAPL": "Apple · CEDEAR",
    "TSLA": "Tesla · CEDEAR",
    "AL30": "Bono Soberano Argentina 2030",
    "GD30": "Bono Global Argentina 2030",
    "AE38": "Bono Soberano Argentina 2038",
    "AL35": "Bono Soberano Argentina 2035",
    "MEP":  "Dólar MEP · Bursátil",
}

POPULAR_TICKERS = ["GGAL", "YPF", "PAMP", "BMA", "MELI", "AL30", "GD30"]

BCRA_BASE = "https://api.bcra.gob.ar/estadisticas/v3.0"


async def get_asset_data(ticker: str) -> dict:
    """Precio actual, variación del día e historial de 365 días. Cache: 5 min."""
    key = f"asset:{ticker.upper()}"
    cached = _cache_get(key)
    if cached:
        return cached

    yf_ticker = TICKER_MAP.get(ticker.upper(), ticker + ".BA")

    try:
        stock = yf.Ticker(yf_ticker)
        hist = stock.history(period="1y")

        if hist.empty:
            raise ValueError(f"No se encontraron datos para {ticker}")

        current_price = float(hist["Close"].iloc[-1])
        prev_price    = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current_price
        change_pct    = ((current_price - prev_price) / prev_price) * 100

        history = [
            {"date": str(idx.date()), "price": round(float(row["Close"]), 2)}
            for idx, row in hist.iterrows()
        ][::5]

        result = {
            "ticker":     ticker.upper(),
            "name":       ASSET_NAMES.get(ticker.upper(), ticker.upper()),
            "price":      round(current_price, 2),
            "change_pct": round(change_pct, 2),
            "history":    history,
            "currency":   "ARS",
        }
        _cache_set(key, result, ttl=300)  # 5 minutos
        return result

    except Exception as e:
        logger.warning("yfinance falló para %s: %s", ticker, e)
        return _fallback_data(ticker, str(e))


async def get_macro_data() -> dict:
    """Datos macroeconómicos del BCRA. Cache: 20 min."""
    cached = _cache_get("macro")
    if cached:
        return cached

    macro = {
        "usd_oficial":      None,
        "tasa_politica":    None,
        "reservas_mm":      None,
        "inflacion_mensual": None,
        "riesgo_pais":      None,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        for var_id, field, fallback in [
            (4,  "usd_oficial",       1050.0),
            (6,  "tasa_politica",       35.0),
            (1,  "reservas_mm",       28500.0),
            (27, "inflacion_mensual",    2.4),
        ]:
            try:
                r = await client.get(f"{BCRA_BASE}/datosvariable/{var_id}/2024-01-01/{_today()}")
                data = r.json().get("results", []) if r.status_code == 200 else []
                macro[field] = data[-1]["valor"] if data else fallback
            except Exception:
                macro[field] = fallback

    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get("https://mercados.ambito.com//riesgopais/info")
            macro["riesgo_pais"] = r.json().get("valor", 612) if r.status_code == 200 else 612
    except Exception:
        macro["riesgo_pais"] = 612

    _cache_set("macro", macro, ttl=1200)  # 20 minutos
    return macro


async def get_mep_price() -> dict:
    """Precio del dólar MEP. Cache: 5 min."""
    cached = _cache_get("mep_price")
    if cached:
        return cached

    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get("https://mercados.ambito.com/dolar/mep/info")
            if r.status_code == 200:
                data = r.json()
                result = {
                    "price":      float(data.get("venta", 1247)),
                    "change_pct": float(data.get("variacion", 0.3)),
                }
                _cache_set("mep_price", result, ttl=300)
                return result
    except Exception:
        pass

    return {"price": 1247.0, "change_pct": 0.3}


async def get_mep_comparison(ticker: str) -> dict:
    """Rendimiento del activo vs dólar MEP en 30/90/365 días. Cache: 15 min."""
    key = f"mep_cmp:{ticker.upper()}"
    cached = _cache_get(key)
    if cached:
        return cached

    yf_ticker  = TICKER_MAP.get(ticker.upper(), ticker + ".BA")
    mep_ticker = "AL30D.BA"

    try:
        asset = yf.Ticker(yf_ticker)
        mep   = yf.Ticker(mep_ticker)

        asset_hist = asset.history(period="1y")["Close"]
        mep_hist   = mep.history(period="1y")["Close"]

        results = {}
        for key_name, days in [("days_30", 30), ("days_90", 90), ("days_365", 365)]:
            cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            a_slice = asset_hist[asset_hist.index >= cutoff]
            m_slice = mep_hist[mep_hist.index >= cutoff]

            a_then = float(a_slice.iloc[0]) if not a_slice.empty else None
            a_now  = float(asset_hist.iloc[-1])
            m_then = float(m_slice.iloc[0]) if not m_slice.empty else None
            m_now  = float(mep_hist.iloc[-1])

            results[key_name] = round(((a_now - a_then) / a_then * 100), 1) if a_then else 0
            results[key_name.replace("days_", "mep_")] = round(((m_now - m_then) / m_then * 100), 1) if m_then else 0

        _cache_set(f"mep_cmp:{ticker.upper()}", results, ttl=900)  # 15 minutos
        return results

    except Exception as e:
        logger.warning("MEP comparison falló para %s: %s", ticker, e)
        return {
            "days_30": 18.4, "days_90": 41.2, "days_365": 182.6,
            "mep_30":   1.2,  "mep_90":   3.8,  "mep_365":   14.1,
        }


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _fallback_data(ticker: str, error: str) -> dict:
    return {
        "ticker":     ticker.upper(),
        "name":       ASSET_NAMES.get(ticker.upper(), ticker.upper()),
        "price":      1000.0,
        "change_pct": 0.0,
        "history":    [],
        "currency":   "ARS",
        "error":      error,
    }


def search_assets(query: str) -> list:
    """Búsqueda de activos por ticker o nombre."""
    q = query.upper()
    return [
        {"ticker": ticker, "name": name}
        for ticker, name in ASSET_NAMES.items()
        if q in ticker or q in name.upper()
    ][:8]
