"""
ZAA AI Core - Intent Classification & Entity Extraction
Uses Llama 3 via Groq API for fast, cheap inference
"""

import os
import json
import logging
from typing import Dict, Any
import aiohttp

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama3-8b-8192"  # Free tier: 20 requests/min

# System prompt for ZAA AI
ZAA_SYSTEM_PROMPT = """You are ZAA, an AI assistant for farmers and agricultural traders in Northern Ghana.
Your job is to understand what the user wants and extract key information.

IMPORTANT RULES:
1. Always respond in valid JSON format
2. Be respectful — many users are elderly, illiterate, or speaking in their second language
3. Understand agricultural terminology in Dagbani, Twi, Gonja, Hausa, and English
4. Be patient with incomplete or unclear messages

Respond ONLY with a JSON object in this format:
{
    "intent": "one_of_the_intents_below",
    "entities": {
        "commodity": "name_of_crop_or_product",
        "quantity": number_or_null,
        "unit": "kg_or_bag_or_other",
        "price": number_or_null,
        "location": "district_or_market_name",
        "listing_id": "id_if_mentioned",
        "bid_id": "id_if_mentioned"
    },
    "confidence": 0.0_to_1.0,
    "response_hint": "brief_suggestion_for_response"
}

VALID INTENTS:
- price_check: User wants to know current market prices
- list_product: User wants to sell something
- grade_photo: User sent a photo to grade
- view_listings: User wants to see their listings
- place_bid: Buyer wants to make an offer
- accept_bid: Seller wants to accept an offer
- check_status: User wants to know transaction status
- group_selling: User wants to join group selling
- register: User needs to complete registration
- help: User asked for help
- greeting: User said hello
- unknown: Cannot determine intent

COMMODITY MAPPING (understand these in all languages):
- shea nuts, shea butter, kpakpi
- maize, corn, kpaligu, aburoo
- millet, kosaa
- groundnuts, peanuts, simitoo, nkatee
- soybeans, soya
- rice, mui, emo
- cowpeas, bewa, aduwa
- yam, kpihili, bayere
- live chicken, kpini, akokonini
"""

async def process_message(content: Dict[str, Any], language: str, user: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process user message through LLM to determine intent and extract entities
    """
    user_text = content.get("text", "")
    message_type = content.get("type", "text")

    # Build context about the user
    user_context = f"""
User Info:
- Type: {user.get('user_type', 'unknown')}
- Name: {user.get('display_name', 'unknown')}
- Location: {user.get('location_district', 'unknown')}, {user.get('location_region', 'unknown')}
- Language: {language}
- Verification: {user.get('verification_status', 'pending')}
"""

    # Build the prompt
    prompt = f"""{user_context}

User Message:
Type: {message_type}
Content: {user_text}

Analyze this message and respond with JSON."""

    try:
        response = await call_groq_api(prompt)
        result = json.loads(response)

        # Validate and normalize
        intent = result.get("intent", "unknown")
        entities = result.get("entities", {})
        confidence = result.get("confidence", 0.5)

        # Normalize commodity names
        if entities.get("commodity"):
            entities["commodity"] = normalize_commodity(entities["commodity"])

        # Normalize units
        if entities.get("unit"):
            entities["unit"] = normalize_unit(entities["unit"])

        logger.info(f"AI Intent: {intent} (confidence: {confidence})")

        return {
            "intent": intent,
            "entities": entities,
            "confidence": confidence,
            "response_hint": result.get("response_hint", "")
        }

    except Exception as e:
        logger.error(f"AI processing error: {str(e)}")
        return {
            "intent": "unknown",
            "entities": {},
            "confidence": 0.0,
            "response_hint": "Ask for clarification"
        }

AI_GATEWAY_API_KEY = os.getenv("AI_GATEWAY_API_KEY", "")

async def call_groq_api(prompt: str) -> str:
    """Call LLM API via Vercel AI Gateway or Groq for fast LLM inference"""
    if AI_GATEWAY_API_KEY:
        url = "https://ai-gateway.vercel.sh/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {AI_GATEWAY_API_KEY}",
            "x-api-key": AI_GATEWAY_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "model": "google/gemini-2.5-flash",
            "messages": [

                {"role": "system", "content": ZAA_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 500,
            "response_format": {"type": "json_object"}
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data["choices"][0]["message"]["content"]
                    else:
                        logger.warning(f"Vercel AI Gateway returned status {resp.status}, trying Groq API")
        except Exception as e:
            logger.warning(f"Vercel AI Gateway call error: {e}")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": ZAA_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 500,
        "response_format": {"type": "json_object"}
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise Exception(f"Groq API error: {resp.status} - {error_text}")

            data = await resp.json()
            return data["choices"][0]["message"]["content"]


def normalize_commodity(name: str) -> str:
    """Normalize commodity names across languages"""
    name_lower = name.lower().strip()

    mapping = {
        # Shea
        "shea nuts": "shea nuts", "kpakpi": "shea nuts", "shea nut": "shea nuts",
        "shea butter": "shea butter", "kpakpi nu": "shea butter",
        # Maize
        "maize": "maize", "corn": "maize", "kpaligu": "maize", "aburoo": "maize",
        # Millet
        "millet": "millet", "kosaa": "millet",
        # Groundnuts
        "groundnuts": "groundnuts", "peanuts": "groundnuts", 
        "simitoo": "groundnuts", "nkatee": "groundnuts",
        # Soybeans
        "soybeans": "soybeans", "soya": "soybeans",
        # Rice
        "rice": "rice", "mui": "rice", "emo": "rice",
        # Cowpeas
        "cowpeas": "cowpeas", "bewa": "cowpeas", "aduwa": "cowpeas",
        # Yam
        "yam": "yam", "kpihili": "yam", "bayere": "yam",
        # Chicken
        "chicken": "live chicken", "live chicken": "live chicken",
        "kpini": "live chicken", "akokonini": "live chicken"
    }

    return mapping.get(name_lower, name_lower)

def normalize_unit(unit: str) -> str:
    """Normalize unit names"""
    unit_lower = unit.lower().strip()

    mapping = {
        "kg": "kg", "kilogram": "kg", "kilograms": "kg",
        "bag": "bag_85kg", "bags": "bag_85kg", "85kg bag": "bag_85kg",
        "50kg bag": "bag_50kg", "50kg": "bag_50kg",
        "ton": "ton", "tons": "ton", "tonne": "ton", "tonnes": "ton",
        "piece": "piece", "pieces": "piece",
        "litre": "litre", "litres": "litre", "liter": "litre", "liters": "litre"
    }

    return mapping.get(unit_lower, "kg")

async def generate_response(context: str, user_lang: str) -> str:
    """Generate a natural language response"""
    prompt = f"""You are ZAA, a friendly AI assistant for Ghanaian farmers.
Respond to this situation in a warm, helpful way. Keep it under 3 sentences if possible.

Context: {context}"""

    return await call_groq_api(prompt)
