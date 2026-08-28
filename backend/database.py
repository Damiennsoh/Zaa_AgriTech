"""Supabase PostgREST adapter for trusted backend operations."""
import logging
import os
from typing import Any, Dict, List, Optional
from urllib.parse import quote
import httpx

logger = logging.getLogger(__name__)
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


def _headers(prefer: str = "return=representation") -> Dict[str, str]:
    return {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": prefer}

async def request(method: str, table: str, *, params: Optional[Dict[str, str]] = None, payload: Any = None, prefer: str = "return=representation") -> Any:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SECRET_KEY are required")
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.request(method, f"{SUPABASE_URL}/rest/v1/{table}", headers=_headers(prefer), params=params, json=payload)
        response.raise_for_status()
        return response.json() if response.content else None

async def init_db() -> None:
    try:
        await request("GET", "commodities", params={"select": "id", "limit": "1"})
        logger.info("Supabase Data API connected")
    except Exception as exc:
        logger.warning("Supabase health check failed: %s", exc)

async def get_or_create_user(phone: str) -> Dict[str, Any]:
    rows = await request("GET", "users", params={"select": "*", "phone_number": f"eq.{quote(phone, safe='')}" , "limit": "1"})
    if rows:
        return rows[0]
    rows = await request("POST", "users", payload={"phone_number": phone, "user_type": "farmer", "verification_status": "pending"})
    return rows[0]

async def get_user_by_phone(phone: str) -> Optional[Dict[str, Any]]:
    rows = await request("GET", "users", params={"select": "*", "phone_number": f"eq.{quote(phone, safe='')}", "limit": "1"})
    return rows[0] if rows else None

async def save_conversation(user_id: str, wa_message_id: Optional[str], direction: str, msg_type: str, content: Dict[str, Any], language: str, ai_intent: Optional[str] = None):
    return await request("POST", "conversations", payload={"user_id": user_id, "wa_message_id": wa_message_id, "direction": direction, "message_type": msg_type, "content_text": content.get("text", ""), "detected_language": language, "ai_intent": ai_intent})

async def get_active_transactions(user_id: str) -> List[Dict[str, Any]]:
    return await request("GET", "transactions", params={"select": "*,commodities(name_en)", "or": f"seller_id.eq.{user_id},buyer_id.eq.{user_id}", "status": "not.in.(completed,cancelled,refunded)", "order": "created_at.desc"}) or []

async def get_bids_for_listing(listing_id: str) -> List[Dict[str, Any]]:
    return await request("GET", "bids", params={"select": "*,users!buyer_id(display_name)", "listing_id": f"eq.{listing_id}", "order": "created_at.desc"}) or []

# Compatibility exports for modules being migrated incrementally.
def get_pool():
    raise RuntimeError("PostgreSQL pool removed; use database.request")

async def supabase_request(method: str, table: str, **kwargs):
    return await request(method, table, **kwargs)

async def close_pool():
    return None

async def get_listing_by_id(listing_id: str):
    rows = await request("GET", "listings", params={"select": "*", "id": f"eq.{listing_id}", "limit": "1"})
    return rows[0] if rows else None

async def update_listing_status(listing_id: str, status: str) -> bool:
    rows = await request("PATCH", "listings", params={"id": f"eq.{listing_id}"}, payload={"status": status})
    return bool(rows)

async def insert(table: str, payload: Dict[str, Any]):
    rows = await request("POST", table, payload=payload)
    return rows[0] if rows else None

async def select(table: str, params: Dict[str, str]):
    return await request("GET", table, params=params) or []

async def update(table: str, params: Dict[str, str], payload: Dict[str, Any]):
    return await request("PATCH", table, params=params, payload=payload) or []

async def delete(table: str, params: Dict[str, str]):
    return await request("DELETE", table, params=params, prefer="return=minimal")


def is_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)


def get_supabase_config() -> Dict[str, str]:
    return {"url": SUPABASE_URL, "configured": str(is_configured())}


def get_pool_sync_error() -> str:
    return "Use Supabase PostgREST request helpers"


def db_available() -> bool:
    return is_configured()


def rest_url(table: str) -> str:
    return f"{SUPABASE_URL}/rest/v1/{table}"


def rest_headers() -> Dict[str, str]:
    return _headers()
