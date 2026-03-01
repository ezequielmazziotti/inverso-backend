"""
Servicio de análisis con OpenAI GPT-4o mini.
Análisis profesional de nivel institucional para el mercado argentino.
"""
import json
from openai import OpenAI
from config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)


async def run_basic_analysis(asset_data: dict, macro_data: dict, mep_data: dict, mep_comparison: dict) -> dict:
    prompt = _build_basic_prompt(asset_data, macro_data, mep_data, mep_comparison)
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=2500,
            temperature=0.3,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
        return json.loads(response.choices[0].message.content)
    except Exception:
        return _fallback_basic_analysis(asset_data)


async def run_deep_analysis(asset_data: dict, macro_data: dict, mep_data: dict, mep_comparison: dict, news: list) -> dict:
    prompt = _build_deep_prompt(asset_data, macro_data, mep_data, mep_comparison, news)
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=4000,
            temperature=0.3,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
        return json.loads(response.choices[0].message.content)
    except Exception:
        return _fallback_deep_analysis(asset_data)


SYSTEM_PROMPT = """Sos un analista financiero senior especializado en el mercado de capitales argentino, con más de 15 años de experiencia en research de renta variable, renta fija y activos alternativos. Trabajaste en fondos de inversión de primer nivel y tenés un profundo conocimiento del contexto macroeconómico argentino.

Tu análisis debe ser:
- ESPECÍFICO: mencioná el ticker, precios concretos, porcentajes reales, fechas
- PROFESIONAL: usá terminología financiera correcta (P/E, EV/EBITDA, spread, duration, beta, etc.)
- CONTEXTUALIZADO: conectá siempre con el contexto macro argentino actual (tipo de cambio, cepo, riesgo país, inflación, BCRA)
- HONESTO: si hay riesgos reales, mencionarlos sin suavizarlos
- ACCIONABLE: el análisis debe ayudar a tomar una decisión concreta de inversión

Respondés SIEMPRE en JSON válido, sin texto adicional fuera del JSON."""


