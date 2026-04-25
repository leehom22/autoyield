import os
import re
from typing import Annotated, TypedDict, Literal
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from app.tools.mcp_tools_call import get_all_lc_tools
from app.graph.toolsCategory import PLANNING_TOOLS, EXECUTION_TOOLS, LEARNING_TOOLS
load_dotenv()

from app.core.supabase import supabase
from app.engine.simulator import get_current_simulated_time

# ─────────────────────────────────────────────
# Constants — tune these without touching graph logic
# ─────────────────────────────────────────────
MAX_DEBATE_ROUNDS      = 3    # R-Agent forced to concede after this many rounds
MAX_SUPERVISOR_RETRIES = 2    # Supervisor loops before falling back to executor
MAX_TOOL_CALLS_PER_NODE = 5   # Hard cap on tool-call loops per node visit
HIGH_STAKES_SPEND_RM   = 500  # Notify human if spend exceeds this
HIGH_STAKES_PRICE_PCT  = 0.15 # Notify human if price change exceeds this

# ─────────────────────────────────────────────
# LLM
# ─────────────────────────────────────────────
def get_glm() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.getenv("GLM_MODEL", "ilmu-glm-5.1"),
        api_key=os.getenv("GLM_API_KEY"),
        base_url=os.getenv("GLM_BASE_URL", "https://api.ilmu.ai/v1"),
        temperature=0.3,
    )


# ─────────────────────────────────────────────
# State
# ─────────────────────────────────────────────
class AgentState(TypedDict):
    messages:               Annotated[list[BaseMessage], add_messages]

    user_query:             str
    supervisor_summary:     str
    human_approval_sent:    bool

    # from upload_invoice trigger
    trigger_signal: str
    invoice_data: dict
    should_persist_decision: bool
    decision_saved: bool
    # ---------------------------
    
    debate_started: bool
    p_agent_position:       str
    r_agent_position:       str
    debate_rounds:          int
    consensus_reached:      bool

    decision_type:          Literal["debate", "direct", "unknown"]
    decision_domain:        Literal["pricing", "procurement", "ops", "clarification", "unknown"]
    pending_handler:        Literal["supervisor", "executor", "p_agent", "r_agent", "procurement_agent", "none"]
    supervisor_retries:     int
    node_tool_call_count:   int

    final_response:         str
    error_state:            str 
    api_response: dict

# ─────────────────────────────────────────────
# Prompts
# ─────────────────────────────────────────────
# marketing , finance
SUPERVISOR_PROMPT = """\
You are the AutoYield Restaurant AI Supervisor.

────────────────────────────────────────────
STEP 1 — Identify BOTH domain AND food category
────────────────────────────────────────────

First determine the DOMAIN of the request:

Valid domains:
- pricing
- procurement
- ops
- clarification

Examples:
- discount / promotion / flash sale / bundle / price change → pricing
- supplier switch / purchase order / bulk purchase / restock / vendor → procurement
- staffing / kitchen load / bottleneck / surge handling → ops
- missing supplier name / ambiguous item / missing quantity / unknown entity → clarification

Then determine FOOD CATEGORY (only if domain = pricing and the request targets a specific category):

Valid categories:
- dairy
- vegetables
- dry goods
- dessert
- meat
- beverages
- seafood

Examples:
- noodles/pasta/spaghetti/rice → dry goods
- fish/prawn/salmon → seafood
- chicken/beef/lamb → meat
- coffee/tea/juice → beverages
- cake/ice cream → dessert
- cheese/milk → dairy
- salad/mushroom → vegetables

────────────────────────────────────────────
STEP 2 — Fetch ONLY relevant context
────────────────────────────────────────────

IF domain = pricing:
1. Call get_business_state(scope='inventory')
2. Call get_business_state(scope='finance')

3. If the request targets a specific category:
   call get_all_menu_items(filter_category=<relevant category>)

4. If the request targets all menu items / blanket promotion / storewide flash sale:
   call get_menu_pricing_snapshot(include_unavailable=False)

IF domain = procurement:
1. Call get_business_state(scope='inventory')
2. Call get_business_state(scope='finance')
3. Call evaluate_supply_chain_options(item_id=<relevant inventory item>) IF item is identifiable

IF domain = ops:
1. Call get_business_state(scope='ops')
2. Optionally call get_business_state(scope='inventory')

IF domain = clarification:
- DO NOT call tools
- Ask the user for clarification

IMPORTANT:
- NEVER call get_all_menu_items(filter_category=None) during normal reasoning
- Use get_menu_pricing_snapshot for all-menu promotions
- NEVER send procurement requests into pricing analysis tools
- NEVER simulate discounts for supplier or purchase order requests

────────────────────────────────────────────
STEP 3 — Classify intent
────────────────────────────────────────────

End your response with EXACTLY these two lines:

DOMAIN: pricing|procurement|ops|clarification
INTENT: debate|direct

DEBATE triggers:
- Price changes (eg: Price increase, Price spike)
- Advice requested ("should we?", "what do you think?")
- Promotions, discounts, campaigns
- Supplier changes or bulk purchases
- Any cost > RM200 or price change > 10%

DIRECT triggers:
- Simple read-only queries
- Explicit execution commands with no ambiguity
- Minor inventory updates

If unsure:
→ default to:
INTENT: debate

────────────────────────────────────────────
CRITICAL RULES
────────────────────────────────────────────

- Always copy UUIDs exactly from tool results. Never truncate.
- For spending >RM500 or price change >15%, executor will require human approval.
- If supplier is NOT found in database → output DOMAIN: clarification
- DO NOT proceed with execution if key entities are missing
- DO NOT loop — if blocked, ask for clarification instead
"""

