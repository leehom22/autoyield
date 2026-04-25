from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Literal

# --- God Mode Schemas ---
class GodModePayload(BaseModel):
    inventory_target_id: Optional[str] = None
    # Old field
    inventory_multiplier: float = Field(1.0, ge=0.0, le=2.0)
    # New field
    inventory_qty_multiplier: float = Field(1.0, ge=0.0, le=10.0)
    inventory_cost_multiplier: float = Field(1.0, ge=0.0, le=10.0)
    currency_usd_myr: float = Field(1.0)
    oil_price_multiplier: float = Field(1.0)
    order_velocity_multiplier: float = Field(1.0, ge=0.1, le=10.0)

class GodModeVelocityPayload(BaseModel):
    order_velocity_multiplier: float = Field(..., ge=0.1, le=10.0)

# --- Agent Interaction Schemas ---
class ChatbotInstructionPayload(BaseModel):
    query: str
    session_id: str
    user_role: Literal["owner", "manager", "staff"]

class DocumentAssetPayload(BaseModel):
    file_url: HttpUrl
    document_type: Literal["invoice", "handwritten_docket", "other"]
    supplier_id_hint: Optional[str] = None