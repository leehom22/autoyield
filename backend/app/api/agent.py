from app.schemas.payloads import ChatbotInstructionPayload, DocumentAssetPayload
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from typing import Optional
import base64
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from typing import Optional
import base64
from langchain_core.messages import HumanMessage
from app.services.invoice_extractor import extract_invoice_data
from app.services.db_service import get_inventory_status
from app.core.config import settings
from app.engine.simulator import get_current_simulated_time
from app.graph.assistant_graph import get_graph

MAX_FILE_SIZE = 5 * 1024 * 1024   # Maximum 5MB file input

router = APIRouter()

# =========== Agent Interaction Endpoints ============

@router.post("/invoice")
async def upload_invoice(
    request: Request,
    file: UploadFile = File(...)
):
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large. Max {MAX_FILE_SIZE // (1024*1024)}MB")
    
    app = request.app
    graph = get_graph()
    
    # Read and Parse Invoice Image
    b64 = base64.b64encode(contents).decode()
    image_url = f"data:{file.content_type};base64,{b64}"
    print(f"Invoice received: {file.filename}, type={file.content_type}, size={len(contents)} bytes")
    # Retrieve data from OCR Extraction Service
    invoice_data = await extract_invoice_data(contents, file.content_type)
    
    # Check for missing fields
    missing = []
    if not invoice_data.get("supplier"):
        missing.append("supplier")
    for i, item in enumerate(invoice_data.get("items", [])):
        if not item.get("name"):
            missing.append(f"item[{i}].name")
        if item.get("quantity") is None:
            missing.append(f"item[{i}].quantity")
        if item.get("unit_price") is None:
            missing.append(f"item[{i}].unit_price")
    
    if missing:
        return {
            "status": "incomplete",
            "missing_fields": missing,
            "extracted_data": invoice_data
        }
    
    # Check for price spike compared to inventory cost
    inv_items = get_inventory_status()
    spike_detected = False
    spike_items = []
    for item in invoice_data["items"]:
        import re
        def norm(s: str) -> str:
            return re.sub(r"[^a-z0-9 ]", "", (s or "").lower()).strip()

        inv_item = next(
            (i for i in inv_items if norm(i["name"]) == norm(item["name"])),
            None
        )
        if inv_item and item["unit_price"] > inv_item["unit_cost"] * settings.PRICE_SPIKE_THRESHOLD:
            spike_detected = True
            spike_items.append(item["name"])
    
    if spike_detected:
        # Call P/R Agent Graph for debate
        # ** Connect to assistant.py
        trigger_prompt = f"""
        TRIGGER: INVOICE_PRICE_SPIKE
        SOURCE: upload_invoice
        SUPPLIER: {invoice_data.get("supplier")}
        SPIKE_ITEMS: {spike_items}
        INVOICE_DATA: {invoice_data}

        Task:
        Analyze the invoice price spike
        """
        print("⚠ Price spike detected, triggering debating agents")
        result = await graph.ainvoke({
            "messages": [HumanMessage(content=trigger_prompt)],
            "invoice_data": invoice_data,
            "trigger_signal": "INVOICE_PRICE_SPIKE",
            "should_persist_decision": True,
        })
        return {
            "status": "debate_triggered",
            "response": result.get("final_response", ""),
            "decision_saved": result.get("decision_saved", False),
        }
    else:
        # Store into DB
        from app.services.invoice_crud import execute_invoice_crud
        crud_result = await execute_invoice_crud(invoice_data)
        return {"status": "processed", "result": crud_result}










# # TODO: Design a unified endpoint for both text instruction and document asset ingestion
# # from langgraph_agent.graph import graph
# main_graph = get_main_graph()

# @router.post("/ingest")
# async def ingest_instruction(
#     background_tasks: BackgroundTasks,
#     text: Optional[str] = Form(None),
#     file: Optional[UploadFile] = File(None),
#     doc_type: str = Form("message"),
# ):
#     if not text and not file:
#         raise HTTPException(status_code=400, detail="Either text or file is required")
    
#     # 1. Parsing input
#     image_url = None
#     if file:
#         contents = await file.read()
#         b64 = base64.b64encode(contents).decode()
#         image_url = f"data:{file.content_type};base64,{b64}"
    
#     parsed = await parse_unstructured_signal(
#         raw_content=text or "",
#         input_type="ocr_result" if file else "text",
#         image_data_url=image_url
#     )
    
#     # 2. Construct main graph state
#     initial_state = {
#         "raw_content": text or "",
#         "input_type": "ocr_result" if file else "text",
#         "image_data_url": image_url,
#         "source": "user",
#         "parsed_intent": parsed.intent,
#         "parsed_entities": parsed.entities.dict(),
#         "parsed_autonomy": parsed.autonomy_level,
#         "is_complete": True,  # Based on parsed results
#         "missing_fields": [],
#         "target_agent": None,
#         "invoice_data": None,
#         "price_spike_detected": False,
#         "clerk_result": None,
#         "analysis_result": None,
#         "debate_context": None,
#         "debate_result": None,
#         "execution_result": None,
#         "final_response": "",
#         "messages": [],
#     }
    
#     # 3. 调用主 Graph
#     final_state = await main_graph.ainvoke(initial_state)
    
#     return {
#         "status": "completed",
#         "response": final_state.get("final_response", ""),
#         "intent": parsed.intent,
#         "autonomy_level": parsed.autonomy_level,
#     }








# Instruction or Chat Message Channel (Chatbot)
# @router.post("/chat")
# async def handle_instruction(payload: ChatbotInstructionPayload, background_tasks: BackgroundTasks):
    
#     # Risk control: Reject unauthorized requests and offload heavy inference to Background Tasks
#     if payload.user_role == "staff":
#         return {"reply": "Permission Denied. Staff cannot issue architectural constraints.", "status": "rejected"}
    
#     # Asynchronously trigger R-Agent to parse human instruction and save into Knowledge Base
#     # background_tasks.add_task(kernel.process_human_constraint, payload.query)
    
#     return {"reply": "Instruction acknowledged. Recalculating margin constraints...", "status": "accepted"}


# @router.post("/parse-document")
# async def handle_document(payload: DocumentAssetPayload):
    
#     # OCR Extraction: Feed file_url to GLM-4V (Vision), retrieve structured JSON data and store in Supdabase
#     # TODO: 调用 GLM-4V API，传入 payload.file_url
#     # mock_extracted_data = glm_service.parse_invoice(payload.file_url)
    
#     return {"status": "processing", "asset_type": payload.document_type}