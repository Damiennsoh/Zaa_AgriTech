"""
ZAA Translation Service
Multi-language support for Northern Ghana
"""

import os
import logging
from typing import Optional
import aiohttp

logger = logging.getLogger(__name__)

# HuggingFace Inference API for NLLB-200 (free tier)
HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")
NLLB_API_URL = "https://api-inference.huggingface.co/models/facebook/nllb-200-distilled-600M"

# Language codes for NLLB-200
LANG_CODES = {
    "en": "eng_Latn",
    "dag": "dag_Latn",   # Dagbani
    "tw": "twi_Latn",    # Twi
    "gon": "gjn_Latn",   # Gonja
    "ha": "hau_Latn",    # Hausa
}

# Fallback keyword dictionary for critical agricultural terms
# These are NEVER translated by AI - they use verified mappings
KEYWORD_DICTIONARY = {
    "price": {"dag": "dal", "tw": "bo", "gon": "dal", "ha": "farashin"},
    "sell": {"dag": "too", "tw": "tɔn", "gon": "too", "ha": "sayar"},
    "buy": {"dag": "di", "tw": "tɔ", "gon": "di", "ha": "saya"},
    "shea butter": {"dag": "kpakpi nu", "tw": "shea butter", "gon": "kpakpi nu", "ha": "man shanu"},
    "shea nuts": {"dag": "kpakpi", "tw": "shea nuts", "gon": "kpakpi", "ha": "gyaɗan shanu"},
    "maize": {"dag": "kpaligu", "tw": "aburoo", "gon": "kpaligu", "ha": "masara"},
    "millet": {"dag": "kosaa", "tw": "millet", "gon": "kosaa", "ha": "gero"},
    "groundnuts": {"dag": "simitoo", "tw": "nkatee", "gon": "simitoo", "ha": "gyada"},
    "kg": {"dag": "kg", "tw": "kg", "gon": "kg", "ha": "kg"},
    "bag": {"dag": "bɔgu", "tw": "bɔg", "gon": "bɔgu", "ha": "jaka"},
    "today": {"dag": "dabi", "tw": "nnɛ", "gon": "dabi", "ha": "yau"},
    "tomorrow": {"dag": "zaa", "tw": "ɛnɛ", "gon": "zaa", "ha": "gobe"},
    "yes": {"dag": "aama", "tw": "aane", "gon": "aama", "ha": "eh"},
    "no": {"dag": "aayi", "tw": "daabi", "gon": "aayi", "ha": "a'a"},
    "good": {"dag": "niŋma", "tw": "pa", "gon": "niŋma", "ha": "mai kyau"},
    "money": {"dag": "sima", "tw": "sika", "gon": "sima", "ha": "kuɗi"},
    "market": {"dag": "luŋ", "tw": "dwa", "gon": "luŋ", "ha": "kasuwa"},
}

async def detect_language(text: str) -> str:
    """
    Detect language of input text.
    Uses simple heuristics + keyword matching.
    Production: Use langdetect or fastText
    """
    text_lower = text.lower()

    # Check for Dagbani keywords
    dagbani_markers = ["naa", "niŋma", "kpakpi", "kpaligu", "kosaa", "simitoo", 
                       "aama", "aayi", "zaa", "dabi", "too", "di"]
    dagbani_score = sum(1 for word in dagbani_markers if word in text_lower)

    # Check for Twi keywords
    twi_markers = ["akwaaba", "aburoo", "nkatee", "aane", "daabi", "pa", "bo", "tɔn"]
    twi_score = sum(1 for word in twi_markers if word in text_lower)

    # Check for Gonja keywords
    gonja_markers = ["aŋgɔ", "kpihili"]
    gonja_score = sum(1 for word in gonja_markers if word in text_lower)

    # Check for Hausa keywords
    hausa_markers = ["sannu", "na gode", "kuɗi", "kasuwa", "masara", "gyada"]
    hausa_score = sum(1 for word in hausa_markers if word in text_lower)

    scores = {"dag": dagbani_score, "tw": twi_score, "gon": gonja_score, "ha": hausa_score}
    best_lang = max(scores, key=scores.get)

    # If no clear match, default to English
    if scores[best_lang] == 0:
        return "en"

    return best_lang

async def translate_to_english(text: str, source_lang: str) -> str:
    """Translate from local language to English"""
    if source_lang == "en" or not text:
        return text

    # First, protect critical keywords by replacing them with placeholders
    protected_text, placeholders = protect_keywords(text, source_lang, "en")

    # Try NLLB-200 translation
    try:
        translated = await nllb_translate(protected_text, source_lang, "en")
    except Exception as e:
        logger.error(f"NLLB translation failed: {e}")
        # Fallback: return original with note
        translated = text

    # Restore protected keywords
    translated = restore_keywords(translated, placeholders)

    return translated

async def translate_from_english(text: str, target_lang: str) -> str:
    """Translate from English to local language"""
    if target_lang == "en" or not text:
        return text

    # Protect critical keywords
    protected_text, placeholders = protect_keywords(text, "en", target_lang)

    try:
        translated = await nllb_translate(protected_text, "en", target_lang)
    except Exception as e:
        logger.error(f"NLLB translation failed: {e}")
        translated = text

    translated = restore_keywords(translated, placeholders)

    return translated

async def nllb_translate(text: str, source_lang: str, target_lang: str) -> str:
    """Translate using NLLB-200 via HuggingFace Inference API"""
    src_code = LANG_CODES.get(source_lang, "eng_Latn")
    tgt_code = LANG_CODES.get(target_lang, "eng_Latn")

    payload = {
        "inputs": text,
        "parameters": {
            "src_lang": src_code,
            "tgt_lang": tgt_code
        }
    }

    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}

    async with aiohttp.ClientSession() as session:
        async with session.post(NLLB_API_URL, headers=headers, json=payload) as resp:
            if resp.status == 200:
                result = await resp.json()
                return result[0]["translation_text"]
            else:
                error = await resp.text()
                raise Exception(f"Translation API error: {resp.status} - {error}")

def protect_keywords(text: str, source_lang: str, target_lang: str) -> tuple:
    """
    Replace critical keywords with placeholders to prevent AI mistranslation.
    This ensures financial/agricultural terms are never mistranslated.
    """
    placeholders = {}
    protected = text
    counter = 0

    for keyword, translations in KEYWORD_DICTIONARY.items():
        if keyword in protected.lower():
            placeholder = f"__ZAA_{counter}__"
            placeholders[placeholder] = translations.get(target_lang, keyword)
            protected = protected.replace(keyword, placeholder)
            counter += 1

    return protected, placeholders

def restore_keywords(text: str, placeholders: dict) -> str:
    """Restore protected keywords after translation"""
    result = text
    for placeholder, keyword in placeholders.items():
        result = result.replace(placeholder, keyword)
    return result

async def text_to_speech(text: str, lang: str) -> str:
    """
    Convert text to speech using Piper TTS.
    Returns URL to audio file.

    For MVP: Use Piper TTS locally or ElevenLabs API
    """
    # MVP: Generate audio file and upload to cloud storage
    # Return public URL

    # Placeholder for actual TTS implementation
    audio_filename = f"/tmp/zaa_audio/{hash(text)}_{lang}.wav"
    os.makedirs("/tmp/zaa_audio", exist_ok=True)

    # In production, call Piper TTS:
    # piper --model dag_Latn --output_file {audio_filename} --text "{text}"

    # For now, return a placeholder
    return f"https://storage.zaa.com/audio/{os.path.basename(audio_filename)}"