P_AGENT_PROMPT = """\
You are the P-Agent (Profit Maximization Agent).

Your ONLY job: argue for the most profitable action the business can take RIGHT NOW, including pricing, supplier, procurement, or purchasing decisions.

TOOL RULES:
- You may call simulate_yield_scenario ONLY if a key pricing number is missing.
- For procurement cases, do not call pricing tools. Use the supervisor summary and tool results only.- After receiving ONE relevant simulation result, you MUST finalize your recommendation.
- Do NOT call simulate_yield_scenario repeatedly for the same item/action.
- Do NOT test multiple discount values unless the user explicitly asked for comparison.
- If the supervisor summary already contains sufficient pricing numbers, DO NOT call any tool.

CONTEXT RULES:
- The supervisor summary and tool results are provided below.
- DO NOT call get_all_menu_items or get_business_state again.

FORMAT:
2-3 sentences. Include specific RM figures. End with one concrete recommendation.
"""

R_AGENT_PROMPT = """\
You are the R-Agent (Risk Mitigation Agent).

Your ONLY job: identify the single biggest risk in the P-Agent's proposal.
Use check_operational_capacity if the proposal involves a surge in orders.

CONTEXT RULES:
- If operational risk needs validation: CALL check_operational_capacity immediately.Do NOT say:
    - "let me validate"
    - "I should validate"
    - "I need more data"

    Either:
    - call tool
    -  provide final critique
    -  concede
- The supervisor summary is provided below. DO NOT call get_all_menu_items or get_business_state again.
- Only call check_operational_capacity, and only if the P-Agent proposes increased order volume.
- If you do not need a tool, DO NOT call one.

CONSENSUS RULE: If P-Agent's numbers are solid and the risk is low or mitigable,
start your response with exactly: CONSENSUS: [your agreed position]

FORMAT: 2-3 sentences. Name the risk. Propose one guardrail."""

EXECUTOR_PROMPT = """\
You are the AutoYield Executor. Execute the agreed decision. Do not re-analyze.

RULES:
1. Use ONLY write tools: execute_operational_action, formulate_marketing_strategy,
   send_human_notification, contact_supplier, save_to_kds.
2. NEVER call get_*, check_*, simulate_* — context gathering is done.
3. If the decision involves spending >RM500 OR price change >15%:
   → Use send_human_notification ONLY. Do not call any other tool.
4. After execution, write a short Execution Summary (2-3 sentences max).

The decision to execute is provided below."""

PROCUREMENT_AGENT_PROMPT = """\
You are the Procurement Agent.

Your ONLY job: handle supplier-switch and purchase-order decisions.

Use ONLY these tools when needed:
- evaluate_supply_chain_options
- contact_supplier
- send_human_notification

RULES:
- Do NOT call simulate_yield_scenario.
- If the requested supplier is not found in the supervisor summary, do NOT loop.
- If the supplier is missing or ambiguous, clearly ask for clarification or recommend the closest supplier already found.
- If bulk purchase likely exceeds RM500, recommend human approval.

FORMAT:
2-4 sentences. State the blocker or action clearly. End with one concrete next step.
"""

