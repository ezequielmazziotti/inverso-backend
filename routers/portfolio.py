from fastapi import APIRouter
from models.schemas import FixedPortfolioRequest, DynamicPortfolioRequest
from services.portfolio import simulate_fixed_portfolio, simulate_dynamic_portfolio

router = APIRouter()


@router.post("/fixed")
async def fixed_portfolio(req: FixedPortfolioRequest):
    """
    Simula una cartera fija desde una fecha de inicio hasta hoy.
    """
    allocations = [{"ticker": a.ticker, "percentage": a.percentage} for a in req.allocations]
    return await simulate_fixed_portfolio(
        amount=req.amount,
        currency=req.currency,
        start_date=req.start_date,
        allocations=allocations,
    )


@router.post("/dynamic")
async def dynamic_portfolio(req: DynamicPortfolioRequest):
    """
    Calcula resultado de una cartera dinámica con operaciones de compra y venta.
    """
    operations = [
        {
            "type":     op.type,
            "ticker":   op.ticker,
            "quantity": op.quantity,
            "price":    op.price,
            "date":     op.date,
        }
        for op in req.operations
    ]
    return await simulate_dynamic_portfolio(operations, req.currency)
