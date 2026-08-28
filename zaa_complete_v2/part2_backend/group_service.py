"""
ZAA Group Selling Service
"""

import logging, uuid
from datetime import datetime, timedelta
from typing import Dict, Any
from services.database import get_pool

logger = logging.getLogger(__name__)

async def find_or_create_group(commodity_name: str, user: dict) -> Dict[str, Any]:
    pool = await get_pool()
    district = user.get("location_district", "Tamale")
    async with pool.acquire() as conn:
        commodity = await conn.fetchrow("SELECT id FROM commodities WHERE name_en ILIKE $1 LIMIT 1", f"%{commodity_name}%")
        if not commodity:
            return {"error": "Commodity not found"}
        existing = await conn.fetchrow("""
            SELECT g.*, COUNT(gm.id) as mc, COALESCE(SUM(gm.quantity_contributed),0) as tq
            FROM selling_groups g LEFT JOIN group_members gm ON g.id = gm.group_id
            WHERE g.commodity_id = $1 AND g.location_district = $2 AND g.status = 'forming' AND g.deadline > CURRENT_DATE
            GROUP BY g.id ORDER BY g.created_at DESC LIMIT 1
        """, commodity["id"], district)
        if existing:
            await conn.execute("INSERT INTO group_members (group_id, farmer_id, quantity_contributed, unit, contribution_percentage) VALUES ($1,$2,$3,$4,$5) ON CONFLICT DO NOTHING",
                existing["id"], user["id"], 50, "kg", 10)
            return {"is_new": False, "group_id": existing["id"], "member_count": existing["mc"]+1, "total_quantity": existing["tq"]+50}
        gid = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO selling_groups (id, name, commodity_id, location_district, target_price_per_unit, ai_suggested_premium_pct, status, coordinator_id, deadline)
            VALUES ($1,$2,$3,$4,$5,$6,'forming',$7,$8)
        """, gid, f"{commodity_name} - {district}", commodity["id"], district, 0, 25.0, user["id"], datetime.now()+timedelta(days=14))
        await conn.execute("INSERT INTO group_members (group_id, farmer_id, quantity_contributed, unit, contribution_percentage) VALUES ($1,$2,$3,$4,$5)",
            gid, user["id"], 50, "kg", 100)
        return {"is_new": True, "group_id": gid, "member_count": 1, "total_quantity": 50}