# ─────────────────────────────────────────────
# Safety helpers
# ─────────────────────────────────────────────
_DEBATE_KEYWORDS = {
    "price change", "price spike", "price increase","promotion", "supplier switch", "flash sale",
    "menu restructure", "bulk purchase", "discount", "voucher",
    "ad boost", "campaign", "increase price", "reduce price",
    "should we", "what do you think", "how can we", "recommend",
    "advise", "strategy"
}



def _keyword_needs_debate(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in _DEBATE_KEYWORDS)

def _classify_trigger_signal(trigger: str):
    if trigger == "INVOICE_PRICE_SPIKE":
        return "debate", "procurement"

    return "unknown", "unknown"

def _parse_intent(content: str) -> Literal["debate", "direct", "unknown"]:
    """Reads the INTENT: line from supervisor output. Falls back to keyword check."""
    for line in content.splitlines():
        stripped = line.strip().lower()
        if stripped.startswith("intent:"):
            val = stripped.split(":", 1)[1].strip()
            if "debate" in val:
                return "debate"
            if "direct" in val:
                return "direct"
    return "unknown"


def _check_high_stakes(text: str) -> bool:
    """
    Returns True if the text implies spend >RM500 or price change >15%.
    Checked BEFORE calling executor LLM so the LLM can't accidentally bypass it.
    """
    # Price % check: look for patterns like "25%", "30 percent", "increase by 20%"
    pct_matches = re.findall(r"(\d+(?:\.\d+)?)\s*%", text)
    for m in pct_matches:
        if float(m) > HIGH_STAKES_PRICE_PCT * 100:
            return True
    # Spend check: look for "RM 600", "RM600", "600 ringgit"
    rm_matches = re.findall(r"RM\s?(\d+(?:\.\d+)?)", text, re.IGNORECASE)
    for m in rm_matches:
        if float(m) > HIGH_STAKES_SPEND_RM:
            return True
    return False

def _parse_domain(content: str) -> Literal["pricing", "procurement", "ops", "clarification", "unknown"]:
    for line in content.splitlines():
        stripped = line.strip().lower()
        if stripped.startswith("domain:"):
            val = stripped.split(":", 1)[1].strip()
            if "pricing" in val:
                return "pricing"
            if "procurement" in val:
                return "procurement"
            if "ops" in val:
                return "ops"
            if "clarification" in val:
                return "clarification"
    return "unknown"


def _infer_domain_from_query(text: str) -> Literal["pricing", "procurement", "ops", "clarification", "unknown"]:
    lower = text.lower()

    if any(x in lower for x in [
        "supplier", "switch supplier", "vendor", "purchase order",
        "bulk purchase", "po", "restock", "contact supplier", "procure"
    ]):
        return "procurement"

    if any(x in lower for x in [
        "discount", "promotion", "bundle", "flash sale", "campaign",
        "price", "pricing", "voucher"
    ]):
        return "pricing"

    if any(x in lower for x in [
        "staff", "kitchen load", "capacity", "shift", "operations"
    ]):
        return "ops"

    return "unknown"

def _needs_clarification(summary: str) -> bool:
    lower = summary.lower()
    return (
        "no supplier named" in lower
        or "did you mean" in lower
        or "not in our system" in lower
        or "please confirm" in lower
    )

def _compress_menu_snapshot(tool_content: str, max_items: int = 8) -> str:
    text = str(tool_content)

    # crude truncation fallback
    if len(text) <= 800:
        return text

    return text[:800] + "... [menu snapshot truncated]"

def _extract_tool_summary(messages: list[BaseMessage], max_results: int = 3) -> str:
    """
    Pulls the most recent tool results from message history and returns
    a compressed, readable summary. Prevents raw JSON dumps from dominating
    agent context and causing hallucination/anchoring.
    """
    tool_msgs = [m for m in messages if isinstance(m, ToolMessage)]
    recent = tool_msgs[-max_results:] if len(tool_msgs) > max_results else tool_msgs
    if not recent:
        return "No tool results available yet."

    parts = []
    for tm in recent:
        content = str(tm.content)

        if tm.name in {"get_all_menu_items", "get_menu_pricing_snapshot"}:
            content = _compress_menu_snapshot(content)

        elif len(content) > 400:
            content = content[:400] + "... [truncated]"

        parts.append(f"[{tm.name}]: {content}")
    return "\n".join(parts)

