"""
WhatsApp Webhook & Message Handlers
Handles all incoming messages from farmers and buyers via WhatsApp
"""

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import os
import json
import logging
from datetime import datetime

from services.ai_core import process_message, generate_response
from database import save_conversation, get_or_create_user, get_user_by_phone
from services.market_data import get_current_prices, get_price_history
from services.listing_service import create_listing, get_user_listings, get_listing_by_id
from services.bid_service import place_bid, get_bids_for_listing, accept_bid
from services.translation import detect_language, translate_to_english, translate_from_english, text_to_speech
from services.notification import send_text, send_voice, notify_seller_of_bid

router = APIRouter()
logger = logging.getLogger(__name__)

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "zaa_verify_token_2024")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")

# ============================================================
# WEBHOOK VERIFICATION (For Meta Dashboard)
# ============================================================

@router.get("/webhook")
async def verify_webhook(request: Request):
    """Meta verifies this endpoint during webhook setup"""
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        logger.info("✅ Webhook verified successfully")
        return int(challenge)
    raise HTTPException(status_code=403, detail="Verification failed")

# ============================================================
# INCOMING MESSAGE HANDLER
# ============================================================

@router.post("/webhook")
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    """Handle all incoming WhatsApp messages"""
    try:
        body = await request.json()

        # Extract message data
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return {"status": "no_messages"}

        message = messages[0]
        from_number = message.get("from")  # e.g., "233241234567"
        message_type = message.get("type")  # text, audio, image, location
        message_id = message.get("id")

        logger.info(f"📩 Received {message_type} from {from_number}")

        # Process in background so we respond quickly to Meta
        background_tasks.add_task(
            process_incoming_message,
            from_number,
            message_type,
            message,
            message_id
        )

        return {"status": "processing"}

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {"status": "error", "detail": str(e)}

async def process_incoming_message(phone: str, msg_type: str, message: dict, msg_id: str):
    """Main message processing pipeline"""
    try:
        # 1. Get or create user
        user = await get_or_create_user(phone)

        # 2. Extract content based on message type
        content = extract_content(message, msg_type)

        # 3. Detect language
        detected_lang = await detect_language(content.get("text", ""))
        if user.get("preferred_language") == "en":
            detected_lang = "en"

        # 4. Save conversation
        await save_conversation(user["id"], msg_id, "inbound", msg_type, content, detected_lang)

        # 5. Determine intent using AI
        intent_data = await process_message(content, detected_lang, user)
        intent = intent_data.get("intent")
        entities = intent_data.get("entities", {})

        # 6. Route to appropriate handler
        response = await route_intent(intent, entities, user, content, detected_lang)

        # 7. Translate response to user's language
        if detected_lang != "en":
            response_text = await translate_from_english(response["text"], detected_lang)
        else:
            response_text = response["text"]

        # 8. Send response (voice for farmers, text for buyers)
        if user.get("user_type") == "farmer" and detected_lang != "en":
            # Generate voice note
            audio_url = await text_to_speech(response_text, detected_lang)
            await send_voice(phone, audio_url)
        else:
            await send_text(phone, response_text)

        # 9. Save outbound conversation
        await save_conversation(user["id"], None, "outbound", "text", 
                                {"text": response_text}, detected_lang, 
                                ai_intent=intent)

    except Exception as e:
        logger.error(f"Error in message processing: {str(e)}")
        # Send friendly error message
        error_msg = "Sorry, I had trouble understanding. Please try again or say 'help'."
        await send_text(phone, error_msg)

def extract_content(message: dict, msg_type: str) -> dict:
    """Extract relevant content from WhatsApp message"""
    content = {"type": msg_type}

    if msg_type == "text":
        content["text"] = message.get("text", {}).get("body", "")

    elif msg_type == "audio":
        audio = message.get("audio", {})
        content["media_id"] = audio.get("id")
        content["mime_type"] = audio.get("mime_type")
        content["text"] = ""  # Will be populated after STT

    elif msg_type == "image":
        image = message.get("image", {})
        content["media_id"] = image.get("id")
        content["mime_type"] = image.get("mime_type")
        content["caption"] = image.get("caption", "")
        content["text"] = image.get("caption", "")

    elif msg_type == "location":
        loc = message.get("location", {})
        content["latitude"] = loc.get("latitude")
        content["longitude"] = loc.get("longitude")
        content["text"] = f"Location: {loc.get('latitude')}, {loc.get('longitude')}"

    elif msg_type == "interactive":
        interactive = message.get("interactive", {})
        if interactive.get("type") == "button_reply":
            content["text"] = interactive.get("button_reply", {}).get("title", "")
            content["button_id"] = interactive.get("button_reply", {}).get("id", "")
        elif interactive.get("type") == "list_reply":
            content["text"] = interactive.get("list_reply", {}).get("title", "")
            content["list_id"] = interactive.get("list_reply", {}).get("id", "")

    return content

