"""Bid & negotiation operations backed by Supabase PostgREST."""
from typing import Any, Dict, List, Optional
import uuid
from database import request

async def place_bid(buyer_id: str, listing_id: str, bid_price: float, quantity_requested: Optional[float] = None, delivery_terms: str = "farmer_delivers", payment_terms: str = "50_50") -> Dict[str, Any]:
    listing = (await request("GET", "listings", params={"select": "quantity,unit", "id": f"eq.{listing_id}", "status": "eq.active", "limit": "1"}) or [None])[0]
    if not listing:
        return {"success": False, "error": "Listing not found"}
    qty = quantity_requested or listing["quantity"]
    total = bid_price * qty
    bid_id = str(uuid.uuid4())
    await request("POST", "bids", payload={"id": bid_id, "listing_id": listing_id, "buyer_id": buyer_id, "bid_price_per_unit": bid_price, "total_bid_value": total, "quantity_requested": qty, "unit": listing["unit"], "delivery_terms": delivery_terms, "payment_terms": payment_terms, "status": "pending"})
    return {"success": True, "bid_id": bid_id, "buyer_id": buyer_id, "price": bid_price, "total": total}

async def get_bids_for_listing(listing_id: str) -> List[Dict[str, Any]]:
    return await request("GET", "bids", params={"select": "*,users!buyer_id(display_name)", "listing_id": f"eq.{listing_id}", "order": "created_at.desc"}) or []

async def accept_bid(bid_id: str, seller_id: str) -> Dict[str, Any]:
    bids = await request("GET", "bids", params={"select": "*,listings(seller_id,commodity_id)", "id": f"eq.{bid_id}", "limit": "1"}) or []
    if not bids or bids[0]["listings"]["seller_id"] != seller_id:
        return {"success": False, "error": "Unauthorized"}
    bid = bids[0]
    await request("PATCH", "bids", params={"id": f"eq.{bid_id}"}, payload={"status": "accepted"})
    await request("PATCH", "listings", params={"id": f"eq.{bid['listing_id']}"}, payload={"status": "negotiating"})
    tx_id = str(uuid.uuid4())
    fee = bid["total_bid_value"] * 0.02
    seller_gets = bid["total_bid_value"] - fee
    await request("POST", "transactions", payload={"id": tx_id, "bid_id": bid_id, "listing_id": bid["listing_id"], "seller_id": seller_id, "buyer_id": bid["buyer_id"], "commodity_id": bid["listings"]["commodity_id"], "quantity": bid["quantity_requested"], "unit": bid["unit"], "agreed_price_per_unit": bid["bid_price_per_unit"], "total_value": bid["total_bid_value"], "platform_fee": fee, "seller_receives": seller_gets, "status": "pending"})
    return {"success": True, "transaction_id": tx_id, "buyer_id": bid["buyer_id"], "price": bid["bid_price_per_unit"], "total": bid["total_bid_value"]}

async def get_bids_for_buyer(buyer_id: str) -> List[Dict[str, Any]]:
    return await request("GET", "bids", params={"select": "*,listings(status,commodity_id),commodities(name_en)", "buyer_id": f"eq.{buyer_id}", "order": "created_at.desc"}) or []

__all__ = ["place_bid", "get_bids_for_listing", "accept_bid", "get_bids_for_buyer"]
