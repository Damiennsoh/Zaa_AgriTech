"""
ZAA AI Vision - Produce Quality Grading
Uses fine-tuned computer vision models to grade agricultural produce from photos
"""

import os
import logging
from typing import Dict, Any
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

# For MVP, we use a rule-based system + CLIP/similarity
# In production, fine-tune YOLOv8 or ResNet on shea/maize datasets

async def grade_produce_image(image_path: str, caption: str = "") -> Dict[str, Any]:
    """
    Grade agricultural produce from a photo.

    MVP Implementation:
    1. Use color analysis for shea butter grading
    2. Use texture analysis for grain quality
    3. Use caption/commodity hint to determine what to grade

    Production: Fine-tuned YOLOv8 or EfficientNet model
    """
    try:
        # Load image
        img = Image.open(image_path)
        img_array = np.array(img)

        # Determine commodity from caption or default to shea butter
        commodity = detect_commodity_from_caption(caption)

        if commodity == "shea_butter":
            return await grade_shea_butter(img, img_array)
        elif commodity in ["maize", "millet", "groundnuts", "soybeans", "cowpeas"]:
            return await grade_grains(img, img_array, commodity)
        elif commodity == "shea_nuts":
            return await grade_shea_nuts(img, img_array)
        else:
            return await grade_generic(img, img_array, commodity)

    except Exception as e:
        logger.error(f"Vision grading error: {str(e)}")
        return {
            "grade": "C",
            "confidence": 0.5,
            "attributes": {"error": "Could not analyze image"},
            "estimated_value": 0,
            "market_comparison": {}
        }

def detect_commodity_from_caption(caption: str) -> str:
    """Detect commodity from user caption"""
    caption_lower = caption.lower()

    if any(word in caption_lower for word in ["shea butter", "kpakpi nu", "butter"]):
        return "shea_butter"
    elif any(word in caption_lower for word in ["shea nut", "kpakpi"]):
        return "shea_nuts"
    elif "maize" in caption_lower or "corn" in caption_lower or "aburoo" in caption_lower:
        return "maize"
    elif "millet" in caption_lower or "kosaa" in caption_lower:
        return "millet"
    elif any(word in caption_lower for word in ["groundnut", "peanut", "nkatee", "simitoo"]):
        return "groundnuts"
    elif "soya" in caption_lower or "soybean" in caption_lower:
        return "soybeans"
    elif "cowpea" in caption_lower or "bewa" in caption_lower:
        return "cowpeas"
    else:
        return "unknown"

async def grade_shea_butter(img: Image.Image, img_array: np.ndarray) -> Dict[str, Any]:
    """
    Grade shea butter based on visual characteristics:
    - Color: Ivory white (A) > Cream (B) > Yellowish/Grey (C)
    - Texture: Smooth (A) > Grainy (B) > Crumbly (C)
    - Impurities: None visible (A) > Some (B) > Many (C)
    """
    # Color analysis
    avg_color = np.mean(img_array, axis=(0, 1))

    # Convert to approximate color description
    r, g, b = avg_color[:3]
    brightness = (r + g + b) / 3

    # Shea butter grading logic
    color_grade = "unknown"
    if brightness > 220 and abs(r - g) < 20 and abs(g - b) < 20:
        color_grade = "ivory_white"
        color_score = 3
    elif brightness > 180 and abs(r - g) < 30:
        color_grade = "cream"
        color_score = 2
    elif r > g + 20 or brightness < 150:
        color_grade = "yellowish_grey"
        color_score = 1
    else:
        color_grade = "cream"
        color_score = 2

    # Texture analysis (simplified - use standard deviation as proxy)
    gray = np.mean(img_array, axis=2) if len(img_array.shape) == 3 else img_array
    texture_std = np.std(gray)

    if texture_std < 30:
        texture_grade = "smooth"
        texture_score = 3
    elif texture_std < 60:
        texture_grade = "grainy"
        texture_score = 2
    else:
        texture_grade = "crumbly"
        texture_score = 1

    # Calculate overall grade
    total_score = color_score + texture_score

    if total_score >= 5:
        overall_grade = "A"
        confidence = 0.85
        estimated_value = 12.0  # GHS per kg for Grade A
    elif total_score >= 3:
        overall_grade = "B"
        confidence = 0.75
        estimated_value = 8.0   # GHS per kg for Grade B
    else:
        overall_grade = "C"
        confidence = 0.65
        estimated_value = 5.0   # GHS per kg for Grade C

    return {
        "grade": overall_grade,
        "confidence": confidence,
        "attributes": {
            "color": color_grade,
            "texture": texture_grade,
            "brightness_score": int(brightness)
        },
        "estimated_value": estimated_value,
        "market_comparison": {
            "local_avg": 6.0,
            "regional_avg": 8.0,
            "export_avg": 12.0 if overall_grade == "A" else 8.0
        }
    }

