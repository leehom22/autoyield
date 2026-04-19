from app.schemas.payloads import ChatbotInstructionPayload, DocumentAssetPayload
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import base64
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from typing import Optional
import base64
from app.graph.main_graph import get_main_graph
from app.services.glm_parser import parse_unstructured_signal

router = APIRouter()

# =========== Agent Interaction Endpoints ============

# TODO: Design a unified endpoint for both text instruction and document asset ingestion
# from langgraph_agent.graph import graph
main_graph = get_main_graph()

@router.post("/ingest")
async def ingest_instruction(
    background_tasks: BackgroundTasks,
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    doc_type: str = Form("message"),
):
    if not text and not file:
        raise HTTPException(status_code=400, detail="Either text or file is required")
    
    # 1. 先解析输入（调用 GLM 提取意图和实体）
    image_url = None
    if file:
        contents = await file.read()
        b64 = base64.b64encode(contents).decode()
        image_url = f"data:{file.content_type};base64,{b64}"
    
    parsed = await parse_unstructured_signal(
        raw_content=text or "",
        input_type="ocr_result" if file else "text",
        image_data_url=image_url
    )
    
    # 2. 构建主 Graph 状态
    initial_state = {
        "raw_content": text or "",
        "input_type": "ocr_result" if file else "text",
        "image_data_url": image_url,
        "source": "user",
        "parsed_intent": parsed.intent,
        "parsed_entities": parsed.entities.dict(),
        "parsed_autonomy": parsed.autonomy_level,
        "is_complete": True,  # 可根据 parsed 结果判断
        "missing_fields": [],
        "target_agent": None,
        "invoice_data": None,
        "price_spike_detected": False,
        "clerk_result": None,
        "analysis_result": None,
        "debate_context": None,
        "debate_result": None,
        "execution_result": None,
        "final_response": "",
        "messages": [],
    }
    
    # 3. 调用主 Graph
    final_state = await main_graph.ainvoke(initial_state)
    
    return {
        "status": "completed",
        "response": final_state.get("final_response", ""),
        "intent": parsed.intent,
        "autonomy_level": parsed.autonomy_level,
    }








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