def _build_basic_prompt(asset_data, macro_data, mep_data, mep_comparison):
    ticker   = asset_data['ticker']
    precio   = asset_data['price']
    variacion = asset_data['change_pct']
    nombre   = asset_data['name']
    history  = asset_data.get('history', [])

    # Calcular métricas técnicas del historial
    prices = [h['price'] for h in history if h.get('price', 0) > 0]
    tecnico = ""
    if len(prices) >= 10:
        max_12m  = max(prices)
        min_12m  = min(prices)
        avg_price = sum(prices) / len(prices)
        dist_max  = round((precio - max_12m) / max_12m * 100, 1)
        dist_min  = round((precio - min_12m) / min_12m * 100, 1)
        vs_avg    = round((precio - avg_price) / avg_price * 100, 1)
        # SMA 20 y 50 aproximados
        sma20 = round(sum(prices[-4:]) / min(4, len(prices[-4:])), 2) if len(prices) >= 4 else precio
        sma50 = round(sum(prices[-10:]) / min(10, len(prices[-10:])), 2) if len(prices) >= 10 else precio
        tendencia = "alcista" if prices[-1] > prices[-5] > prices[-10] else "bajista" if prices[-1] < prices[-5] < prices[-10] else "lateral"
        tecnico = f"""
## ANÁLISIS TÉCNICO (datos reales)
- Precio actual: ${precio:,.2f} ARS
- Máximo 12 meses: ${max_12m:,.2f} ({dist_max:+.1f}% vs máximo)
- Mínimo 12 meses: ${min_12m:,.2f} ({dist_min:+.1f}% vs mínimo)
- Precio promedio 12m: ${avg_price:,.2f} ({vs_avg:+.1f}% vs promedio)
- SMA20 aprox: ${sma20:,.2f} | SMA50 aprox: ${sma50:,.2f}
- Tendencia general: {tendencia}
- Posición en rango 12m: {'zona alta (>70%)' if dist_min > (max_12m - min_12m) * 0.7 / min_12m * 100 else 'zona baja (<30%)' if dist_min < (max_12m - min_12m) * 0.3 / min_12m * 100 else 'zona media (30-70%)'}"""

    return f"""Realizá un análisis profesional completo del siguiente activo argentino:

## ACTIVO
- Ticker: {ticker}
- Nombre: {nombre}
- Precio actual: ${precio:,.2f} ARS
- Variación diaria: {variacion:+.2f}%
{tecnico}

## CONTEXTO MACROECONÓMICO ARGENTINO
- Dólar oficial (BNA): ${macro_data.get('usd_oficial', 'N/D'):,.0f} ARS
- Dólar MEP: ${mep_data.get('price', 'N/D'):,.0f} ARS ({mep_data.get('change_pct', 0):+.1f}% hoy)
- Tasa política monetaria: {macro_data.get('tasa_politica', 'N/D')}% anual
- Reservas internacionales: USD {macro_data.get('reservas_mm', 'N/D'):,} millones
- Inflación mensual: {macro_data.get('inflacion_mensual', 'N/D')}%
- Riesgo país (EMBI+): {macro_data.get('riesgo_pais', 'N/D')} puntos básicos

## PERFORMANCE vs DÓLAR MEP
| Período | {ticker} | Dólar MEP | Diferencia |
|---------|----------|-----------|------------|
| 30 días | {mep_comparison.get('days_30', 0):+.1f}% | {mep_comparison.get('mep_30', 0):+.1f}% | {mep_comparison.get('days_30', 0) - mep_comparison.get('mep_30', 0):+.1f}% |
| 90 días | {mep_comparison.get('days_90', 0):+.1f}% | {mep_comparison.get('mep_90', 0):+.1f}% | {mep_comparison.get('days_90', 0) - mep_comparison.get('mep_90', 0):+.1f}% |
| 365 días | {mep_comparison.get('days_365', 0):+.1f}% | {mep_comparison.get('mep_365', 0):+.1f}% | {mep_comparison.get('days_365', 0) - mep_comparison.get('mep_365', 0):+.1f}% |

## INSTRUCCIONES
Generá exactamente este JSON con análisis ESPECÍFICO y PROFESIONAL para {ticker}:

{{
  "score": <número preciso del 1.0 al 10.0 basado en datos reales>,
  "score_description": "<descripción específica en 8-10 palabras mencionando el ticker>",
  "factors": [
    {{
      "title": "<nombre concreto del factor, ej: 'Momentum bajista en zona de soporte'>",
      "description": "<2-3 oraciones técnicas con datos concretos, precios, porcentajes y contexto específico del activo y Argentina>",
      "type": "<positive|negative|neutral>"
    }}
  ],
  "mep_comparison": {{
    "days_30": {mep_comparison.get('days_30', 0)},
    "days_90": {mep_comparison.get('days_90', 0)},
    "days_365": {mep_comparison.get('days_365', 0)},
    "mep_30": {mep_comparison.get('mep_30', 0)},
    "mep_90": {mep_comparison.get('mep_90', 0)},
    "mep_365": {mep_comparison.get('mep_365', 0)}
  }},
  "summary": "<5-6 oraciones profesionales con: (1) situación técnica actual con precios concretos, (2) drivers fundamentales específicos del negocio/sector, (3) impacto del contexto macro argentino en este activo, (4) niveles clave de soporte/resistencia, (5) conclusión con sesgo direccional y nivel de convicción>"
}}

Generá exactamente 5 factores. Sé específico con {ticker}: mencioná su sector, competidores, regulación, exposición al tipo de cambio, y cómo le afecta el riesgo país {macro_data.get('riesgo_pais', '')} puntos."""


