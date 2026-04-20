from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal, Optional

# ==========================================
# Phase 1: Perception (Observation)
# ==========================================

class GetBusinessStateInput(BaseModel):
    """Retrieves real-time snapshots of inventory health, profit margins, and active staff load."""
    scope: Literal["inventory", "finance", "ops"] = Field(
        ..., description="The scope of business state to retrieve."
    ) 

class ParseUnstructuredSignalInput(BaseModel):
    """Uses GLM to extract intent, dates, and prices from messy inputs."""
    raw_content: str = Field(..., description="The raw unstructured text.") 
    type: Literal["text", "ocr_result", "stt_transcript"] = Field(
        ..., description="The type of the unstructured input."
    ) 
    image_data_url: Optional[str] = Field(None, description="Data URL of the image (if type is ocr_result)")

class QueryMacroContextInput(BaseModel):
    """Fetches oil prices and currency trends to adjust weights."""
    indicators: List[Literal["oil_price", "usd_myr", "local_inflation"]] = Field(
        ..., description="List of macro indicators to query."
    ) 


# ==========================================
# Phase 2: Reasoning & Simulation (The Debate)
# ==========================================

class SimulateYieldScenarioInput(BaseModel):
    """A Sandboxed calculator for the P-Agent to estimate the profit impact."""
    item_id: str = Field(..., description="Target menu item ID.") 
    action: Literal["discount", "bundle"] = Field(..., description="Action to simulate.") 
    value: float = Field(..., description="Numerical value for the action (e.g., discount percentage).") 

class EvaluateSupplyChainOptionsInput(BaseModel):
    """Compares different suppliers based on unit_cost vs. reliability_score + logistics_surcharge. [cite: 37]"""
    item_id: str = Field(..., description="Target inventory item ID to evaluate.") 

class CheckOperationalCapacityInput(BaseModel):
    """Validates if the current staff_roster can handle the projected surge."""
    projected_order_surge: float = Field(..., description="Estimated increase in order volume.") 
    complexity_factor: int = Field(..., ge=1, le=5, description="Complexity of the new menu/campaign (1-5).") 


# ==========================================
# Phase 3: Execution (Action)
# ==========================================

class ActionPayload(BaseModel):
    target_id: str 
    new_value: Any 

class ExecuteOperationalActionInput(BaseModel):
    """The primary write-tool for UPDATE_MENU, CREATE_PURCHASE_ORDER, or INVENTORY_CORRECTION."""
    action_type: Literal["UPDATE_MENU", "CREATE_PO", "INVENTORY_ADJUST", "ALERT_KDS"]
    payload: ActionPayload 
    p_logic_summary: str = Field(..., description="Reasoning trace from P-Agent.") 
    r_logic_summary: str = Field(..., description="Reasoning trace from R-Agent.") 

class MarketingConfig(BaseModel):
    discount: float 
    audience: str 
    budget: float 

class FormulateMarketingStrategyInput(BaseModel):
    """Triggers targeted interventions."""
    strategy_type: Literal["VOUCHER", "FLASH_SALE", "AD_BOOST"] 
    config: MarketingConfig 
    goal: Literal["clear_stock", "maximize_margin"] 

class SendHumanNotificationInput(BaseModel):
    """Requests Approve/Reject for high-stakes decisions."""
    priority: Literal["high", "medium"] 
    message: str = Field(..., description="Explanation to the human manager.") 
    proposed_action_json: Dict[str, Any] = Field(..., description="The action awaiting approval.")
    channel: Optional[Literal["dashboard", "email", "whatsapp", "telegram"]] = Field(
        default="dashboard", description="Delivery channel for the notification."
    ) 


# ==========================================
# Phase 4: Evolution (Memory)
# ==========================================

class ActualOutcome(BaseModel):
    revenue: float 
    waste_reduced: float 

class GeneratePostMortemLearningInput(BaseModel):
    """Compares expected_yield vs. actual_yield and writes the Lesson."""
    event_id: str = Field(..., description="The ID of the decision/campaign being evaluated.") 
    actual_outcome: ActualOutcome

class FetchMacroNewsInput(BaseModel):
    """Fetches real-time macro news and festival context."""
    query: str = Field(..., description="Keywords for news search (e.g., 'seafood supply', 'upcoming festivals')")