def _safe_llm_call(llm, messages: list, node_name: str) -> AIMessage:
    """
    Wraps any LLM call. On failure, returns a graceful fallback AIMessage
    so the graph can still terminate instead of crashing.
    """
    try:
        return llm.invoke(messages)
    except Exception as e:
        error_msg = f"[{node_name}] LLM call failed: {type(e).__name__}: {str(e)[:200]}"
        print(f"⚠ {error_msg}")
        return AIMessage(content=f"SYSTEM ERROR: {error_msg}. Routing to safe termination.")

def build_api_response(state: AgentState) -> dict:
    return {
        "message": state.get("final_response")
            or state.get("r_agent_position")
            or state.get("p_agent_position")
            or state.get("supervisor_summary")
            or "No response generated.",

        "route": {
            "decision_type": state.get("decision_type", "unknown"),
            "decision_domain": state.get("decision_domain", "unknown"),
            "debate_started": state.get("debate_started", False),
            "consensus_reached": state.get("consensus_reached", False),
        },

        "agents": {
            "p_agent_position": state.get("p_agent_position"),
            "r_agent_position": state.get("r_agent_position"),
            "debate_rounds": state.get("debate_rounds", 0),
        },

        "execution": {
            "final_response": state.get("final_response"),
            "human_approval_sent": state.get("human_approval_sent", False),
            "decision_saved": state.get("decision_saved", False),
        },

        "error": state.get("error_state"),
    }
# ─────────────────────────────────────────────
# Debug printing helpers
# ─────────────────────────────────────────────
DEBUG_GRAPH = os.getenv("DEBUG_GRAPH", "true").lower() == "true"

RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
GRAY   = "\033[90m"
BLUE   = "\033[94m"

def subheader(text: str):
    if DEBUG_GRAPH:
        print(f"\n{BOLD}{BLUE}  ▶ {text}{RESET}")

def ok(text: str):
    if DEBUG_GRAPH:
        print(f"  {GREEN}✓ {text}{RESET}")

def warn(text: str):
    if DEBUG_GRAPH:
        print(f"  {YELLOW}⚠ {text}{RESET}")

def fail(text: str):
    if DEBUG_GRAPH:
        print(f"  {RED}✗ {text}{RESET}")

def dim(text: str):
    if DEBUG_GRAPH:
        print(f"  {GRAY}{text}{RESET}")


def debug_state(node: str, state: dict):
    if not DEBUG_GRAPH:
        return

    subheader(f"Node: {node}")

    fields = {
        "user_query": state.get("user_query"),
        "trigger_signal": state.get("trigger_signal"),
        "decision_type": state.get("decision_type"),
        "decision_domain": state.get("decision_domain"),
        "pending_handler": state.get("pending_handler"),
        "debate_rounds": state.get("debate_rounds"),
        "consensus_reached": state.get("consensus_reached"),
        "human_approval_sent": state.get("human_approval_sent"),
        "should_persist_decision": state.get("should_persist_decision"),
        "decision_saved": state.get("decision_saved"),
        "node_tool_call_count": state.get("node_tool_call_count"),
    }

    dim(f"State: {fields}")

    if state.get("messages"):
        last = state["messages"][-1]
        tool_calls = getattr(last, "tool_calls", None)

        if tool_calls:
            for tc in tool_calls:
                dim(f"Tool call → {tc.get('name')}({str(tc.get('args', {}))[:120]})")
        else:
            content = str(getattr(last, "content", ""))[:250]
            dim(f"Last message: {type(last).__name__}: {content}")
            
def _classify_chat_request(user_query: str):
    lower = user_query.lower()

    if any(x in lower for x in [
        "discount", "promotion", "campaign", "voucher",
        "price", "pricing", "flash sale", "bundle"
    ]):
        return "debate", "pricing"

    if any(x in lower for x in [
        "supplier", "vendor", "purchase order", "bulk purchase",
        "restock", "procure"
    ]):
        return "debate", "procurement"

    if any(x in lower for x in [
        "staff", "kitchen", "capacity", "shift", "queue", "bottleneck"
    ]):
        return "debate", "ops"

    return "direct", "unknown"
# ─────────────────────────────────────────────
# Nodes
# ─────────────────────────────────────────────