def _build_deep_prompt(asset_data, macro_data, mep_data, mep_comparison, news):
    ticker = asset_data['ticker']
    precio = asset_data['price']
    nombre = asset_data['name']

    news_text = ""
    if news:
        news_text = "\n".join([
            f"- [{n.get('date','')[:10]}] {n.get('title','')} ({n.get('source','')}): {n.get('summary','')[:150]}"
            for n in news[:5]
        ])
    else:
        news_text = "No hay noticias disponibles en este momento."

    peers_map = {
        "GGAL": [("BMA","Banco Macro"),("SUPV","Supervielle"),("BBAR","Banco BBVA Argentina")],
        "YPF":  [("PAMP","Pampa Energía"),("VIST","Vista Energy"),("TGSU2","Transportadora Gas del Sur")],
        "AL30": [("GD30","Global 2030"),("AE38","Bono 2038"),("AL35","Bono 2035")],
        "GD30": [("AL30","Soberano 2030"),("GD35","Global 2035"),("GD41","Global 2041")],
        "PAMP": [("YPF","YPF"),("VIST","Vista Energy"),("TRAN","Transener")],
        "MELI": [("AMZN","Amazon"),("SHOP","Shopify"),("GLOB","Globant")],
    }
    peers = peers_map.get(ticker.upper(), [("GGAL","Galicia"),("YPF","YPF"),("AL30","AL30")])

    history  = asset_data.get('history', [])
    prices   = [h['price'] for h in history if h.get('price', 0) > 0]
    volatilidad = ""
    if len(prices) >= 10:
        import statistics
        retornos = [(prices[i] - prices[i-1]) / prices[i-1] * 100 for i in range(1, len(prices))]
        vol = round(statistics.stdev(retornos), 2) if len(retornos) > 1 else 0
        volatilidad = f"Volatilidad histórica (semanal): {vol:.1f}%"

    basic_prompt = _build_basic_prompt(asset_data, macro_data, mep_data, mep_comparison)

    return f"""{basic_prompt}

---
## ANÁLISIS PROFUNDO ADICIONAL

{volatilidad}

## NOTICIAS RECIENTES PARA ANALIZAR
{news_text}

## ACTIVOS COMPARABLES (peers)
{', '.join([f"{p[0]} ({p[1]})" for p in peers])}

Además del JSON básico, incluí estas secciones adicionales con análisis PROFESIONAL y ESPECÍFICO:

  "projections": {{
    "months_3":  {{
      "optimistic": "<+X.X% con catalizador específico, ej: +18% si el BCRA libera el cepo>",
      "neutral":    "<+X.X% escenario base con condiciones actuales>",
      "pessimistic":"<-X.X% con riesgo específico, ej: -15% ante reperfilamiento de deuda>"
    }},
    "months_6":  {{
      "optimistic": "<proyección con fundamento>",
      "neutral":    "<proyección base>",
      "pessimistic":"<proyección pesimista>"
    }},
    "months_12": {{
      "optimistic": "<proyección con fundamento>",
      "neutral":    "<proyección base>",
      "pessimistic":"<proyección pesimista>"
    }}
  }},
  "peers": [
    {{"ticker": "{peers[0][0]}", "name": "{peers[0][1]}", "performance_90d": <número real estimado>}},
    {{"ticker": "{peers[1][0]}", "name": "{peers[1][1]}", "performance_90d": <número real estimado>}},
    {{"ticker": "{peers[2][0]}", "name": "{peers[2][1]}", "performance_90d": <número real estimado>}}
  ],
  "news": [
    {{
      "title": "<título de la noticia>",
      "source": "<fuente>",
      "date": "<YYYY-MM-DD>",
      "summary": "<2-3 oraciones explicando el impacto concreto en {ticker}: cómo afecta al precio, a los fundamentals o al sentimiento del mercado>",
      "impact": "<positive|negative|neutral>"
    }}
  ],
  "technical_summary": "<párrafo profesional de 4-5 oraciones con: niveles de soporte y resistencia con precios exactos en ARS, tendencia según medias móviles, RSI estimado y si está sobrecomprado/sobrevendido, volumen relativo, y señal técnica de corto plazo (compra/venta/esperar) con nivel de confianza>"

IMPORTANTE: Las proyecciones deben ser ESPECÍFICAS para {ticker} considerando su sector ({nombre}), el contexto macro argentino actual (riesgo país {macro_data.get('riesgo_pais', '')} pts, MEP ${mep_data.get('price', ''):,.0f}), y los catalizadores e inhibidores propios de este activo."""


def _fallback_basic_analysis(asset_data):
    return {
        "score": 5.0,
        "score_description": "API no configurada — completá OPENAI_API_KEY",
        "factors": [{"title": "Configuración pendiente", "description": "Completá OPENAI_API_KEY en las variables de entorno de Render.", "type": "neutral"}],
        "mep_comparison": {"days_30":0,"days_90":0,"days_365":0,"mep_30":0,"mep_90":0,"mep_365":0},
        "summary": f"Para obtener el análisis profesional de {asset_data['ticker']}, configurá tu clave de OpenAI en las variables de entorno.",
    }


def _fallback_deep_analysis(asset_data):
    base = _fallback_basic_analysis(asset_data)
    base.update({
        "projections": {
            "months_3":  {"optimistic":"N/D","neutral":"N/D","pessimistic":"N/D"},
            "months_6":  {"optimistic":"N/D","neutral":"N/D","pessimistic":"N/D"},
            "months_12": {"optimistic":"N/D","neutral":"N/D","pessimistic":"N/D"},
        },
        "peers": [], "news": [],
        "technical_summary": "Configurá OPENAI_API_KEY para obtener análisis técnico profesional.",
    })
    return base