# ============================================================
# INTENT ROUTING
# ============================================================

async def route_intent(intent: str, entities: dict, user: dict, content: dict, lang: str):
    """Route to the correct business logic based on AI-detected intent"""

    handlers = {
        "price_check": handle_price_check,
        "list_product": handle_list_product,
        "grade_photo": handle_grade_photo,
        "view_listings": handle_view_listings,
        "place_bid": handle_place_bid,
        "accept_bid": handle_accept_bid,
        "check_status": handle_check_status,
        "help": handle_help,
        "greeting": handle_greeting,
        "group_selling": handle_group_selling,
        "register": handle_registration,
        "unknown": handle_unknown
    }

    handler = handlers.get(intent, handle_unknown)
    return await handler(entities, user, content, lang)

# ============================================================
# INTENT HANDLERS
# ============================================================

async def handle_price_check(entities: dict, user: dict, content: dict, lang: str):
    """Get current market prices for a commodity"""
    commodity = entities.get("commodity", "shea butter")
    location = entities.get("location", user.get("location_district", "Tamale"))

    prices = await get_current_prices(commodity, location)

    if not prices:
        return {"text": f"I don't have current prices for {commodity} in {location} yet. Let me check with the market and get back to you within 24 hours."}

    text = f"📊 Today's prices for {commodity}:\n\n"
    for p in prices:
        text += f"• {p['market']}: ₵{p['price']}/{p['unit']} ({p['grade']} grade)\n"
    text += f"\n💡 Tip: Prices in Accra are typically 30-50% higher. Want me to help you sell directly to Accra buyers?"

    return {"text": text}

async def handle_list_product(entities: dict, user: dict, content: dict, lang: str):
    """Create a new listing from farmer's message"""
    commodity = entities.get("commodity")
    quantity = entities.get("quantity")
    unit = entities.get("unit", "kg")
    price = entities.get("price")

    if not commodity or not quantity:
        return {"text": "I'd love to help you sell your produce! Please tell me:\n1. What are you selling? (e.g., shea butter, maize)\n2. How much do you have? (e.g., 50kg)\n3. What price are you hoping for? (optional)"}

    # Create listing
    listing = await create_listing(
        seller_id=user["id"],
        commodity_name=commodity,
        quantity=quantity,
        unit=unit,
        asking_price=price,
        location_district=user.get("location_district"),
        location_village=user.get("location_village")
    )

    text = f"✅ Great! I've listed your {quantity}{unit} of {commodity}.\n\n"
    text += f"Listing ID: #{listing['id'][:8]}\n"
    text += f"Status: Active\n"
    text += f"Expiry: 14 days\n\n"
    text += "📸 Send me a photo of your produce and I'll grade the quality to help you get the best price!\n\n"
    text += "Buyers will see your listing and place bids. I'll notify you when someone is interested."

    return {"text": text}

