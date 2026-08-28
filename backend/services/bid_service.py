"""
ZAA Bid & Negotiation Service
"""

import logging
from typing import Dict, Any, Optional, List
import uuid
from database import get_pool

logger = logging.getLogger(__name__)

async def place_bid(buyer_id: str, listing_id: str, bid_price: float,
                    quantity_requested: Optional[float] = None,
                    delivery_terms: str = "farmer_delivers",
                    payment_terms: str = "50_50") -> Dict[str, Any]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        listing = await conn.fetchrow("SELECT * FROM listings WHERE id = $1 AND status = 'active'", listing_id)
        if not listing:
            return {"success": False, "error": "Listing not found"}
        qty = quantity_requested or listing["quantity"]
        total = bid_price * qty
        bid_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO bids (id, listing_id, buyer_id, bid_price_per_unit, total_bid_value, quantity_requested, unit, delivery_terms, payment_terms)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """, bid_id, listing_id, buyer_id, bid_price, total, qty, listing["unit"], delivery_terms, payment_terms)
        return {"success": True, "bid_id": bid_id, "buyer_id": buyer_id, "price": bid_price, "total": total}

async def get_bids_for_listing(listing_id: str) -> List[Dict[str, Any]]:
    """Get all bids for a listing"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT b.*, u.display_name as buyer_name
            FROM bids b
            JOIN users u ON b.buyer_id = u.id
            WHERE b.listing_id = $1
            ORDER BY b.created_at DESC
            """,
            listing_id
        )
        return [dict(row) for row in rows]

async def accept_bid(bid_id: str, seller_id: str) -> Dict[str, Any]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        bid = await conn.fetchrow("""
            SELECT b.*, l.seller_id, l.commodity_id FROM bids b JOIN listings l ON b.listing_id = l.id WHERE b.id = $1
        """, bid_id)
        if not bid or bid["seller_id"] != seller_id:
            return {"success": False, "error": "Unauthorized"}
        await conn.execute("UPDATE bids SET status = 'accepted' WHERE id = $1", bid_id)
        await conn.execute("UPDATE listings SET status = 'negotiating' WHERE id = $1", bid["listing_id"])
        tx_id = str(uuid.uuid4())
        fee = bid["total_bid_value"] * 0.02
        seller_gets = bid["total_bid_value"] - fee
        await conn.execute("""
            INSERT INTO transactions (id, bid_id, listing_id, seller_id, buyer_id, commodity_id, quantity, unit,
            agreed_price_per_unit, total_value, platform_fee, seller_receives, status)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,'pending')
        """, tx_id, bid_id, bid["listing_id"], seller_id, bid["buyer_id"], bid["commodity_id"],
        bid["quantity_requested"], bid["unit"], bid["bid_price_per_unit"], bid["total_bid_value"], fee, seller_gets)
        return {"success": True, "transaction_id": tx_id, "buyer_id": bid["buyer_id"], "price": bid["bid_price_per_unit"], "total": bid["total_bid_value"]}

async def get_bids_for_buyer(buyer_id: str) -> List[Dict[str, Any]]:
    """Get all bids placed by a buyer"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT b.*, l.status as listing_status, c.name_en as commodity_name
            FROM bids b
            JOIN listings l ON b.listing_id = l.id
            JOIN commodities c ON l.commodity_id = c.id
            WHERE b.buyer_id = $1
            ORDER BY b.created_at DESC
            """,
            buyer_id
        )
        return [dict(row) for row in rows]
