"""
Servicio de análisis con Claude (Anthropic).
"""
import json
import re
from anthropic import AsyncAnthropic
from config import settings

client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

_SYSTEM = (
    "Sos un analista financiero especializado en el mercado argentino. "
    "Respondés ÚNICAMENTE con JSON válido, sin texto adicional ni bloques de código."
)


def _extract_json(text: str) -> str:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group() if match else text


async def run_basic_analysis(asset_data: dict, macro_data: dict, mep_data: dict, mep_comparison: dict) -> dict:
    prompt = _build_basic_prompt(asset_data, macro_data, mep_data, mep_comparison)
    try:
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            system=_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        return json.loads(_extract_json(response.content[0].text))
    except Exception:
        return _fallback_basic_analysis(asset_data)


async def run_deep_analysis(asset_data: dict, macro_data: dict, mep_data: dict, mep_comparison: dict, news: list) -> dict:
    prompt = _build_deep_prompt(asset_data, macro_data, mep_data, mep_comparison, news)
    try:
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=3000,
            system=_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        return json.loads(_extract_json(response.content[0].text))
    except Exception:
        return _fallback_deep_analysis(asset_data)


def _build_basic_prompt(asset_data, macro_data, mep_data, mep_comparison):
    history_summary = ""
    if asset_data.get("history"):
        prices = [h["price"] for h in asset_data["history"]]
        if prices:
            history_summary = f"Mínimo 12m: {min(prices):.2f} | Máximo 12m: {max(prices):.2f} | Actual: {prices[-1]:.2f}"

    return f"""Analizá este activo del mercado argentino y respondé ÚNICAMENTE con el siguiente JSON:

## DATOS DEL ACTIVO
- Ticker: {asset_data['ticker']}
- Nombre: {asset_data['name']}
- Precio actual: {asset_data['price']} ARS
- Variación hoy: {asset_data['change_pct']}%
- {history_summary}

## CONTEXTO MACRO ARGENTINO
- Dólar oficial: {macro_data.get('usd_oficial', 'N/D')} ARS
- Dólar MEP: {mep_data.get('price', 'N/D')} ARS
- Tasa política monetaria: {macro_data.get('tasa_politica', 'N/D')}%
- Reservas: USD {macro_data.get('reservas_mm', 'N/D')} millones
- Inflación mensual: {macro_data.get('inflacion_mensual', 'N/D')}%
- Riesgo país: {macro_data.get('riesgo_pais', 'N/D')} puntos

## COMPARACIÓN CON DÓLAR MEP
- Activo 30d: {mep_comparison.get('days_30', 0)}% | MEP 30d: {mep_comparison.get('mep_30', 0)}%
- Activo 90d: {mep_comparison.get('days_90', 0)}% | MEP 90d: {mep_comparison.get('mep_90', 0)}%
- Activo 365d: {mep_comparison.get('days_365', 0)}% | MEP 365d: {mep_comparison.get('mep_365', 0)}%

## JSON REQUERIDO
{{
  "score": <número del 1.0 al 10.0>,
  "score_description": "<descripción breve en 10 palabras>",
  "factors": [
    {{"title": "<nombre>", "description": "<1-2 oraciones>", "type": "<positive|negative|neutral>"}}
  ],
  "mep_comparison": {{
    "days_30": {mep_comparison.get('days_30', 0)},
    "days_90": {mep_comparison.get('days_90', 0)},
    "days_365": {mep_comparison.get('days_365', 0)},
    "mep_30": {mep_comparison.get('mep_30', 0)},
    "mep_90": {mep_comparison.get('mep_90', 0)},
    "mep_365": {mep_comparison.get('mep_365', 0)}
  }},
  "summary": "<4-5 oraciones en lenguaje simple para el inversor retail argentino>"
}}

Generá exactamente 5 factores. Sé específico con el contexto argentino."""


def _build_deep_prompt(asset_data, macro_data, mep_data, mep_comparison, news):
    basic = _build_basic_prompt(asset_data, macro_data, mep_data, mep_comparison)
    news_text = "\n".join([f"- {n['title']} ({n['source']}): {n['summary']}" for n in news[:5]])
    ticker = asset_data['ticker']
    peers_map = {
        "GGAL": [("BMA", "Banco Macro"), ("SUPV", "Supervielle")],
        "YPF":  [("PAMP", "Pampa Energía"), ("VIST", "Vista Energy")],
        "AL30": [("GD30", "Bono Global 2030"), ("AE38", "Bono 2038")],
        "PAMP": [("YPF", "YPF S.A."), ("VIST", "Vista Energy")],
    }
    peers = peers_map.get(ticker.upper(), [("GGAL", "Galicia"), ("YPF", "YPF")])

    return f"""{basic}

Además incluí en el JSON estas secciones adicionales:

  "projections": {{
    "months_3":  {{"optimistic": "<+X%>", "neutral": "<+X%>", "pessimistic": "<-X%>"}},
    "months_6":  {{"optimistic": "<+X%>", "neutral": "<+X%>", "pessimistic": "<-X%>"}},
    "months_12": {{"optimistic": "<+X%>", "neutral": "<+X%>", "pessimistic": "<-X%>"}}
  }},
  "peers": [
    {{"ticker": "{peers[0][0]}", "name": "{peers[0][1]}", "performance_90d": <número>}},
    {{"ticker": "{peers[1][0]}", "name": "{peers[1][1]}", "performance_90d": <número>}}
  ],
  "news": [
    {{"title": "<título>", "source": "<fuente>", "date": "<YYYY-MM-DD>", "summary": "<impacto en 1-2 oraciones>", "impact": "<positive|negative|neutral>"}}
  ],
  "technical_summary": "<tendencia, soportes, resistencias en 3-4 oraciones>"

## NOTICIAS PARA ANALIZAR
{news_text if news_text else "No hay noticias disponibles."}"""


def _fallback_basic_analysis(asset_data):
    return {
        "score": 5.0,
        "score_description": "API no configurada",
        "factors": [{"title": "Configuración pendiente", "description": "Completá ANTHROPIC_API_KEY en .env", "type": "neutral"}],
        "mep_comparison": {"days_30": 0, "days_90": 0, "days_365": 0, "mep_30": 0, "mep_90": 0, "mep_365": 0},
        "summary": f"Para obtener el análisis de {asset_data['ticker']}, configurá tu clave de Anthropic en .env",
    }


def _fallback_deep_analysis(asset_data):
    base = _fallback_basic_analysis(asset_data)
    base.update({
        "projections": {
            "months_3":  {"optimistic": "N/D", "neutral": "N/D", "pessimistic": "N/D"},
            "months_6":  {"optimistic": "N/D", "neutral": "N/D", "pessimistic": "N/D"},
            "months_12": {"optimistic": "N/D", "neutral": "N/D", "pessimistic": "N/D"},
        },
        "peers": [], "news": [],
        "technical_summary": "Configurá ANTHROPIC_API_KEY para obtener análisis técnico.",
    })
    return base