async def handle_grade_photo(entities: dict, user: dict, content: dict, lang: str):
    """Grade produce quality from photo"""
    if content.get("type") != "image":
        return {"text": "Please send me a clear photo of your produce and I'll grade the quality for you!"}

    # This calls the AI vision service
    from services.ai_vision import grade_produce_image

    media_id = content.get("media_id")
    caption = content.get("caption", "")

    # Download image from WhatsApp
    image_path = await download_whatsapp_media(media_id)

    # AI grading
    grading = await grade_produce_image(image_path, caption)

    grade = grading.get("grade", "C")
    confidence = grading.get("confidence", 0.0)
    attributes = grading.get("attributes", {})
    estimated_value = grading.get("estimated_value", 0)
    market_comparison = grading.get("market_comparison", {})

    text = f"📸 AI Quality Grading Result:\n\n"
    text += f"Grade: {'⭐' * (4 if grade == 'A' else 3 if grade == 'B' else 2)} {grade}\n"
    text += f"Confidence: {int(confidence * 100)}%\n\n"

    if attributes:
        text += "Details:\n"
        for key, val in attributes.items():
            text += f"• {key.replace('_', ' ').title()}: {val}\n"

    text += f"\n💰 Estimated Fair Value: ₵{estimated_value}/kg\n"
    text += f"Local market average: ₵{market_comparison.get('local_avg', 'N/A')}\n"
    text += f"Export market potential: ₵{market_comparison.get('export_avg', 'N/A')}\n\n"

    if grade == "A":
        text += "🌟 Excellent quality! You can command premium prices. Would you like me to list this for export buyers?"
    elif grade == "B":
        text += "👍 Good quality. This meets standard market requirements."
    else:
        text += "⚠️ This grade may get lower prices. Tips to improve: [storage/drying advice based on commodity]"

    return {"text": text}

async def handle_view_listings(entities: dict, user: dict, content: dict, lang: str):
    """Show farmer their active listings"""
    listings = await get_user_listings(user["id"])

    if not listings:
        return {"text": "You don't have any active listings. Send me a message like 'I want to sell 50kg shea butter' to create one!"}

    text = "📋 Your Active Listings:\n\n"
    for i, listing in enumerate(listings[:5], 1):
        text += f"{i}. #{listing['id'][:8]} - {listing['quantity']}{listing['unit']} {listing['commodity']}\n"
        text += f"   Status: {listing['status']} | Bids: {listing.get('bid_count', 0)}\n"

    return {"text": text}

async def handle_place_bid(entities: dict, user: dict, content: dict, lang: str):
    """Buyer places a bid on a listing"""
    if user.get("user_type") != "buyer":
        return {"text": "You need a buyer account to place bids. Reply 'register buyer' to get started."}

    listing_id = entities.get("listing_id")
    bid_amount = entities.get("amount")

    if not listing_id or not bid_amount:
        return {"text": "To place a bid, tell me:\n1. The listing ID (e.g., #A3B7C9D2)\n2. Your offer price per kg"}

    bid = await place_bid(
        buyer_id=user["id"],
        listing_id=listing_id,
        bid_price=bid_amount
    )

    # Notify seller
    await notify_seller_of_bid(bid)

    return {"text": f"✅ Your bid of ₵{bid_amount}/kg has been placed! The seller has been notified. You'll hear back within 24 hours."}

async def handle_accept_bid(entities: dict, user: dict, content: dict, lang: str):
    """Farmer accepts a bid"""
    bid_id = entities.get("bid_id")

    if not bid_id:
        return {"text": "Please tell me which bid you want to accept. Say something like 'Accept bid #B2C4D6'"}

    result = await accept_bid(bid_id, user["id"])

    if result.get("success"):
        text = f"🎉 Deal confirmed!\n\n"
        text += f"Buyer: {result['buyer_name']}\n"
        text += f"Price: ₵{result['price']}/kg\n"
        text += f"Total: ₵{result['total']}\n\n"
        text += "💰 The buyer has been asked to deposit 50% into escrow. I'll notify you when the payment is received.\n\n"
        text += "📦 Delivery: Please prepare your produce. The buyer will arrange pickup or you can deliver to [agreed location]."
        return {"text": text}
    else:
        return {"text": f"Sorry, I couldn't accept that bid: {result.get('error', 'Unknown error')}"}

async def handle_check_status(entities: dict, user: dict, content: dict, lang: str):
    """Check transaction or listing status"""
    # Check for active transactions
    from database import get_active_transactions
    transactions = await get_active_transactions(user["id"])

    if transactions:
        text = "📦 Your Active Transactions:\n\n"
        for t in transactions:
            text += f"• #{t['id'][:8]}: {t['commodity']} - {t['status']}\n"
            text += f"  Value: ₵{t['total_value']} | Escrow: {t['escrow_status']}\n"
        return {"text": text}

    return {"text": "You don't have any active transactions right now. Your listings are still active and waiting for buyers!"}

