from app.schemas.payloads import ChatbotInstructionPayload, DocumentAssetPayload
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import base64

router = APIRouter()

# =========== Agent Interaction Endpoints ============


# TODO: Design a unified endpoint for both text instruction and document asset ingestion
# from langgraph_agent.graph import graph

@router.post("/ingest")
async def ingest_instruction(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    type: str = Form("text")
):
    if not text and not file:
        raise HTTPException(status_code=400, detail="Either text or file is required")
    
    # Input Normalization
    input_state = {
        "raw_content": text or "",
        "input_type": type,
        "image_data_url": None,
    }
    if file:
        contents = await file.read()
        b64 = base64.b64encode(contents).decode()
        input_state["image_data_url"] = f"data:{file.content_type};base64,{b64}"
        input_state["input_type"] = "ocr_result"
    
    # TODO: Wait for LangGraph Agent integration
    # final_state = await graph.ainvoke(input_state)
    # return {"parsed": final_state.get("parsed_result"), "action": final_state.get("action_result")}
    
    # Fallback response before integration
    return {"status": "pending", "message": "LangGraph agent not integrated yet", "input": input_state}









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