from pydantic import BaseModel
from typing import Optional, List
from datetime import date

# ── AUTH ──────────────────────────────────────────────
class UserRegister(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

# ── ANÁLISIS ──────────────────────────────────────────
class AnalysisRequest(BaseModel):
    ticker: str
    plan: str = "free"  # free | basic | pro

class Factor(BaseModel):
    title: str
    description: str
    type: str  # positive | negative | neutral

class MEPComparison(BaseModel):
    days_30: float
    days_90: float
    days_365: float
    mep_30: float
    mep_90: float
    mep_365: float

class ProjectionScenario(BaseModel):
    optimistic: str
    neutral: str
    pessimistic: str

class Projections(BaseModel):
    months_3: ProjectionScenario
    months_6: ProjectionScenario
    months_12: ProjectionScenario

class NewsItem(BaseModel):
    title: str
    source: str
    date: str
    summary: str
    impact: str  # positive | negative | neutral

class PeerAsset(BaseModel):
    ticker: str
    name: str
    performance_90d: float

class BasicAnalysis(BaseModel):
    ticker: str
    name: str
    price: float
    change_pct: float
    score: float
    factors: List[Factor]
    mep_comparison: MEPComparison
    summary: str

class DeepAnalysis(BasicAnalysis):
    price_history: List[dict]
    projections: Projections
    peers: List[PeerAsset]
    news: List[NewsItem]
    technical_summary: str

# ── SIMULADOR ─────────────────────────────────────────
class Allocation(BaseModel):
    ticker: str
    percentage: float

class FixedPortfolioRequest(BaseModel):
    amount: float
    currency: str  # ars | usd
    start_date: date
    allocations: List[Allocation]

class Operation(BaseModel):
    type: str  # buy | sell
    ticker: str
    quantity: float
    price: float
    date: date

class DynamicPortfolioRequest(BaseModel):
    operations: List[Operation]
    currency: str = "ars"

class PortfolioResult(BaseModel):
    initial_amount: float
    current_value: float
    total_return_pct: float
    vs_inflation_pct: float
    vs_mep_pct: float
    history: List[dict]

class DynamicPortfolioResult(BaseModel):
    invested_capital: float
    current_value: float
    total_result: float
    return_pct: float
    positions: List[dict]