async def handle_help(entities: dict, user: dict, content: dict, lang: str):
    """Show help menu"""
    text = "🌾 Welcome to ZAA! Here is what I can do:\n\n"
    text += "1️⃣ *Check prices* - Send: 'What is the price of shea butter?'\n"
    text += "2️⃣ *Sell produce* - Send: 'I want to sell 50kg maize'\n"
    text += "3️⃣ *Grade quality* - Send a photo of your produce\n"
    text += "4️⃣ *View listings* - Send: 'Show my listings'\n"
    text += "5️⃣ *Check status* - Send: 'What is my status?'\n"
    text += "6️⃣ *Group selling* - Send: 'Group selling for shea'\n\n"
    text += "💡 I understand Dagbani, Twi, Gonja, and English. You can send voice notes too!"

    return {"text": text}

async def handle_greeting(entities: dict, user: dict, content: dict, lang: str):
    """Handle greetings"""
    name = user.get("display_name", "friend")

    greetings = {
        "dag": f"Naa! {name}, ZAA nye niŋma. (Hello! {name}, tomorrow is sweet.) How can I help you today?",
        "tw": f"Akwaaba, {name}! Wo ho te sɛn? (Welcome, {name}! How are you?) What would you like to do today?",
        "gon": f"Aŋgɔ, {name}! How can ZAA help you today?",
        "en": f"Hello {name}! Welcome to ZAA — your voice-first marketplace. What can I do for you today?"
    }

    return {"text": greetings.get(lang, greetings["en"])}

async def handle_group_selling(entities: dict, user: dict, content: dict, lang: str):
    """AI-coordinated group selling"""
    commodity = entities.get("commodity", "shea butter")

    from services.group_service import find_or_create_group
    group = await find_or_create_group(commodity, user)

    if group.get("is_new"):
        text = f"🤝 Group Selling Opportunity!\n\n"
        text += f"I've started a group for {commodity} sellers in {user.get('location_district', 'your area')}.\n"
        text += f"Current members: {group['member_count']}\n"
        text += f"Combined quantity: {group['total_quantity']}kg\n\n"
        text += "When we reach 500kg, we can negotiate bulk prices 25% higher than individual sales.\n\n"
        text += f"Want to join? Reply 'YES join group {group['id'][:6]}'"
    else:
        text = f"🤝 You're already in a {commodity} selling group!\n\n"
        text += f"Group size: {group['member_count']} farmers\n"
        text += f"Total: {group['total_quantity']}kg\n"
        text += f"Target: 500kg\n"
        text += f"Estimated premium: +25%\n\n"
        text += "I'll notify everyone when we reach the target!"

    return {"text": text}

async def handle_registration(entities: dict, user: dict, content: dict, lang: str):
    """Guide user through registration"""
    if user.get("verification_status") == "verified":
        return {"text": f"You're already registered, {user.get('display_name')}! Your account is active."}

    text = "📝 Let's get you set up on ZAA!\n\n"
    text += "I just need a few details:\n"
    text += "1. What is your name?\n"
    text += "2. What district are you in? (e.g., Tamale, Savelugu, Walewale)\n"
    text += "3. What do you mainly grow or produce?\n\n"
    text += "Reply with your answers and I'll complete your registration!"

    return {"text": text}

async def handle_unknown(entities: dict, user: dict, content: dict, lang: str):
    """Fallback for unknown intents"""
    text = "I'm not sure I understood that perfectly. Here is what I can help with:\n\n"
    text += "• Check market prices\n"
    text += "• List your produce for sale\n"
    text += "• Grade your produce from a photo\n"
    text += "• Join group selling\n\n"
    text += "Or just say 'help' for the full menu!"

    return {"text": text}

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

async def download_whatsapp_media(media_id: str) -> str:
    """Download media from WhatsApp servers"""
    import aiohttp

    url = f"https://graph.facebook.com/v18.0/{media_id}"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            data = await resp.json()
            media_url = data.get("url")

        async with session.get(media_url, headers=headers) as resp:
            content = await resp.read()

            # Save to temp file
            ext = data.get("mime_type", "").split("/")[-1]
            filename = f"/tmp/zaa_media/{media_id}.{ext}"
            os.makedirs("/tmp/zaa_media", exist_ok=True)

            with open(filename, "wb") as f:
                f.write(content)

            return filename
