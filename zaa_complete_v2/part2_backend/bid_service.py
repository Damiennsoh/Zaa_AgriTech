"""
ZAA Bid & Negotiation Service
Handles bids, counter-offers, and deal acceptance
"""

import logging
from typing import Dict, Any, Optional
import uuid
from datetime import datetime

from services.database import get_pool

logger = logging.getLogger(__name__)

async def place_bid(buyer_id: str, listing_id: str, bid_price: float, 
                    quantity_requested: Optional[float] = None,
                    delivery_terms: str = "farmer_delivers",
                    payment_terms: str = "50_50") -> Dict[str, Any]:
    """Place a bid on a listing"""
    pool = await get_pool()

    async with pool.acquire() as conn:
        # Get listing details
        listing = await conn.fetchrow(
            "SELECT * FROM listings WHERE id = $1 AND status = 'active'",
            listing_id
        )

        if not listing:
            return {"success": False, "error": "Listing not found or not active"}

        # Check if buyer is not the seller
        if listing["seller_id"] == buyer_id:
            return {"success": False, "error": "Cannot bid on your own listing"}

        qty = quantity_requested or listing["quantity"]
        total = bid_price * qty

        bid_id = str(uuid.uuid4())

        await conn.execute(
            """
            INSERT INTO bids 
            (id, listing_id, buyer_id, bid_price_per_unit, total_bid_value, 
             quantity_requested, unit, delivery_terms, payment_terms)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            bid_id, listing_id, buyer_id, bid_price, total,
            qty, listing["unit"], delivery_terms, payment_terms
        )

        return {
            "success": True,
            "bid_id": bid_id,
            "listing_id": listing_id,
            "price": bid_price,
            "total": total,
            "quantity": qty,
            "buyer_id": buyer_id
        }

async def get_bids_for_listing(listing_id: str) -> list:
    """Get all bids for a listing"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT b.*, u.display_name as buyer_name, u.phone_number as buyer_phone
            FROM bids b
            JOIN users u ON b.buyer_id = u.id
            WHERE b.listing_id = $1
            ORDER BY b.bid_price_per_unit DESC
            """,
            listing_id
        )
        return [dict(row) for row in rows]

async def get_bids_for_buyer(buyer_id: str) -> list:
    """Get all bids placed by a specific buyer (for "My Bids" dashboard tab)"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT 
                b.*,
                c.name_en as commodity_name,
                l.quantity as listing_quantity,
                l.unit,
                u.display_name as seller_name,
                l.location_district,
                l.location_village
            FROM bids b
            JOIN listings l ON b.listing_id = l.id
            JOIN commodities c ON l.commodity_id = c.id
            JOIN users u ON l.seller_id = u.id
            WHERE b.buyer_id = $1
            ORDER BY b.created_at DESC
            """,
            buyer_id
        )
        return [dict(row) for row in rows]

async def accept_bid(bid_id: str, seller_id: str) -> Dict[str, Any]:
    """Seller accepts a bid"""
    pool = await get_pool()

    async with pool.acquire() as conn:
        bid = await conn.fetchrow(
            """
            SELECT b.*, l.seller_id, l.commodity_id, l.quantity, l.unit
            FROM bids b
            JOIN listings l ON b.listing_id = l.id
            WHERE b.id = $1
            """,
            bid_id
        )

        if not bid:
            return {"success": False, "error": "Bid not found"}

        if bid["seller_id"] != seller_id:
            return {"success": False, "error": "Not authorized to accept this bid"}

        if bid["status"] != "pending":
            return {"success": False, "error": "Bid is no longer pending"}

        # Update bid status
        await conn.execute(
            "UPDATE bids SET status = 'accepted', updated_at = NOW() WHERE id = $1",
            bid_id
        )

        # Update listing status
        await conn.execute(
            "UPDATE listings SET status = 'negotiating', updated_at = NOW() WHERE id = $1",
            bid["listing_id"]
        )

        # Create transaction
        transaction_id = str(uuid.uuid4())
        platform_fee = bid["total_bid_value"] * 0.02  # 2% platform fee
        seller_receives = bid["total_bid_value"] - platform_fee
        deposit_amount = bid["total_bid_value"] * 0.5  # 50% deposit

        await conn.execute(
            """
            INSERT INTO transactions
            (id, bid_id, listing_id, seller_id, buyer_id, commodity_id,
             quantity, unit, agreed_price_per_unit, total_value, platform_fee, 
             seller_receives, deposit_amount, status, escrow_status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, 'pending', 'pending')
            """,
            transaction_id, bid_id, bid["listing_id"], seller_id, bid["buyer_id"],
            bid["commodity_id"], bid["quantity_requested"], bid["unit"],
            bid["bid_price_per_unit"], bid["total_bid_value"], platform_fee, 
            seller_receives, deposit_amount
        )

        # Get buyer name and phone for notification
        buyer = await conn.fetchrow(
            "SELECT display_name, phone_number FROM users WHERE id = $1", 
            bid["buyer_id"]
        )

        return {
            "success": True,
            "transaction_id": transaction_id,
            "buyer_id": bid["buyer_id"],
            "buyer_name": buyer["display_name"] if buyer else "Buyer",
            "buyer_phone": buyer["phone_number"] if buyer else None,
            "price": bid["bid_price_per_unit"],
            "total": bid["total_bid_value"],
            "deposit_amount": deposit_amount
        }