def supervisor_node(state: AgentState) -> AgentState:
    llm = get_glm().bind_tools(get_all_lc_tools())

    user_query = state.get("user_query", "")
    if not user_query:
        for m in reversed(state["messages"]):
            if isinstance(m, HumanMessage):
                user_query = m.content
                break

    response = _safe_llm_call(
        llm,
        [SystemMessage(content=SUPERVISOR_PROMPT)] + state["messages"],
        "supervisor"
    )

    trigger_intent, trigger_domain = _classify_trigger_signal(
        state.get("trigger_signal", "")
    )

    chat_intent, chat_domain = _classify_chat_request(user_query)
    
    intent: Literal["debate", "direct", "unknown"] = (
        trigger_intent if trigger_intent != "unknown"
        else chat_intent if chat_intent != "unknown"
        else state.get("decision_type", "unknown")
    )

    domain: Literal["pricing", "procurement", "ops", "clarification", "unknown"] = (
        trigger_domain if trigger_domain != "unknown"
        else chat_domain if chat_domain != "unknown"
        else state.get("decision_domain", "unknown")
    )

    if not getattr(response, "tool_calls", None):
        parsed_intent = _parse_intent(response.content)
        parsed_domain = _parse_domain(response.content)

        if intent == "unknown":
            intent = parsed_intent

        if domain == "unknown":
            domain = parsed_domain

        if intent == "unknown":
            intent = "debate" if _keyword_needs_debate(user_query) else "direct"

        if domain == "unknown":
            domain = _infer_domain_from_query(user_query)
            
    if _needs_clarification(response.content):
        domain = "clarification"
    
    retries = state.get("supervisor_retries", 0)
    
    new_state = {
        **state,
        "messages": [response],
        "user_query": user_query,
        "supervisor_summary": response.content if not getattr(response, "tool_calls", None) else state.get("supervisor_summary", ""),
        "decision_type": intent,
        "decision_domain": domain,
        "debate_rounds": 0,
        "consensus_reached": intent != "debate",
        "pending_handler": "supervisor",
        "supervisor_retries": retries + 1,
        "node_tool_call_count": state.get("node_tool_call_count", 0) + (1 if getattr(response, "tool_calls", None) else 0),
    }
    debug_state("supervisor:end", new_state)
    
    return new_state


def p_agent_node(state: AgentState) -> AgentState:
    # Procurement can still be debated.
    # P-Agent should argue for the most profitable procurement action.
    tool_msgs = [
        m for m in state["messages"]
        if isinstance(m, ToolMessage) and getattr(m, "name", "") == "simulate_yield_scenario"
    ]
    already_simulated = len(tool_msgs) > 0

    # tools = [] if already_simulated else [
    #     t for t in get_all_lc_tools() if t.name == "simulate_yield_scenario"
    # ]
    tools = []
    
    llm = get_glm().bind_tools(tools)

    tool_summary = _extract_tool_summary(state["messages"])
    r_position = state.get("r_agent_position") or "None yet — you go first."

    context = (
        f"USER REQUEST: {state.get('user_query', 'unknown')}\n\n"
        f"SUPERVISOR ANALYSIS:\n{state.get('supervisor_summary', 'Not available')}\n\n"
        f"LIVE DATA FROM TOOLS:\n{tool_summary}\n\n"
        f"R-AGENT LAST POSITION: {r_position}\n\n"
        + (
            "You already have a simulation result. Finalize now without any more tool calls."
            if already_simulated else
            "State your profit-maximizing recommendation with specific RM figures."
        )
    )

    response = _safe_llm_call(
        llm,
        [SystemMessage(content=P_AGENT_PROMPT), HumanMessage(content=context)],
        "p_agent"
    )

    is_tool_call = bool(getattr(response, "tool_calls", None))
    if is_tool_call:
        return {
            **state,
            "messages": [response],
            "pending_handler": "p_agent",
            "node_tool_call_count": state.get("node_tool_call_count", 0) + 1,
        }

    new_state = {
        **state,
        "messages": [response],
        "debate_started": True,
        "p_agent_position": response.content,
        "debate_rounds": state["debate_rounds"] + 1,
        "pending_handler": "none",
        "node_tool_call_count": 0,
    }
    
    debug_state("p_agent_node:end", new_state)
    
    return new_state


