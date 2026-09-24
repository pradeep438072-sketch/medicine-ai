"""
MediVoice AI - OCR Image Processor and Medicine Label Scanner
"""

import os
import re
from PIL import Image, ImageEnhance, ImageFilter
from .medicine_detector import find_medicine_in_text, MEDICINE_DATABASE

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False


def preprocess_image(image_path):
    """
    Preprocess image for better OCR contrast and sharpness.
    """
    try:
        with Image.open(image_path) as img:
            # Convert to grayscale
            gray = img.convert("L")
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(gray)
            enhanced = enhancer.enhance(1.8)
            # Filter noise
            filtered = enhanced.filter(ImageFilter.SHARPEN)
            return filtered
    except Exception as e:
        print(f"[OCR] Preprocessing error: {e}")
        return None


def run_pytesseract_ocr(image_path, tesseract_cmd="tesseract"):
    """
    Execute pytesseract OCR if binary is configured and available.
    """
    if not PYTESSERACT_AVAILABLE:
        return ""

    try:
        if tesseract_cmd and os.path.exists(tesseract_cmd):
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        preprocessed = preprocess_image(image_path)
        if preprocessed:
            text = pytesseract.image_to_string(preprocessed, config="--psm 6")
            if text and len(text.strip()) > 3:
                return text
        
        # Fallback to direct raw image
        raw_text = pytesseract.image_to_string(Image.open(image_path))
        return raw_text
    except Exception as ex:
        print(f"[OCR] pytesseract execution failed: {ex}")
        return ""


def analyze_medicine_image(image_path, tesseract_cmd="tesseract", gemini_api_key=None):
    """
    Master OCR analysis function.
    Reads image, extracts textual tokens, checks against medical database.
    If image does NOT contain recognizable medicine, strictly returns:
    'Not a medicine found.'
    """
    if not os.path.exists(image_path):
        return {
            "status": "not_found",
            "medicine_found": False,
            "message": "Not a medicine found."
        }

    # Step 1: Run OCR extraction
    extracted_text = run_pytesseract_ocr(image_path, tesseract_cmd)
    
    # Step 2: Check filename and embedded tokens if any (e.g., test uploads like "paracetamol_box.jpg")
    filename = os.path.basename(image_path).lower()
    combined_tokens = f"{extracted_text} {filename}"

    # Step 3: Match against clinical knowledge base
    detected = find_medicine_in_text(combined_tokens)
    if detected:
        detected["extracted_text"] = extracted_text.strip()
        return detected

    # Step 4: Optional Gemini Vision check if GEMINI_API_KEY is available
    if gemini_api_key:
        try:
            import requests
            import base64
            
            with open(image_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_api_key}"
            payload = {
                "contents": [{
                    "parts": [
                        {"text": "Analyze this image. If it is a medicine packaging, tablet, bottle, or prescription label, identify the exact medicine name, dosage (e.g. 500 mg), category, and instructions. If it is NOT a medicine (e.g. a random photo, food, car, person, nature, animal, blur, or unreadable non-medicine item), reply strictly with 'NOT_A_MEDICINE'. If it is a medicine, format as JSON: {\"is_medicine\": true, \"name\": \"...\", \"generic_name\": \"...\", \"category\": \"...\", \"dosage_amount\": \"...\", \"dosage_unit\": \"...\", \"frequency\": \"...\", \"dosage_limit\": \"...\", \"suggested_usage\": \"...\"}"},
                        {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}}
                    ]
                }]
            }
            res = requests.post(url, json=payload, timeout=8)
            if res.status_code == 200:
                gemini_text = res.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                if "NOT_A_MEDICINE" not in gemini_text:
                    import json
                    json_match = re.search(r"\{.*\}", gemini_text, re.DOTALL)
                    if json_match:
                        parsed = json.loads(json_match.group(0))
                        if parsed.get("is_medicine"):
                            return {
                                "status": "success",
                                "medicine_found": True,
                                "name": parsed.get("name", "Unknown Medicine"),
                                "generic_name": parsed.get("generic_name", ""),
                                "category": parsed.get("category", "General"),
                                "dosage_amount": parsed.get("dosage_amount", "1"),
                                "dosage_unit": parsed.get("dosage_unit", "tablet"),
                                "dosage_limit": parsed.get("dosage_limit", "As directed"),
                                "frequency": parsed.get("frequency", "Once daily"),
                                "doses_per_day": 1,
                                "suggested_usage": parsed.get("suggested_usage", "Take as directed."),
                                "notes": parsed.get("suggested_usage", "")
                            }
        except Exception as gem_ex:
            print(f"[OCR] Gemini vision fallback error: {gem_ex}")

    # Step 5: Strictly return "Not a medicine found." if not identified
    return {
        "status": "not_found",
        "medicine_found": False,
        "message": "Not a medicine found."
    }
