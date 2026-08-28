"""
ZAA Database Service
PostgreSQL / Supabase integration
"""

import os
import asyncpg
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/zaa")

_pool: Optional[asyncpg.Pool] = None
_db_failed: bool = False

async def get_pool() -> Optional[asyncpg.Pool]:
    """Get or create database connection pool"""
    global _pool, _db_failed
    if _pool is None and not _db_failed:
        try:
            _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5, timeout=2.0)
        except Exception as e:
            logger.warning(f"⚠️ Could not create DB pool: {e}")
            _db_failed = True
            _pool = None
    return _pool

async def init_db():
    """Initialize database connection"""
    try:
        pool = await get_pool()
        if pool:
            async with pool.acquire() as conn:
                await conn.execute("SELECT 1")
            logger.info("✅ Database connected")
        else:
            logger.info("⚠️ Running in development mode without database")
    except Exception as e:
        logger.warning(f"⚠️ Database connection failed: {str(e)}")
        logger.info("⚠️ Running in development mode without database")

async def get_or_create_user(phone: str) -> Dict[str, Any]:
    """Get existing user or create new one"""
    try:
        pool = await get_pool()
        if pool:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM users WHERE phone_number = $1",
                    phone
                )
                if row:
                    return dict(row)
                new_user = await conn.fetchrow(
                    """
                    INSERT INTO users (phone_number, user_type, verification_status)
                    VALUES ($1, 'farmer', 'pending')
                    RETURNING *
                    """,
                    phone
                )
                logger.info(f"New user registered: {phone}")
                return dict(new_user)
    except Exception as e:
        logger.warning(f"DB user query failed ({e}), using mock user")
    
    return {
        "id": f"dev-user-{phone[-4:] if len(phone)>=4 else '0000'}",
        "phone_number": phone,
        "user_type": "farmer",
        "verification_status": "verified",
        "preferred_language": "dag"
    }


async def get_user_by_phone(phone: str) -> Optional[Dict[str, Any]]:
    """Get user by phone number"""
    try:
        pool = await get_pool()
        if pool:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM users WHERE phone_number = $1",
                    phone
                )
                return dict(row) if row else None
    except Exception as e:
        logger.warning(f"get_user_by_phone DB query failed: {e}")
    return None

async def save_conversation(
    user_id: str,
    wa_message_id: Optional[str],
    direction: str,
    msg_type: str,
    content: Dict[str, Any],
    language: str,
    ai_intent: Optional[str] = None
):
    """Save conversation to database"""
    try:
        pool = await get_pool()
        if pool:
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO conversations 
                    (user_id, wa_message_id, direction, message_type, content_text, 
                     detected_language, ai_intent)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    user_id,
                    wa_message_id,
                    direction,
                    msg_type,
                    content.get("text", ""),
                    language,
                    ai_intent
                )
    except Exception as e:
        logger.warning(f"save_conversation DB failed: {e}")


async def get_active_transactions(user_id: str) -> List[Dict[str, Any]]:
    """Get active transactions for a user"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT t.*, c.name_en as commodity_name
            FROM transactions t
            JOIN commodities c ON t.commodity_id = c.id
            WHERE (t.seller_id = $1 OR t.buyer_id = $1)
            AND t.status NOT IN ('completed', 'cancelled', 'refunded')
            ORDER BY t.created_at DESC
            """,
            user_id
        )
        return [dict(row) for row in rows]

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
