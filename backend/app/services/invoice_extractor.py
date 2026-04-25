import json
from typing import Dict, Any, Optional, List
from app.core.glm_client import glm_client
import re

from pydantic import BaseModel, Field
from typing import Optional, List

class InvoiceItem(BaseModel):
    name: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None

class InvoiceData(BaseModel):
    supplier: Optional[str] = None
    items: List[InvoiceItem] = Field(default_factory=list)
    total_amount: Optional[float] = None
    date: Optional[str] = None
    currency: str = "MYR"
    
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

async def extract_invoice_data(image_bytes: bytes,mime_type: str,) -> Dict[str, Any]:
    response = ""

    try:
        response = await glm_client.vision_completion(
            image_bytes,
            mime_type,
            INVOICE_EXTRACT_PROMPT
        )
        
        cleaned = response.replace("```json", "").replace("```", "").strip()
        json_match = re.search(r"\{[\s\S]*\}", cleaned)
        if json_match:
            cleaned = json_match.group(0)

        data = json.loads(cleaned)
        validated = InvoiceData.model_validate(data)
        result = validated.model_dump()

    except Exception as e:
        print(f"Invoice extraction error: {e}")
        result = {
            "supplier": None,
            "items": [],
            "total_amount": None,
            "date": None,
            "currency": "MYR",
        }

    result["_raw_model_response"] = response[:1000] if response else None
    return result