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

async def get_pool() -> asyncpg.Pool:
    """Get or create database connection pool"""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)
    return _pool

async def init_db():
    """Initialize database connection"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("SELECT 1")
    logger.info("✅ Database connected")

async def get_or_create_user(phone: str) -> Dict[str, Any]:
    """Get existing user or create new one"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Try to find existing user
        row = await conn.fetchrow(
            "SELECT * FROM users WHERE phone_number = $1",
            phone
        )

        if row:
            return dict(row)

        # Create new user
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

async def get_user_by_phone(phone: str) -> Optional[Dict[str, Any]]:
    """Get user by phone number"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM users WHERE phone_number = $1",
            phone
        )
        return dict(row) if row else None

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
    pool = await get_pool()
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
