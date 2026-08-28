"""WhatsApp notification delivery and Supabase lookups."""
import os
import aiohttp
from database import request

WAPI = "https://graph.facebook.com/v18.0"
TOKEN = os.getenv("WHATSAPP_TOKEN", "")
PHONE_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")

async def send_text(to: str, body: str):
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{WAPI}/{PHONE_ID}/messages", headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}, json={"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": body}}) as response:
            return response.status == 200

async def send_voice(to: str, audio_url: str):
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{WAPI}/{PHONE_ID}/messages", headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}, json={"messaging_product": "whatsapp", "to": to, "type": "audio", "audio": {"link": audio_url}}) as response:
            return response.status == 200

async def notify_seller_of_bid(bid: dict):
    rows = await request("GET", "listings", params={"select": "id,users!seller_id(phone_number)", "id": f"eq.{bid['listing_id']}", "limit": "1"}) or []
    if rows and rows[0].get("users"):
        await send_text(rows[0]["users"]["phone_number"], f"New bid: GHS {bid['bid_price_per_unit']}/kg (Total: GHS {bid['total_bid_value']}). Reply ACCEPT {bid['id'][:6]} to accept.")