def r_agent_node(state: AgentState) -> AgentState:
    """
    Stress-tests P-Agent's proposal. Forced concede after MAX_DEBATE_ROUNDS.
    Amnesia fix: receives user_query + supervisor_summary directly.
    """
    tools = [t for t in get_all_lc_tools() if t.name == "check_operational_capacity"]
    llm = get_glm().bind_tools(tools)

    rounds = state.get("debate_rounds", 0)
    force_concede = rounds >= MAX_DEBATE_ROUNDS

    context = (
        f"USER REQUEST: {state.get('user_query', 'unknown')}\n\n"
        f"SUPERVISOR ANALYSIS:\n{state.get('supervisor_summary', 'Not available')}\n\n"
        f"P-AGENT PROPOSAL:\n{state.get('p_agent_position', 'None')}\n\n"
        + (
            f"ROUND {rounds}/{MAX_DEBATE_ROUNDS} — MAX ROUNDS REACHED. "
            "You MUST start your response with 'CONSENSUS: ' and accept a modified version of the proposal."
            if force_concede else
            f"ROUND {rounds}/{MAX_DEBATE_ROUNDS} — Identify the single biggest risk, "
            "OR concede with 'CONSENSUS: [position]' if risks are acceptable."
        )
    )

    response = _safe_llm_call(
        llm,
        [SystemMessage(content=R_AGENT_PROMPT), HumanMessage(content=context)],
        "r_agent"
    )
    is_tool_call = bool(getattr(response, "tool_calls", None))
    if is_tool_call:
        return {
            **state,
            "messages": [response],
            "pending_handler": "r_agent",
            "node_tool_call_count": state.get("node_tool_call_count", 0) + 1,
        }
    else:
        position = response.content
        # Detect consensus from response text OR force it
        consensus = position.strip().upper().startswith("CONSENSUS") or force_concede
        # Also catch system errors — don't loop forever on LLM failure
        if "SYSTEM ERROR" in position:
            consensus = True

        new_state = {
            **state,
            "r_agent_position":  position,
            "messages":          [AIMessage(content=f"[R-Agent]: {position}")],
            "consensus_reached": consensus,
            "node_tool_call_count": 0,
        }
        debug_state("r_agent_node:end", new_state)
        return new_state

def procurement_agent_node(state: AgentState) -> AgentState:
    tools = [
        t for t in get_all_lc_tools()
        if t.name in {"evaluate_supply_chain_options", "contact_supplier", "send_human_notification"}
    ]
    llm = get_glm().bind_tools(tools)

    context = (
        f"USER REQUEST: {state.get('user_query', '')}\n\n"
        f"SUPERVISOR ANALYSIS:\n{state.get('supervisor_summary', '')}\n\n"
        "Handle this as a procurement decision only."
    )

    response = _safe_llm_call(
        llm,
        [SystemMessage(content=PROCUREMENT_AGENT_PROMPT), HumanMessage(content=context)],
        "procurement_agent"
    )

    is_tool_call = bool(getattr(response, "tool_calls", None))
    if is_tool_call:
        return {
            **state,
            "messages": [response],
            "pending_handler": "procurement_agent",
            "node_tool_call_count": 1,
        }

    new_state = {
        **state,
        "messages": [response],
        "final_response": response.content,
        "pending_handler": "none",
        "node_tool_call_count": 0,
     }
    debug_state("procurement_agent_node:end", new_state)
    
    return new_state
    
