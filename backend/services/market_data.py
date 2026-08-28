"""
ZAA Market Data Service
Aggregates and serves real-time agricultural prices
"""

import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Seed price data for MVP
# In production, scrape from market reports, call traders, or partner with MOFA
SEED_PRICES = {
    "shea butter": [
        {"market": "Tamale Central", "price": 8.0, "unit": "kg", "grade": "A", "type": "local"},
        {"market": "Accra Makola", "price": 12.0, "unit": "kg", "grade": "A", "type": "regional"},
        {"market": "Export (FOB)", "price": 18.0, "unit": "kg", "grade": "A", "type": "export"},
        {"market": "Tamale Central", "price": 5.5, "unit": "kg", "grade": "B", "type": "local"},
        {"market": "Accra Makola", "price": 8.0, "unit": "kg", "grade": "B", "type": "regional"},
    ],
    "shea nuts": [
        {"market": "Walewale", "price": 2.0, "unit": "kg", "grade": "A", "type": "local"},
        {"market": "Tamale", "price": 2.5, "unit": "kg", "grade": "A", "type": "local"},
        {"market": "Export", "price": 3.5, "unit": "kg", "grade": "A", "type": "export"},
    ],
    "maize": [
        {"market": "Tamale", "price": 3.5, "unit": "kg", "grade": "A", "type": "local"},
        {"market": "Techiman", "price": 4.0, "unit": "kg", "grade": "A", "type": "regional"},
        {"market": "Accra", "price": 5.0, "unit": "kg", "grade": "A", "type": "regional"},
    ],
    "groundnuts": [
        {"market": "Tamale", "price": 6.0, "unit": "kg", "grade": "A", "type": "local"},
        {"market": "Techiman", "price": 7.0, "unit": "kg", "grade": "A", "type": "regional"},
        {"market": "Export", "price": 10.0, "unit": "kg", "grade": "A", "type": "export"},
    ],
    "millet": [
        {"market": "Bolgatanga", "price": 4.0, "unit": "kg", "grade": "A", "type": "local"},
        {"market": "Tamale", "price": 4.5, "unit": "kg", "grade": "A", "type": "local"},
    ],
    "soybeans": [
        {"market": "Tamale", "price": 5.0, "unit": "kg", "grade": "A", "type": "local"},
        {"market": "Accra", "price": 6.5, "unit": "kg", "grade": "A", "type": "regional"},
    ],
    "cowpeas": [
        {"market": "Tamale", "price": 5.5, "unit": "kg", "grade": "A", "type": "local"},
        {"market": "Accra", "price": 7.0, "unit": "kg", "grade": "A", "type": "regional"},
    ]
}

async def get_current_prices(commodity: str, location: str = None) -> List[Dict[str, Any]]:
    """Get current market prices for a commodity"""
    normalized = commodity.lower().strip()

    prices = SEED_PRICES.get(normalized, [])

    # Filter by location if provided
    if location:
        location_lower = location.lower()
        prices = [p for p in prices if location_lower in p["market"].lower()]

    # If no local prices found, return all prices for that commodity
    if not prices:
        prices = SEED_PRICES.get(normalized, [])

    return prices

async def get_price_history(commodity: str, days: int = 30) -> List[Dict[str, Any]]:
    """Get historical price trends"""
    # In production, query database for historical data
    # For MVP, return simulated trend data

    base_price = 8.0 if "shea butter" in commodity.lower() else 4.0

    history = []
    for i in range(days):
        date = datetime.now() - timedelta(days=i)
        # Simulate seasonal variation
        variation = (i % 7) * 0.1  # Weekly pattern
        history.append({
            "date": date.strftime("%Y-%m-%d"),
            "price": round(base_price + variation + (i * 0.02), 2),
            "market": "Tamale Central"
        })

    return history

async def get_price_trend(commodity: str) -> str:
    """Get price trend direction"""
    history = await get_price_history(commodity, days=7)

    if len(history) < 2:
        return "stable"

    recent = history[0]["price"]
    previous = history[1]["price"]

    diff = ((recent - previous) / previous) * 100

    if diff > 5:
        return "rising"
    elif diff < -5:
        return "falling"
    else:
        return "stable"
