# app/services/glm_parser.py
import json
from typing import Dict, Any, Optional, List
from app.core.glm_client import glm_client
from app.schemas.tools_out import ParseUnstructuredSignalOutput, ExtractedEntities

# ---------- Prompt ----------

GUARDRAIL_PROMPT = """
You are a content filter for a restaurant operations system. Determine whether the following input is relevant to restaurant business (inventory, supply chain, menu, orders, staff, marketing, finance, macro trends, etc.).
If completely irrelevant (e.g., casual chat, politics, entertainment), output only {"is_relevant": false}.
If relevant, output {"is_relevant": true, "cleaned_text": "cleaned text (remove profanity and irrelevant noise)"}.

Input: {raw_content}
"""

LONG_TEXT_SUMMARIZE_PROMPT = """
Please summarize the following long text into a concise version within 200 words. Retain key information such as items, prices, dates, suppliers, requested actions, etc.
Output only the summary text, no extra explanation.

Text: {raw_content}
"""

INTENT_CLASSIFICATION_PROMPT = """
You are a decision parser for a restaurant operations agent. Analyze the following user input and output JSON with these fields:
- intent: Choose the most appropriate from:
    ["PRICE_UPDATE", "MENU_HIDE", "CREATE_PO", "INVENTORY_ADJUST",           // L1: direct CRUD
     "WHAT_IF_ANALYSIS", "DATA_ANALYSIS", "FORECAST_REQUEST",                // L2: analysis only
     "CLEAR_STOCK", "SUPPLY_DELAY", "PRICE_SPIKE_ALERT", "RULE_CREATION", "GENERAL_CRISIS"]  // L3: autonomous action
- autonomy_level: "L1" (user explicitly requests direct data modification),
                 "L2" (user asks for analysis/prediction/advice, no execution),
                 "L3" (user requests autonomous decision + execution, or urgent/vague instruction)
- entities: include fields such as item, price, date, supplier, urgency_level (0-5), requested_action, new_value, etc. (as appropriate)
- sentiment: "urgent", "neutral", or "negative"

Rules:
- If user explicitly says "change X to Y", "hide X", "create purchase order X" → L1.
- If user asks "what if...", "analyze why...", "forecast..." → L2.
- If user says "you decide", "handle it", "must fix", "urgent", or describes a problem without specific action → L3.
- If emotional words or time pressure (tonight, immediately) appear, increase urgency_level.

User input: {user_input}
"""

OCR_IMAGE_PROMPT = """
You are a restaurant document parser. This image may be an invoice, handwritten order, delivery note, or meeting minutes photo.
Extract all text information and output JSON in the following format:
{
    "full_text": "All extracted text (preserve original order)",
    "structured": {
        "supplier": "supplier name (if any)",
        "items": [{"name": "item name", "quantity": number, "unit_price": number}],
        "total_amount": number,
        "date": "date",
        "remarks": "any other notes"
    }
}
If a field cannot be recognized, set it to null. Output only JSON.
"""

FUZZY_INSTRUCTION_PROMPT = """
The user input may be vague or incomplete. Infer the likely intention and output JSON:
{
    "normalized_intent": "standardized intent",
    "entities": { ... },
    "confidence": 0.0-1.0,
    "clarification_needed": true/false,
    "clarification_question": "question to ask user if needed"
}
Raw input: {raw_content}
"""

# ---------- Parsing ----------

async def parse_unstructured_signal(
    raw_content: str,
    input_type: str,   # "text", "ocr_result", "stt_transcript"
    image_data_url: Optional[str] = None
) -> ParseUnstructuredSignalOutput:
    """
    Guardrail → (OCR if image) → Long Text Summary → Intention → Output
    """
    # 1. Guardrail
    guard_result = await _guardrail(raw_content)
    if not guard_result["is_relevant"]:
        return ParseUnstructuredSignalOutput(
            intent="IRRELEVANT",
            entities=ExtractedEntities(),
            sentiment="neutral"
        )
    cleaned_text = guard_result.get("cleaned_text", raw_content)

    # 2. OCR if image
    if input_type == "ocr_result" and image_data_url:
        ocr_text = await _ocr_image(image_data_url)
        full_text = f"OCR提取: {ocr_text}\nUser Additional Notes:{cleaned_text}"
    else:
        full_text = cleaned_text

    # 3. Long Text Summary
    if len(full_text) > 1500:
        full_text = await _summarize_long_text(full_text)

    # 4. Intent Classification
    parsed = await _classify_intent(full_text)

    # 5. Fuzzyy instruction handling
    if parsed.get("confidence", 1.0) < 0.6:
        # Extra logic to handle: Claridication actions, autonomy level adjustment
        parsed["autonomy_level"] = "L2"
        parsed["entities"]["clarification_needed"] = True

    return ParseUnstructuredSignalOutput(
        intent=parsed["intent"],
        entities=ExtractedEntities(
            item=parsed["entities"].get("item"),
            price=parsed["entities"].get("price"),
            date=parsed["entities"].get("date"),
            # 扩展字段可放在 extra 中，但 schema 只有这三个；我们可以后续扩展
        ),
        sentiment=parsed["sentiment"],
        autonomy_level=parsed["autonomy_level"]
    )

# ---------- Helper ----------

async def _guardrail(text: str) -> Dict[str, Any]:
    prompt = GUARDRAIL_PROMPT.format(raw_content=text[:1000])
    resp = await glm_client.chat_completion([{"role": "user", "content": prompt}], response_format="json_object")
    return json.loads(resp)

async def _ocr_image(image_data_url: str) -> str:
    prompt = OCR_IMAGE_PROMPT
    resp = await glm_client.vision_completion(image_data_url, prompt)
    # Parsing JSON
    try:
        data = json.loads(resp)
        return data.get("full_text", resp)
    except:
        return resp

async def _summarize_long_text(text: str) -> str:
    prompt = LONG_TEXT_SUMMARIZE_PROMPT.format(raw_content=text)
    return await glm_client.chat_completion([{"role": "user", "content": prompt}])

async def _classify_intent(text: str) -> Dict[str, Any]:
    prompt = INTENT_CLASSIFICATION_PROMPT.format(user_input=text[:2000])
    resp = await glm_client.chat_completion([{"role": "user", "content": prompt}], response_format="json_object")
    return json.loads(resp)