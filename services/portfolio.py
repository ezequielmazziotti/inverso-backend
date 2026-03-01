"""
Servicio del simulador de cartera.
Calcula evolución histórica de carteras fijas y dinámicas.
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, date, timedelta
from services.market_data import TICKER_MAP


async def simulate_fixed_portfolio(amount: float, currency: str, start_date: date, allocations: list) -> dict:
    """
    Simula una cartera fija desde start_date hasta hoy.
    """
    end_date = datetime.now().date()
    start_str = start_date.strftime("%Y-%m-%d")

    # Descargar historial de todos los activos
    all_prices = {}
    for alloc in allocations:
        ticker = alloc["ticker"].upper()
        yf_ticker = TICKER_MAP.get(ticker, ticker + ".BA")
        try:
            stock = yf.Ticker(yf_ticker)
            hist = stock.history(start=start_str)["Close"]
            if not hist.empty:
                all_prices[ticker] = hist
        except Exception:
            pass

    if not all_prices:
        return _fallback_portfolio_result(amount)

    # Crear DataFrame unificado con fechas en común
    df = pd.DataFrame(all_prices).dropna()
    if df.empty:
        return _fallback_portfolio_result(amount)

    # Calcular valor de la cartera día a día
    portfolio_values = []
    initial_prices = df.iloc[0]

    for idx, row in df.iterrows():
        day_value = 0
        for alloc in allocations:
            ticker = alloc["ticker"].upper()
            pct = alloc["percentage"] / 100
            if ticker in row and ticker in initial_prices:
                units = (amount * pct) / initial_prices[ticker]
                day_value += units * row[ticker]
        portfolio_values.append({
            "date":  str(idx.date()),
            "value": round(day_value, 2)
        })

    # Comparación con inflación y MEP (aproximación mensual)
    months = max(1, len(df) // 22)
    inflation_monthly = 2.4 / 100
    inflation_total = ((1 + inflation_monthly) ** months - 1) * 100

    mep_monthly = 0.3 / 100
    mep_total = ((1 + mep_monthly) ** months - 1) * 100

    current_value = portfolio_values[-1]["value"] if portfolio_values else amount
    total_return = ((current_value - amount) / amount) * 100

    # Convertir a USD si se pidió
    if currency == "usd":
        usd_rate = 1247.0
        amount        = round(amount / usd_rate, 2)
        current_value = round(current_value / usd_rate, 2)

    return {
        "initial_amount":    round(amount, 2),
        "current_value":     round(current_value, 2),
        "total_return_pct":  round(total_return, 1),
        "vs_inflation_pct":  round(total_return - inflation_total, 1),
        "vs_mep_pct":        round(total_return - mep_total, 1),
        "history":           portfolio_values[::3],  # muestra cada 3 días
    }


async def simulate_dynamic_portfolio(operations: list, currency: str) -> dict:
    """
    Calcula resultado de una cartera dinámica con compras y ventas.
    """
    positions = {}
    total_invested = 0

    for op in operations:
        ticker = op["ticker"].upper()
        qty    = op["quantity"]
        price  = op["price"]

        if op["type"].lower() in ["buy", "compra"]:
            if ticker not in positions:
                positions[ticker] = {"quantity": 0, "avg_price": 0, "invested": 0}
            total_cost = positions[ticker]["invested"] + (qty * price)
            total_qty  = positions[ticker]["quantity"] + qty
            positions[ticker]["avg_price"] = total_cost / total_qty
            positions[ticker]["quantity"]  = total_qty
            positions[ticker]["invested"]  = total_cost
            total_invested += qty * price

        elif op["type"].lower() in ["sell", "venta"]:
            if ticker in positions:
                positions[ticker]["quantity"] = max(0, positions[ticker]["quantity"] - qty)

    # Obtener precios actuales
    current_positions = []
    current_value = 0

    for ticker, pos in positions.items():
        if pos["quantity"] <= 0:
            continue
        yf_ticker = TICKER_MAP.get(ticker, ticker + ".BA")
        try:
            stock = yf.Ticker(yf_ticker)
            hist  = stock.history(period="2d")["Close"]
            current_price = float(hist.iloc[-1]) if not hist.empty else pos["avg_price"]
        except Exception:
            current_price = pos["avg_price"]

        position_value = pos["quantity"] * current_price
        current_value += position_value
        gain_pct = ((current_price - pos["avg_price"]) / pos["avg_price"]) * 100

        current_positions.append({
            "ticker":         ticker,
            "quantity":       pos["quantity"],
            "avg_price":      round(pos["avg_price"], 2),
            "current_price":  round(current_price, 2),
            "value":          round(position_value, 2),
            "gain_pct":       round(gain_pct, 1),
        })

    total_result = current_value - total_invested
    return_pct   = (total_result / total_invested * 100) if total_invested > 0 else 0

    return {
        "invested_capital": round(total_invested, 2),
        "current_value":    round(current_value, 2),
        "total_result":     round(total_result, 2),
        "return_pct":       round(return_pct, 1),
        "positions":        current_positions,
    }


def _fallback_portfolio_result(amount: float) -> dict:
    return {
        "initial_amount":    amount,
        "current_value":     amount,
        "total_return_pct":  0.0,
        "vs_inflation_pct":  0.0,
        "vs_mep_pct":        0.0,
        "history":           [{"date": str(datetime.now().date()), "value": amount}],
    }