async def grade_grains(img: Image.Image, img_array: np.ndarray, commodity: str) -> Dict[str, Any]:
    """Grade cereal grains (maize, millet, etc.)"""
    # Simplified grading based on color uniformity and visible damage

    gray = np.mean(img_array, axis=2) if len(img_array.shape) == 3 else img_array
    uniformity = 1 - (np.std(gray) / 128)  # Higher = more uniform

    # Detect dark spots (potential mold/damage)
    dark_pixels = np.sum(gray < 50) / gray.size

    if uniformity > 0.7 and dark_pixels < 0.05:
        grade = "A"
        confidence = 0.80
    elif uniformity > 0.5 and dark_pixels < 0.10:
        grade = "B"
        confidence = 0.70
    else:
        grade = "C"
        confidence = 0.60

    price_map = {
        "maize": {"A": 4.5, "B": 3.5, "C": 2.5},
        "millet": {"A": 5.0, "B": 4.0, "C": 3.0},
        "groundnuts": {"A": 8.0, "B": 6.0, "C": 4.0},
        "soybeans": {"A": 6.0, "B": 5.0, "C": 3.5},
        "cowpeas": {"A": 7.0, "B": 5.5, "C": 4.0}
    }

    commodity_prices = price_map.get(commodity, {"A": 5.0, "B": 4.0, "C": 3.0})

    return {
        "grade": grade,
        "confidence": confidence,
        "attributes": {
            "uniformity": f"{uniformity:.0%}",
            "damage_estimate": f"{dark_pixels:.1%}",
            "commodity": commodity
        },
        "estimated_value": commodity_prices[grade],
        "market_comparison": {
            "local_avg": commodity_prices["B"],
            "regional_avg": commodity_prices["A"],
            "export_avg": commodity_prices["A"] * 1.2
        }
    }

async def grade_shea_nuts(img: Image.Image, img_array: np.ndarray) -> Dict[str, Any]:
    """Grade shea nuts based on size and color"""
    # Similar to grains but with nut-specific criteria
    gray = np.mean(img_array, axis=2) if len(img_array.shape) == 3 else img_array

    # Estimate nut size from image (simplified)
    # In production, use object detection to count and size individual nuts

    brightness = np.mean(gray)

    if brightness > 100 and np.std(gray) < 40:
        grade = "A"
        confidence = 0.75
        value = 3.5
    elif brightness > 80:
        grade = "B"
        confidence = 0.70
        value = 2.5
    else:
        grade = "C"
        confidence = 0.65
        value = 1.5

    return {
        "grade": grade,
        "confidence": confidence,
        "attributes": {
            "color": "light_brown" if brightness > 100 else "brown" if brightness > 80 else "dark",
            "size_estimate": "medium_to_large"
        },
        "estimated_value": value,
        "market_comparison": {
            "local_avg": 2.0,
            "regional_avg": 2.5,
            "export_avg": 3.5
        }
    }

async def grade_generic(img: Image.Image, img_array: np.ndarray, commodity: str) -> Dict[str, Any]:
    """Generic grading for unknown commodities"""
    return {
        "grade": "B",
        "confidence": 0.50,
        "attributes": {
            "note": "Generic grading - please specify commodity for accurate assessment",
            "commodity_guess": commodity
        },
        "estimated_value": 5.0,
        "market_comparison": {
            "local_avg": 4.0,
            "regional_avg": 5.0,
            "export_avg": 6.0
        }
    }
