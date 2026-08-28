"""
ZAA Payment Service - MTN MoMo Escrow
"""

import os, logging, aiohttp, base64, uuid
from typing import Dict, Any

logger = logging.getLogger(__name__)
MOMO_BASE = "https://sandbox.momodeveloper.mtn.com"
SUB_KEY = os.getenv("MOMO_SUBSCRIPTION_KEY", "")
API_USER = os.getenv("MOMO_API_USER", "")
API_KEY = os.getenv("MOMO_API_KEY", "")

async def get_token() -> str:
    creds = base64.b64encode(f"{API_USER}:{API_KEY}".encode()).decode()
    headers = {"Authorization": f"Basic {creds}", "Ocp-Apim-Subscription-Key": SUB_KEY}
    async with aiohttp.ClientSession() as s:
        async with s.post(f"{MOMO_BASE}/collection/token/", headers=headers) as r:
            return (await r.json()).get("access_token", "")

async def initiate_escrow_payment(tx_id: str, buyer_phone: str, amount: float) -> Dict[str, Any]:
    try:
        token = await get_token()
        ref = str(uuid.uuid4())
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Reference-Id": ref,
            "X-Target-Environment": "sandbox",
            "Ocp-Apim-Subscription-Key": SUB_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "amount": str(amount), "currency": "GHS", "externalId": tx_id,
            "payer": {"partyIdType": "MSISDN", "partyId": buyer_phone},
            "payerMessage": f"ZAA Escrow {tx_id[:8]}",
            "payeeNote": f"Escrow for {tx_id}"
        }
        async with aiohttp.ClientSession() as s:
            async with s.post(f"{MOMO_BASE}/collection/v1_0/requesttopay", headers=headers, json=payload) as r:
                return {"success": r.status in [200,202], "reference_id": ref, "status": "pending"}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def confirm_delivery(tx_id: str) -> Dict[str, Any]:
    """Confirm delivery and release escrow payment"""
    # Placeholder for actual delivery confirmation logic
    return {"success": True, "message": "Delivery confirmed, payment released"}

# Alias for marketplace router compatibility
async def request_payment(transaction_id: str, buyer_phone: str, amount: float) -> Dict[str, Any]:
    """Alias for initiate_escrow_payment for marketplace router compatibility"""
    return await initiate_escrow_payment(transaction_id, buyer_phone, amount)
