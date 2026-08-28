"""
ZAA Listing Service
Handles creation and management of product listings
"""

import logging
from typing import Dict, Any, List, Optional
import uuid

from database import get_pool

logger = logging.getLogger(__name__)

async def create_listing(
    seller_id: str,
    commodity_name: str,
    quantity: float,
    unit: str = "kg",
    asking_price: Optional[float] = None,
    location_district: Optional[str] = None,
    location_village: Optional[str] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new product listing"""
    pool = await get_pool()

    async with pool.acquire() as conn:
        # Find commodity ID
        commodity = await conn.fetchrow(
            "SELECT id FROM commodities WHERE name_en ILIKE $1 OR name_dag ILIKE $1 LIMIT 1",
            f"%{commodity_name}%"
        )

        if not commodity:
            # Create generic commodity entry
            commodity_id = str(uuid.uuid4())
            await conn.execute(
                "INSERT INTO commodities (id, name_en, category) VALUES ($1, $2, 'other')",
                commodity_id, commodity_name
            )
        else:
            commodity_id = commodity["id"]

        # Create listing
        listing_id = str(uuid.uuid4())

        await conn.execute(
            """
            INSERT INTO listings 
            (id, seller_id, commodity_id, quantity, unit, asking_price_per_unit,
             location_district, location_village, description, status, expiry_date)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'active', CURRENT_DATE + INTERVAL '14 days')
            """,
            listing_id, seller_id, commodity_id, quantity, unit, asking_price,
            location_district, location_village, description
        )

        return {
            "id": listing_id,
            "commodity": commodity_name,
            "quantity": quantity,
            "unit": unit,
            "status": "active"
        }

async def get_user_listings(user_id: str) -> List[Dict[str, Any]]:
    """Get all active listings for a user"""
    pool = await get_pool()

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT l.*, c.name_en as commodity_name,
                   (SELECT COUNT(*) FROM bids WHERE listing_id = l.id) as bid_count
            FROM listings l
            JOIN commodities c ON l.commodity_id = c.id
            WHERE l.seller_id = $1 AND l.status = 'active'
            ORDER BY l.created_at DESC
            """,
            user_id
        )

        return [dict(row) for row in rows]

async def get_listing_by_id(listing_id: str) -> Optional[Dict[str, Any]]:
    """Get a single listing by ID"""
    pool = await get_pool()

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT l.*, c.name_en as commodity_name, u.display_name as seller_name
            FROM listings l
            JOIN commodities c ON l.commodity_id = c.id
            JOIN users u ON l.seller_id = u.id
            WHERE l.id = $1
            """,
            listing_id
        )

        return dict(row) if row else None

async def get_all_listings(
    commodity: Optional[str] = None,
    location_district: Optional[str] = None,
    location_region: Optional[str] = None,
    grade: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    status: str = "active",
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Get all listings with optional filters"""
    pool = await get_pool()

    # Build dynamic query
    conditions = ["l.status = $1"]
    params = [status]
    param_count = 1

    if commodity:
        param_count += 1
        conditions.append(f"c.name_en ILIKE ${param_count}")
        params.append(f"%{commodity}%")

    if location_district:
        param_count += 1
        conditions.append(f"l.location_district ILIKE ${param_count}")
        params.append(f"%{location_district}%")

    if location_region:
        param_count += 1
        conditions.append(f"u.location_region ILIKE ${param_count}")
        params.append(f"%{location_region}%")

    if grade:
        param_count += 1
        conditions.append(f"l.quality_grade = ${param_count}")
        params.append(grade)

    if min_price:
        param_count += 1
        conditions.append(f"l.asking_price_per_unit >= ${param_count}")
        params.append(min_price)

    if max_price:
        param_count += 1
        conditions.append(f"l.asking_price_per_unit <= ${param_count}")
        params.append(max_price)

    where_clause = " AND ".join(conditions)

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            f"""
            SELECT l.*, c.name_en as commodity_name, u.display_name as seller_name,
                   u.location_region, u.rating as seller_rating,
                   (SELECT COUNT(*) FROM bids WHERE listing_id = l.id) as bid_count
            FROM listings l
            JOIN commodities c ON l.commodity_id = c.id
            JOIN users u ON l.seller_id = u.id
            WHERE {where_clause}
            ORDER BY l.created_at DESC
            LIMIT ${param_count + 1} OFFSET ${param_count + 2}
            """,
            *params, limit, offset
        )

        return [dict(row) for row in rows]

async def update_listing_status(listing_id: str, status: str) -> bool:
    """Update listing status"""
    pool = await get_pool()

    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE listings SET status = $1 WHERE id = $2",
            status, listing_id
        )

        return result != "UPDATE 0"
