"""Group selling operations backed by Supabase PostgREST."""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict
import uuid
from database import request

async def find_or_create_group(commodity_name: str, user: dict) -> Dict[str, Any]:
    district = user.get("location_district") or "Tamale"
    commodities = await request("GET", "commodities", params={"select": "id", "name_en": f"ilike.*{commodity_name}*", "limit": "1"}) or []
    if not commodities:
        return {"error": "Commodity not found"}
    commodity_id = commodities[0]["id"]
    groups = await request("GET", "selling_groups", params={"select": "*", "commodity_id": f"eq.{commodity_id}", "location_district": f"eq.{district}", "status": "eq.forming", "deadline": f"gt.{datetime.now(timezone.utc).isoformat()}", "order": "created_at.desc", "limit": "1"}) or []
    if groups:
        group = groups[0]
        members = await request("POST", "group_members", payload={"group_id": group["id"], "farmer_id": user["id"], "quantity_contributed": 50, "unit": "kg", "contribution_percentage": 10}, prefer="return=representation") or []
        return {"is_new": False, "group_id": group["id"], "member_count": 1, "total_quantity": 50}
    gid = str(uuid.uuid4())
    await request("POST", "selling_groups", payload={"id": gid, "name": f"{commodity_name} - {district}", "commodity_id": commodity_id, "location_district": district, "target_price_per_unit": 0, "ai_suggested_premium_pct": 25, "status": "forming", "coordinator_id": user["id"], "deadline": (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()})
    await request("POST", "group_members", payload={"group_id": gid, "farmer_id": user["id"], "quantity_contributed": 50, "unit": "kg", "contribution_percentage": 100})
    return {"is_new": True, "group_id": gid, "member_count": 1, "total_quantity": 50}

async def check_group_readiness(group_id: str) -> Dict[str, Any]:
    groups = await request("GET", "selling_groups", params={"select": "*", "id": f"eq.{group_id}", "limit": "1"}) or []
    if not groups:
        return {"error": "Group not found"}
    members = await request("GET", "group_members", params={"select": "quantity_contributed", "group_id": f"eq.{group_id}"}) or []
    total = sum(float(member.get("quantity_contributed") or 0) for member in members)
    target = float(groups[0].get("target_quantity") or 500)
    return {"group_id": group_id, "total_quantity": total, "target_quantity": target, "is_ready": total >= target, "status": groups[0]["status"]}
