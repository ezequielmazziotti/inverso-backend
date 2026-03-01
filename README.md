# Inverso — Backend API

Backend de Inverso, la herramienta de análisis de activos con IA para el mercado argentino.

## Stack

- **Python 3.11+** con FastAPI
- **Claude API** (Anthropic) para el análisis con IA
- **yfinance** para datos históricos de acciones y CEDEARs
- **BCRA API** para datos macroeconómicos (gratuita)
- **Supabase** para base de datos y autenticación
- **Railway** para hosting

---

## Deploy paso a paso (sin saber programar)

### Paso 1 — Crear cuenta en Supabase (gratis)

1. Ir a https://supabase.com y crear una cuenta
2. Crear un nuevo proyecto (elegí región "South America")
3. En el menú izquierdo ir a **SQL Editor**
4. Copiar el contenido del archivo `database_schema.sql` y ejecutarlo
5. Ir a **Settings → API** y copiar:
   - `Project URL` → es tu `SUPABASE_URL`
   - `anon/public key` → es tu `SUPABASE_KEY`

### Paso 2 — Obtener API key de Anthropic

1. Ir a https://console.anthropic.com
2. Crear una cuenta y agregar crédito (mínimo $5 USD)
3. Ir a **API Keys** y crear una nueva clave
4. Copiar la clave → es tu `ANTHROPIC_API_KEY`

### Paso 3 — Obtener API key de NewsAPI (opcional)

1. Ir a https://newsapi.org y crear cuenta gratuita
2. Copiar la API key de tu dashboard
3. El plan gratuito incluye 100 llamadas por día (suficiente para el MVP)

### Paso 4 — Subir el código a GitHub

1. Crear una cuenta en https://github.com si no tenés
2. Crear un repositorio nuevo llamado `inverso-backend`
3. Subir todos los archivos de esta carpeta al repositorio
4. **MUY IMPORTANTE:** NO subas el archivo `.env` (está en el .gitignore para evitarlo)

### Paso 5 — Deploy en Railway

1. Ir a https://railway.app y crear cuenta (gratis hasta $5 USD/mes de uso)
2. Hacer clic en **New Project → Deploy from GitHub repo**
3. Seleccionar el repositorio `inverso-backend`
4. Railway detecta automáticamente que es Python y usa el `Procfile`
5. Ir a **Variables** y agregar cada variable del archivo `.env.example` con sus valores reales:
   - `ANTHROPIC_API_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `NEWS_API_KEY` (opcional)
   - `SECRET_KEY` (inventar una cadena larga aleatoria)
6. Railway hace el deploy automáticamente
7. En **Settings → Domains** generar un dominio público (ej: `inverso-backend.railway.app`)

### Paso 6 — Conectar el frontend

En el archivo `inverso-app.html` del frontend, reemplazar todas las referencias a `http://localhost:8000` por la URL de Railway que generaste en el paso anterior.

---

## Estructura del proyecto

```
inverso-backend/
├── main.py                 # Punto de entrada de la aplicación
├── config.py               # Variables de entorno
├── requirements.txt        # Dependencias Python
├── Procfile                # Configuración de Railway
├── database_schema.sql     # SQL para crear las tablas en Supabase
├── .env.example            # Variables de entorno de ejemplo
├── .gitignore
├── routers/
│   ├── auth.py             # Login y registro
│   ├── assets.py           # Búsqueda de activos
│   ├── analysis.py         # Análisis básico y profundo
│   └── portfolio.py        # Simulador de cartera
└── services/
    ├── market_data.py      # yfinance + BCRA + MEP
    ├── ai_analysis.py      # Integración con Claude
    └── database.py         # Operaciones con Supabase
```

---

## Endpoints disponibles

| Método | Ruta | Descripción | Plan requerido |
|--------|------|-------------|----------------|
| POST | /auth/register | Registrar usuario | — |
| POST | /auth/login | Iniciar sesión | — |
| GET | /assets/search?q=GGAL | Buscar activos | — |
| GET | /assets/popular | Activos más consultados | — |
| GET | /assets/market-summary | Resumen del mercado | — |
| POST | /analyze/basic | Análisis básico | Free (3/mes) |
| POST | /analyze/deep | Análisis profundo | Pro |
| GET | /analyze/history | Historial de análisis | Basic/Pro |
| POST | /portfolio/fixed | Simulador cartera fija | Pro |
| POST | /portfolio/dynamic | Simulador cartera dinámica | Pro |

La documentación interactiva de todos los endpoints está disponible en `/docs` una vez deployado.

---

## Desarrollo local (opcional)

Si querés correrlo localmente para probarlo:

```bash
# 1. Instalar Python 3.11+ desde python.org

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Copiar y completar variables de entorno
cp .env.example .env
# Editar .env con tus claves reales

# 5. Correr el servidor
uvicorn main:app --reload

# 6. Abrir en el navegador
# http://localhost:8000/docs
```

---

## Costos estimados

| Servicio | Costo |
|----------|-------|
| Railway | $0-7 USD/mes |
| Supabase | $0 (hasta 500MB) |
| Claude API | ~$0.003 por análisis básico / ~$0.015 por análisis profundo |
| NewsAPI | $0 (plan gratuito, 100 llamadas/día) |
| **Total MVP** | **$0-57 USD/mes** |

Con 20 usuarios en el plan Basic ($7.99) los costos operativos quedan cubiertos.

---

## Soporte

Ante cualquier duda en el deploy, la documentación de Railway está en https://docs.railway.app y la de Supabase en https://supabase.com/docs
