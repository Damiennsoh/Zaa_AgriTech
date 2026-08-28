"""
ZAA Listing Service
Handles creation and management of product listings
"""

import logging
from typing import Dict, Any, List, Optional
import uuid

from services.database import get_pool

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
            RETURNING *
            """,
            listing_id, seller_id, commodity_id, quantity, unit, asking_price,
            location_district, location_village, description
        )

        # Fetch the created listing with commodity name
        listing = await conn.fetchrow(
            """
            SELECT l.*, c.name_en as commodity_name, u.display_name as seller_name
            FROM listings l
            JOIN commodities c ON l.commodity_id = c.id
            JOIN users u ON l.seller_id = u.id
            WHERE l.id = $1
            """,
            listing_id
        )

        return dict(listing) if listing else {"id": listing_id, "status": "active"}

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
    """
    Get all listings with filters.
    This is the main endpoint for the buyer dashboard.
    """
    pool = await get_pool()

    conditions = ["l.status = $1"]
    params = [status]
    param_idx = 2

    if commodity:
        conditions.append(f"(c.name_en ILIKE ${param_idx} OR c.name_dag ILIKE ${param_idx})")
        params.append(f"%{commodity}%")
        param_idx += 1

    if location_district:
        conditions.append(f"l.location_district ILIKE ${param_idx}")
        params.append(f"%{location_district}%")
        param_idx += 1

    if location_region:
        conditions.append(f"l.location_region ILIKE ${param_idx}")
        params.append(f"%{location_region}%")
        param_idx += 1

    if grade:
        conditions.append(f"l.quality_grade = ${param_idx}")
        params.append(grade)
        param_idx += 1

    if min_price is not None:
        conditions.append(f"l.asking_price_per_unit >= ${param_idx}")
        params.append(min_price)
        param_idx += 1

    if max_price is not None:
        conditions.append(f"l.asking_price_per_unit <= ${param_idx}")
        params.append(max_price)
        param_idx += 1

    where_clause = " AND ".join(conditions)

    query = f"""
        SELECT 
            l.id,
            l.commodity_id as commodity,
            c.name_en as commodity_name,
            l.quantity,
            l.unit,
            l.quality_grade,
            l.ai_confidence,
            l.asking_price_per_unit,
            l.location_district,
            l.location_village,
            u.display_name as seller_name,
            COALESCE(u.rating, 4.0) as seller_rating,
            l.status,
            l.photos,
            l.gps_latitude,
            l.gps_longitude,
            l.created_at,
            l.description,
            (SELECT COUNT(*) FROM bids WHERE listing_id = l.id) as bid_count,
            COALESCE(
                (SELECT jsonb_object_agg(key, value) 
                 FROM ai_grading_results 
                 WHERE listing_id = l.id 
                 ORDER BY created_at DESC 
                 LIMIT 1),
                '{{}}'::jsonb
            ) as attributes
        FROM listings l
        JOIN commodities c ON l.commodity_id = c.id
        JOIN users u ON l.seller_id = u.id
        WHERE {where_clause}
        ORDER BY l.created_at DESC
        LIMIT ${param_idx} OFFSET ${param_idx + 1}
    """
    params.extend([limit, offset])

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)
        return [dict(row) for row in rows]

async def get_user_listings(user_id: str) -> List[Dict[str, Any]]:
    """Get all active listings for a specific user"""
    pool = await get_pool()

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT 
                l.*, 
                c.name_en as commodity_name,
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
    """Get a single listing by ID with full details"""
    pool = await get_pool()

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT 
                l.*,
                c.name_en as commodity_name,
                c.name_dag as commodity_name_dag,
                u.display_name as seller_name,
                u.phone_number as seller_phone,
                u.location_district as seller_district,
                u.location_village as seller_village,
                COALESCE(u.rating, 4.0) as seller_rating,
                u.years_in_farming as seller_experience,
                (SELECT COUNT(*) FROM bids WHERE listing_id = l.id) as bid_count,
                (SELECT jsonb_agg(
                    jsonb_build_object(
                        'grade', grade,
                        'confidence', confidence,
                        'attributes', attributes,
                        'estimated_value', estimated_value_per_unit
                    )
                ) FROM ai_grading_results WHERE listing_id = l.id ORDER BY created_at DESC) as grading_history
            FROM listings l
            JOIN commodities c ON l.commodity_id = c.id
            JOIN users u ON l.seller_id = u.id
            WHERE l.id = $1
            """,
            listing_id
        )

        return dict(row) if row else None

async def update_listing_status(listing_id: str, status: str) -> bool:
    """Update the status of a listing"""
    pool = await get_pool()

    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE listings 
            SET status = $1, updated_at = NOW() 
            WHERE id = $2
            """,
            status, listing_id
        )

        # result is like "UPDATE 1" if successful, "UPDATE 0" if not found
        return "UPDATE 1" in result
