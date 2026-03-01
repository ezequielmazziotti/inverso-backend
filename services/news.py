"""
Servicio de noticias financieras via NewsAPI.
"""
import httpx
from config import settings


async def get_news(ticker: str, limit: int = 5) -> list:
    """
    Obtiene noticias recientes relacionadas al ticker.
    """
    if not settings.NEWS_API_KEY:
        return _fallback_news(ticker)

    # Construir query de búsqueda
    query_map = {
        "GGAL": "Galicia banco Argentina",
        "YPF":  "YPF Argentina petroleo",
        "PAMP": "Pampa Energia Argentina",
        "AL30": "bonos soberanos Argentina 2030",
        "GD30": "bonos globales Argentina",
        "MEP":  "dolar MEP Argentina",
        "MELI": "MercadoLibre",
    }
    query = query_map.get(ticker.upper(), f"{ticker} Argentina bolsa")

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q":        query,
                    "language": "es",
                    "sortBy":   "publishedAt",
                    "pageSize": limit,
                    "apiKey":   settings.NEWS_API_KEY,
                }
            )
            if r.status_code != 200:
                return _fallback_news(ticker)

            articles = r.json().get("articles", [])
            return [
                {
                    "title":   a.get("title", ""),
                    "source":  a.get("source", {}).get("name", ""),
                    "date":    a.get("publishedAt", "")[:10],
                    "summary": a.get("description", "")[:200] if a.get("description") else "",
                    "url":     a.get("url", ""),
                    "impact":  "neutral",  # Claude lo evaluará en el análisis
                }
                for a in articles if a.get("title")
            ]

    except Exception:
        return _fallback_news(ticker)


def _fallback_news(ticker: str) -> list:
    return [
        {
            "title":   f"Contexto del mercado argentino para {ticker}",
            "source":  "Inverso",
            "date":    "2025-02-21",
            "summary": "No se pudieron cargar noticias en tiempo real. Configurá NEWS_API_KEY en el archivo .env.",
            "impact":  "neutral",
        }
    ]
