import logging
from fastapi import APIRouter, Depends
from models.schemas import FixedPortfolioRequest, DynamicPortfolioRequest
from services.portfolio import simulate_fixed_portfolio, simulate_dynamic_portfolio
from services.database import save_simulation, get_user_simulations
from dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/fixed")
async def fixed_portfolio(req: FixedPortfolioRequest, current_user: dict = Depends(get_current_user)):
    """Simula una cartera fija desde una fecha de inicio hasta hoy."""
    allocations = [{"ticker": a.ticker, "percentage": a.percentage} for a in req.allocations]
    result = await simulate_fixed_portfolio(
        amount=req.amount,
        currency=req.currency,
        start_date=req.start_date,
        allocations=allocations,
    )

    user_id = current_user["id"]
    if user_id != "demo":
        config = {"amount": req.amount, "currency": req.currency, "start_date": str(req.start_date), "allocations": allocations}
        save_simulation(user_id, "fixed", config, result)

    logger.info("Simulación fija completada — user=%s", current_user["email"])
    return result


@router.post("/dynamic")
async def dynamic_portfolio(req: DynamicPortfolioRequest, current_user: dict = Depends(get_current_user)):
    """Calcula resultado de una cartera dinámica con operaciones de compra y venta."""
    operations = [
        {"type": op.type, "ticker": op.ticker, "quantity": op.quantity, "price": op.price, "date": str(op.date)}
        for op in req.operations
    ]
    result = await simulate_dynamic_portfolio(operations, req.currency)

    user_id = current_user["id"]
    if user_id != "demo":
        config = {"operations": operations, "currency": req.currency}
        save_simulation(user_id, "dynamic", config, result)

    logger.info("Simulación dinámica completada — user=%s", current_user["email"])
    return result


@router.get("/history")
async def portfolio_history(current_user: dict = Depends(get_current_user)):
    """Historial de simulaciones del usuario autenticado (últimas 20)."""
    simulations = get_user_simulations(current_user["id"])
    return {"simulations": simulations}