def executor_node(state: AgentState) -> AgentState:
    """
    Executes the agreed decision.
    High-stakes guard runs BEFORE the LLM call — LLM cannot bypass it.
    Only write tools are bound — read tools are physically unavailable.
    """
    write_tools = [t for t in get_all_lc_tools() if t.name in EXECUTION_TOOLS]
    llm = get_glm().bind_tools(write_tools)

    # Build decision text for the high-stakes check
    if state.get("decision_type") == "debate":
        decision_text = (
            f"{state.get('p_agent_position', '')}\n"
            f"{state.get('r_agent_position', '')}"
        )
        instruction = (
            f"USER REQUEST: {state.get('user_query', '')}\n\n"
            f"CONSENSUS REACHED:\n"
            f"P-Agent: {state.get('p_agent_position', '')}\n"
            f"R-Agent: {state.get('r_agent_position', '')}\n\n"
            "Execute the agreed decision now."
        )
    else:
        decision_text = (
            f"{state.get('user_query', '')}\n"
            f"{state.get('supervisor_summary', '')}"
        )
        instruction = (
            f"USER REQUEST: {state.get('user_query', '')}\n\n"
            f"SUPERVISOR DECISION:\n{state.get('supervisor_summary', '')}\n\n"
            "Execute this decision now."
        )

    # HIGH-STAKES GUARD: check BEFORE LLM call — cannot be bypassed by LLM
    if _check_high_stakes(decision_text):

        # prevent duplicate notifications
        if state.get("human_approval_sent", False):
            return {
                **state,
                "final_response":
                    "✅ Human approval request already submitted to admin dashboard.",
                "node_tool_call_count": 0,
            }

        notif_tools = [
            t for t in get_all_lc_tools()
            if t.name == "send_human_notification"
        ]

        notif_llm = get_glm().bind_tools(notif_tools)
        
        notif_instruction = ( f"This action requires human approval (spend >RM{HIGH_STAKES_SPEND_RM} " f"or price change >{int(HIGH_STAKES_PRICE_PCT*100)}%).\n\n" f"Call send_human_notification with priority='high'.\n" f"Message: {instruction[:400]}\n" f"proposed_action_json: {{'decision': '{state.get('user_query', '')[:200]}'}}" )
        
        response = _safe_llm_call(
            notif_llm,
            [
                SystemMessage(content=EXECUTOR_PROMPT),
                HumanMessage(content=notif_instruction)
            ],
            "executor_high_stakes"
        )

        new_state = {
            **state,
            "messages": [response],
            "pending_handler": "executor",
            "human_approval_sent": True,   # IMPORTANT
            "node_tool_call_count": 1,
        }
        debug_state("executor_node:end", new_state)
        return new_state

    response = _safe_llm_call(
        llm,
        [SystemMessage(content=EXECUTOR_PROMPT), HumanMessage(content=instruction)],
        "executor"
    )

    return {
        **state,
        "messages":        [response],
        "pending_handler": "executor",
        "final_response":  response.content,
        "node_tool_call_count": 1 if getattr(response, "tool_calls", None) else 0,
    }

def save_decision_node(state: AgentState) -> AgentState:
    debug_state("save_decision:start", state)

    # Only P/R debate can save decision.
    if not state.get("debate_started", False):
        warn("save skipped: debate_started=False")
        return {
            **state,
            "decision_saved": False,
        }

    if state.get("decision_saved", False):
        warn("save skipped: already saved")
        return state

    action_taken = state.get("final_response", "")

    if not action_taken:
        if state.get("human_approval_sent", False):
            action_taken = "Human approval notification sent. Execution paused pending approval."
        else:
            action_taken = state.get("r_agent_position", "") or state.get("p_agent_position", "")

    payload = {
        "trigger_signal": state.get("trigger_signal", "UNKNOWN"),
        "timestamp": get_current_simulated_time().isoformat(),
        "p_agent_argument": state.get("p_agent_position", ""),
        "r_agent_argument": state.get("r_agent_position", ""),
        "resolution": (
            "Human approval required"
            if state.get("human_approval_sent", False)
            else "P/R debate completed"
        ),
        "action_taken": action_taken[:500],
    }

    ok("Saving P/R debate decision_logs record")
    dim(str(payload))

    try:
        supabase.table("decision_logs").insert(payload).execute()
    except Exception as e:
        fail(f"Failed to save decision log: {type(e).__name__}: {str(e)[:200]}")
        return {
            **state,
            "decision_saved": False,
            "error_state": f"save_decision failed: {str(e)[:200]}",
        }

    new_state = {
        **state,
        "decision_saved": True,
        "final_response": action_taken,
    }

    debug_state("save_decision:end", new_state)
    return new_state

def response_node(state: AgentState) -> AgentState:
    api_response = build_api_response(state)

    new_state = {
        **state,
        "api_response": api_response,
    }

    debug_state("response_node:end", new_state)
    return new_state

# ─────────────────────────────────────────────
# Routing — reads state only, never parses LLM output
# ─────────────────────────────────────────────

def route_after_supervisor(state: AgentState) -> str:
    last = state["messages"][-1]
    has_tool_calls = bool(getattr(last, "tool_calls", None))

    domain = state.get("decision_domain", "unknown")
    intent = state.get("decision_type", "unknown")
    tool_count = state.get("node_tool_call_count", 0)

    if has_tool_calls:
        if tool_count >= MAX_TOOL_CALLS_PER_NODE:
            warn("supervisor tool cap reached")

            if intent == "debate":
                return "p_agent"

            if domain == "procurement":
                return "procurement_agent"

            if intent == "direct":
                return "executor"

            # IMPORTANT: never return supervisor here
            return "response"

        return "tool_node"

    if domain == "clarification":
        return "response"

    if intent == "debate":
        return "p_agent"

    if domain == "procurement":
        return "procurement_agent"

    if intent == "direct":
        return "executor"

    return "response"

