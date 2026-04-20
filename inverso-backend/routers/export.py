"""
Router de exportación a PDF.
Genera un PDF profesional del análisis usando html2pdf via subprocess.
"""
import logging
import subprocess
import tempfile
import os
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/pdf")
async def export_pdf(analysis: dict, current_user: dict = Depends(get_current_user)):
    """
    Recibe los datos de un análisis y devuelve un PDF.
    """
    try:
        html = _build_pdf_html(analysis)
        pdf_bytes = _html_to_pdf(html)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=inverso-{analysis.get('ticker','análisis')}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando PDF: {str(e)}")


def _build_pdf_html(data: dict) -> str:
    ticker  = data.get("ticker", "")
    name    = data.get("name", "")
    price   = data.get("price", "")
    change  = data.get("change_pct", "")
    score   = data.get("score", "")
    summary = data.get("summary", "")
    factors = data.get("factors", [])

    factors_html = ""
    for f in factors:
        color = "#4caf82" if f.get("type") == "positive" else "#e05a5a" if f.get("type") == "negative" else "#c9a96e"
        factors_html += f"""
        <div style="padding:10px;border-left:3px solid {color};margin-bottom:8px;background:#f9f8f6">
          <strong style="color:#1a1f2e">{f.get('title','')}</strong>
          <p style="margin:4px 0 0;color:#5a6275;font-size:13px">{f.get('description','')}</p>
        </div>"""

    projections_html = ""
    if "projections" in data:
        for period, label in [("months_3","3 meses"), ("months_6","6 meses"), ("months_12","12 meses")]:
            p = data["projections"].get(period, {})
            projections_html += f"""
            <div style="flex:1;background:#f9f8f6;padding:12px;border-radius:6px;margin:4px">
              <div style="color:#c9a96e;font-size:11px;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">{label}</div>
              <div style="font-size:12px;color:#5a6275">▲ Optimista: <strong style="color:#4caf82">{p.get('optimistic','')}</strong></div>
              <div style="font-size:12px;color:#5a6275">→ Neutro: <strong style="color:#c9a96e">{p.get('neutral','')}</strong></div>
              <div style="font-size:12px;color:#5a6275">▼ Pesimista: <strong style="color:#e05a5a">{p.get('pessimistic','')}</strong></div>
            </div>"""

    change_color = "#4caf82" if float(change or 0) >= 0 else "#e05a5a"
    change_sign  = "+" if float(change or 0) >= 0 else ""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8"/>
<style>
  body{{font-family:Arial,sans-serif;color:#1a1f2e;margin:0;padding:40px;background:#fff}}
  .header{{border-bottom:3px solid #c9a96e;padding-bottom:20px;margin-bottom:24px}}
  .logo{{font-size:28px;font-weight:700;color:#c9a96e;letter-spacing:1px}}
  .logo span{{color:#1a1f2e}}
  .ticker{{font-size:36px;font-weight:700;margin:12px 0 4px}}
  .asset-name{{color:#7a8394;font-size:14px}}
  .price-row{{display:flex;align-items:baseline;gap:12px;margin-top:8px}}
  .price{{font-size:28px;font-weight:600}}
  .change{{font-size:16px;color:{change_color}}}
  .score-section{{background:#0b0e13;color:#fff;padding:20px;border-radius:8px;text-align:center;margin-bottom:24px}}
  .score-num{{font-size:52px;font-weight:700;color:#c9a96e;line-height:1}}
  .score-label{{font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#7a8394;margin-top:4px}}
  .score-desc{{font-size:13px;color:#e8e4dc;margin-top:8px}}
  h2{{font-size:14px;letter-spacing:2px;text-transform:uppercase;color:#c9a96e;margin:20px 0 12px;border-bottom:1px solid #e5e0d8;padding-bottom:6px}}
  .summary{{font-size:14px;line-height:1.8;color:#5a6275;background:#f9f8f6;padding:16px;border-left:3px solid #c9a96e}}
  .footer{{margin-top:40px;padding-top:16px;border-top:1px solid #e5e0d8;font-size:11px;color:#aaa;text-align:center}}
  .proj-row{{display:flex;gap:8px;margin-bottom:16px}}
</style>
</head>
<body>
<div class="header">
  <div class="logo">Inver<span>so</span></div>
  <div style="font-size:11px;color:#aaa;margin-top:2px">Análisis de activos con IA · Mercado argentino</div>
</div>

<div class="ticker">{ticker}</div>
<div class="asset-name">{name}</div>
<div class="price-row">
  <span class="price">${price} ARS</span>
  <span class="change">{change_sign}{change}% hoy</span>
</div>

<br/>
<div class="score-section">
  <div class="score-num">{score}</div>
  <div class="score-label">Score de oportunidad</div>
  <div class="score-desc">{data.get('score_description','')}</div>
</div>

<h2>Factores clave</h2>
{factors_html}

<h2>Síntesis</h2>
<div class="summary">{summary}</div>

{"<h2>Proyecciones</h2><div class='proj-row'>" + projections_html + "</div>" if projections_html else ""}

<div class="footer">
  Generado por Inverso · Este análisis es informativo y no constituye asesoramiento financiero profesional ·
  inverso.app · {__import__('datetime').datetime.now().strftime('%d/%m/%Y %H:%M')}
</div>
</body>
</html>"""


def _html_to_pdf(html: str) -> bytes:
    """Convierte HTML a PDF usando wkhtmltopdf si está disponible, sino devuelve el HTML."""
    with tempfile.NamedTemporaryFile(suffix=".html", mode="w", delete=False, encoding="utf-8") as f:
        f.write(html)
        html_path = f.name

    pdf_path = html_path.replace(".html", ".pdf")

    try:
        result = subprocess.run(
            ["wkhtmltopdf", "--quiet", html_path, pdf_path],
            capture_output=True, timeout=30
        )
        if result.returncode == 0 and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                return f.read()
    except FileNotFoundError:
        logger.info("wkhtmltopdf no disponible, usando fallback HTML")
    except subprocess.TimeoutExpired:
        logger.warning("wkhtmltopdf tardó más de 30s, usando fallback HTML")
    finally:
        for p in [html_path, pdf_path]:
            try:
                os.unlink(p)
            except OSError:
                pass

    # Fallback: devolver el HTML como bytes
    return html.encode("utf-8")
