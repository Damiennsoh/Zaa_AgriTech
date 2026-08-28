"""
ZAA Notification Service
"""

import os, logging, aiohttp
from typing import Optional

logger = logging.getLogger(__name__)
WAPI = "https://graph.facebook.com/v18.0"
TOKEN = os.getenv("WHATSAPP_TOKEN", "")
PHONE_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")

async def send_text(to: str, body: str):
    url = f"{WAPI}/{PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": body}}
    async with aiohttp.ClientSession() as s:
        async with s.post(url, headers=headers, json=payload) as r:
            return r.status == 200

async def send_voice(to: str, audio_url: str):
    url = f"{WAPI}/{PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp", "to": to, "type": "audio", "audio": {"link": audio_url}}
    async with aiohttp.ClientSession() as s:
        async with s.post(url, headers=headers, json=payload) as r:
            return r.status == 200

async def notify_seller_of_bid(bid: dict):
    from database import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        listing = await conn.fetchrow("SELECT l.*, u.phone_number FROM listings l JOIN users u ON l.seller_id = u.id WHERE l.id = $1", bid["listing_id"])
        if listing:
            msg = f"New bid: GHS {bid['bid_price_per_unit']}/kg (Total: GHS {bid['total_bid_value']}). Reply ACCEPT {bid['id'][:6]} to accept."
            await send_text(listing["phone_number"], msg)
