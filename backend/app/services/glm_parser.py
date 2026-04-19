# app/services/glm_parser.py
import json
from typing import Dict, Any, Optional
from app.core.glm_client import glm_client
from app.schemas.tools_out import ParseUnstructuredSignalOutput, ExtractedEntities

MASTER_PARSER_PROMPT = """
You are the central "Perception Engine" for AutoYield (a restaurant operations AI).
Analyze the provided input (which may be a document image, a user message, an email, or an instruction).

YOUR GOALS:
1. Relevance Guard: If the input is completely irrelevant to restaurant ops (e.g., casual chat, politics), set "is_relevant": false and stop.
2. Intent Classification: If relevant, assign ONE intent from:
   [ "PRICE_UPDATE", "MENU_HIDE", "CREATE_PO", "INVENTORY_ADJUST", "WHAT_IF_ANALYSIS", "DATA_ANALYSIS", "FORECAST_REQUEST", "CLEAR_STOCK", "SUPPLY_DELAY", "PRICE_SPIKE_ALERT", "GENERAL_CRISIS" ]
3. Entity Extraction: Extract key metrics (item, price, date, supplier).
4. Sentiment & Autonomy: Judge urgency and required autonomy (L1=Direct Exec, L2=Analysis, L3=Urgent/Autonomous Action).

OUTPUT STRICT JSON ONLY:
{
    "is_relevant": true/false,
    "intent": "...",
    "autonomy_level": "L1/L2/L3",
    "sentiment": "urgent/neutral/negative",
    "entities": {
        "item": "string or null",
        "price": float or null,
        "date": "string or null",
        "supplier": "string or null"
    }
}
"""

async def parse_unstructured_signal(
    raw_content: str,
    input_type: str,
    image_data_url: Optional[str] = None
) -> ParseUnstructuredSignalOutput:
    
    # Parameters Validation
    if input_type == "ocr_result" and not image_data_url:
        raise ValueError("image_data_url is required when input_type is 'ocr_result'")

    try:
        if image_data_url:
            combined_prompt = f"{MASTER_PARSER_PROMPT}\n\nUser Notes: {raw_content}"
            resp_str = await glm_client.vision_completion(image_data_url, combined_prompt)
        else:
            combined_prompt = f"{MASTER_PARSER_PROMPT}\n\nInput Content: {raw_content}"
            resp_str = await glm_client.chat_completion(
                [{"role": "user", "content": combined_prompt}],
                response_format="json_object"
            )

        cleaned_resp = resp_str.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(cleaned_resp)

        # Default values for missing fields
        parsed.setdefault("intent", "UNKNOWN")
        parsed.setdefault("autonomy_level", "L2")
        parsed.setdefault("sentiment", "neutral")
        parsed.setdefault("entities", {})
        parsed["entities"].setdefault("item")
        parsed["entities"].setdefault("price")
        parsed["entities"].setdefault("date")
        parsed["entities"].setdefault("supplier")

    except Exception as e:
        print(f"⚠️ GLM Parser Error: {e}")
        return ParseUnstructuredSignalOutput(
            intent="SYSTEM_ERROR",
            entities=ExtractedEntities(),
            sentiment="negative",
            autonomy_level="L2"
        )

    if not parsed.get("is_relevant", True):
        return ParseUnstructuredSignalOutput(
            intent="IRRELEVANT",
            entities=ExtractedEntities(),
            sentiment="neutral",
            autonomy_level="L2"
        )

    return ParseUnstructuredSignalOutput(
        intent=parsed["intent"],
        entities=ExtractedEntities(
            item=parsed["entities"].get("item"),
            price=parsed["entities"].get("price"),
            date=parsed["entities"].get("date"),
            supplier=parsed["entities"].get("supplier")
        ),
        sentiment=parsed["sentiment"],
        autonomy_level=parsed["autonomy_level"]
    )