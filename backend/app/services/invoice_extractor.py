import json
from typing import Dict, Any, Optional, List
from app.core.glm_client import glm_client
import re

INVOICE_EXTRACT_PROMPT = """
You are a restaurant invoice parser for AutoYield. Extract structured data from this invoice image.
Output ONLY valid JSON, no extra text.

Expected JSON format:
{
    "supplier": "supplier name (string, or null if not found)",
    "items": [
        {"name": "item name", "quantity": number, "unit_price": number}
    ],
    "total_amount": number,
    "date": "YYYY-MM-DD",
    "currency": "MYR"
}

Rules:
- quantity and unit_price are numbers (can be integers or floats)
- If an item is missing quantity or unit_price, set that field to null
- If multiple items, include all
- If supplier name not visible, use null
- total_amount can be sum of items or directly from invoice; if not available, use null
- date: try to find issue date; if not, use null
- currency: default "MYR" if not specified
"""

async def extract_invoice_data(image_data_url: str) -> Dict[str, Any]:
    """
    Call GLM-4V to extract structured data from an invoice image.
    
    Args:
        image_data_url: Data URL of the image (e.g., "data:image/png;base64,...")
    
    Returns:
        Dictionary with keys: supplier, items, total_amount, date, currency
    """
    try:
        response = await glm_client.vision_completion(image_data_url, INVOICE_EXTRACT_PROMPT)
        # Clean markdown code blocks if present (robust version)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            cleaned = json_match.group(0)
        else:
            cleaned = response.replace("```json", "").replace("```", "").strip()
        data = json.loads(cleaned)
    except Exception as e:
        print(f"Invoice extraction error: {e}")
        # Return empty structure on failure
        data = {
            "supplier": None,
            "items": [],
            "total_amount": None,
            "date": None,
            "currency": "MYR"
        }
    
    # Ensure all expected keys exist
    data.setdefault("supplier", None)
    data.setdefault("items", [])
    data.setdefault("total_amount", None)
    data.setdefault("date", None)
    data.setdefault("currency", "MYR")
    
    # Validate items structure
    for item in data["items"]:
        item.setdefault("name", None)
        item.setdefault("quantity", None)
        item.setdefault("unit_price", None)
    
    return data