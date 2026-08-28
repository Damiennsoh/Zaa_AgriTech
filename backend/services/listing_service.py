"""Listing operations backed by Supabase PostgREST."""
from typing import Any, Dict, List, Optional
import uuid
from datetime import date, timedelta
from database import request

async def create_listing(seller_id: str, commodity_name: str, quantity: float, unit: str = "kg", asking_price: Optional[float] = None, location_district: Optional[str] = None, location_village: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
    matches = await request("GET", "commodities", params={"select": "id,name_en,name_dag", "or": f"name_en.ilike.*{commodity_name}*,name_dag.ilike.*{commodity_name}*", "limit": "1"}) or []
    if matches:
        commodity_id = matches[0]["id"]
    else:
        created = await request("POST", "commodities", payload={"id": str(uuid.uuid4()), "name_en": commodity_name, "category": "other"}) or []
        commodity_id = created[0]["id"]
    listing_id = str(uuid.uuid4())
    await request("POST", "listings", payload={"id": listing_id, "seller_id": seller_id, "commodity_id": commodity_id, "quantity": quantity, "unit": unit, "asking_price_per_unit": asking_price, "location_district": location_district, "location_village": location_village, "description": description, "status": "active", "expiry_date": (date.today() + timedelta(days=14)).isoformat()})
    return {"id": listing_id, "commodity": commodity_name, "quantity": quantity, "unit": unit, "status": "active"}

async def get_user_listings(user_id: str) -> List[Dict[str, Any]]:
    return await request("GET", "listings", params={"select": "*,commodities(name_en)", "seller_id": f"eq.{user_id}", "status": "eq.active", "order": "created_at.desc"}) or []

async def get_listing_by_id(listing_id: str) -> Optional[Dict[str, Any]]:
    rows = await request("GET", "listings", params={"select": "*,commodities(name_en),users(display_name)", "id": f"eq.{listing_id}", "limit": "1"}) or []
    return rows[0] if rows else None

async def get_all_listings(commodity: Optional[str] = None, location_district: Optional[str] = None, location_region: Optional[str] = None, grade: Optional[str] = None, min_price: Optional[float] = None, max_price: Optional[float] = None, status: str = "active", limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    params = {"select": "*,commodities(name_en),users(display_name,location_region)", "status": f"eq.{status}", "order": "created_at.desc", "limit": str(limit), "offset": str(offset)}
    if commodity: params["commodities.name_en"] = f"ilike.*{commodity}*"
    if location_district: params["location_district"] = f"ilike.*{location_district}*"
    if location_region: params["users.location_region"] = f"ilike.*{location_region}*"
    if grade: params["quality_grade"] = f"eq.{grade}"
    if min_price is not None: params["asking_price_per_unit"] = f"gte.{min_price}"
    if max_price is not None: params["asking_price_per_unit"] = f"lte.{max_price}"
    return await request("GET", "listings", params=params) or []

async def update_listing_status(listing_id: str, status: str) -> bool:
    rows = await request("PATCH", "listings", params={"id": f"eq.{listing_id}"}, payload={"status": status}) or []
    return bool(rows)

__all__ = ["create_listing", "get_user_listings", "get_listing_by_id", "get_all_listings", "update_listing_status"]