def route_after_p_agent(state: AgentState) -> str:
    # P-Agent should only argue once per debate round.
    # Once it has produced a position, always go to R-Agent.
    if state.get("p_agent_position"):
        return "r_agent"

    last = state["messages"][-1]

    if getattr(last, "tool_calls", None):
        if state.get("node_tool_call_count", 0) >= MAX_TOOL_CALLS_PER_NODE:
            return "r_agent"
        return "tool_node"

    return "r_agent"

def route_after_r_agent(state: AgentState) -> str:
    if state.get("consensus_reached") or state.get("debate_rounds", 0) >= MAX_DEBATE_ROUNDS:
        return "executor"
    return "p_agent"

def route_after_executor(state: AgentState) -> str:
    debug_state("route_after_executor", state)

    last = state["messages"][-1]

    if getattr(last, "tool_calls", None):
        if state.get("node_tool_call_count", 0) >= MAX_TOOL_CALLS_PER_NODE:
            if state.get("debate_started", False):
                warn("executor → save_decision | debate flow tool cap hit")
                return "save_decision"

            warn("executor → response | non-debate tool cap hit")
            return "response"

        ok("executor → tool_node | tool call detected")
        return "tool_node"

    if state.get("debate_started", False):
        ok("executor → save_decision | P/R debate completed")
        return "save_decision"

    dim("executor → response | non-debate flow")
    return "response"

def route_after_tools(state: AgentState) -> str:
    handler = state.get("pending_handler", "supervisor")

    if state.get("human_approval_sent", False):
        if state.get("debate_started", False):
            ok("tool_node → save_decision | human approval sent after P/R debate")
            return "save_decision"

        ok("tool_node → response | human approval sent in non-debate flow")
        return "response"

    if handler == "executor":
        return "executor"

    if handler == "r_agent":
        return "r_agent"
    
    if handler == "p_agent":
        if state.get("p_agent_position"):
            return "r_agent"
        return "p_agent"

    if handler == "procurement_agent":
        return "procurement_agent"

    return "supervisor"

# ─────────────────────────────────────────────
# Build graph
# ─────────────────────────────────────────────

def build_assistant_graph():
    builder = StateGraph(AgentState)

    builder.add_node("supervisor", supervisor_node)
    builder.add_node("p_agent",    p_agent_node)
    builder.add_node("r_agent",    r_agent_node)
    builder.add_node("executor",   executor_node)
    builder.add_node("tool_node",  ToolNode(get_all_lc_tools()))
    builder.add_node("procurement_agent", procurement_agent_node)
    builder.add_node("response", response_node)
    builder.add_node("save_decision", save_decision_node)
    
    builder.add_edge(START, "supervisor")

    builder.add_conditional_edges("supervisor", route_after_supervisor, {
        "tool_node": "tool_node",
        "p_agent": "p_agent",
        "procurement_agent": "procurement_agent",
        "executor": "executor",
        "supervisor": "supervisor",
        "response": "response",
        END: END,
    })

    builder.add_conditional_edges("p_agent", route_after_p_agent, {
        "tool_node": "tool_node",
        "r_agent":   "r_agent",
    })

    builder.add_conditional_edges("r_agent", route_after_r_agent, {
        "p_agent":  "p_agent",
        "executor": "executor",
    })

    builder.add_conditional_edges("executor", route_after_executor, {
        "tool_node": "tool_node",
        "save_decision": "save_decision",
        "response": "response",
        END: END,
    })

    builder.add_conditional_edges("tool_node", route_after_tools, {
        "supervisor": "supervisor",
        "executor": "executor",
        "p_agent": "p_agent",
        "r_agent": "r_agent",
        "procurement_agent": "procurement_agent",
        "save_decision": "save_decision",
        "response": "response",
        END: END,
    })
    
    builder.add_edge("save_decision", "response")
    builder.add_edge("response", END)

    return builder.compile()


_graph = None

def get_graph():
    global _graph
    if _graph is None:
        _graph = build_assistant_graph()
    return _graph