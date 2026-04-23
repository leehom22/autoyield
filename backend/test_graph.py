"""
test_graphs.py — Test runner for all 4 agent graphs

Usage:
    python test_graphs.py                    # runs all tests
    python test_graphs.py assistant          # runs only assistant graph tests
    python test_graphs.py ingestion          # runs only ingestion graph tests
    python test_graphs.py proactive          # runs only proactive graph tests
    python test_graphs.py forecast           # runs only forecast graph tests
"""

import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# ─────────────────────────────────────────────
# Colour helpers (no dependencies)
# ─────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
GRAY   = "\033[90m"
BLUE   = "\033[94m"

def header(text: str):
    print(f"\n{BOLD}{CYAN}{'═' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'═' * 60}{RESET}")

def subheader(text: str):
    print(f"\n{BOLD}{BLUE}  ▶ {text}{RESET}")

def ok(text: str):
    print(f"  {GREEN}✓ {text}{RESET}")

def warn(text: str):
    print(f"  {YELLOW}⚠ {text}{RESET}")

def fail(text: str):
    print(f"  {RED}✗ {text}{RESET}")

def dim(text: str):
    print(f"  {GRAY}{text}{RESET}")


# ─────────────────────────────────────────────
# Core stream runner
# ─────────────────────────────────────────────
async def stream_graph(graph, initial_state: dict, label: str):
    """
    Streams a graph run and pretty-prints each node's output.
    Returns the final state dict.
    """
    subheader(f"Query: {label}")
    final_state = {}

    try:
        async for event in graph.astream(initial_state, stream_mode="values"):
            final_state = event

            if "messages" not in event:
                continue

            last_msg = event["messages"][-1]
            msg_type = type(last_msg).__name__

            # Show state fields that changed (excluding messages)
            state_fields = {
                k: v for k, v in event.items()
                if k != "messages" and v not in (None, "", "none", "unknown", False, 0)
            }
            if state_fields:
                dim(f"  State: {state_fields}")

            # Format based on message type
            if isinstance(last_msg, HumanMessage):
                print(f"  {BOLD}[Human]{RESET}: {str(last_msg.content)[:200]}")

            elif isinstance(last_msg, AIMessage):
                # Show tool calls if present
                if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                    for tc in last_msg.tool_calls:
                        args_preview = str(tc.get("args", {}))[:120]
                        print(f"  {YELLOW}[Tool call]{RESET} → {BOLD}{tc['name']}{RESET}({args_preview})")
                else:
                    content = last_msg.content[:300] if last_msg.content else "(no content)"
                    print(f"  {GREEN}[AI]{RESET}: {content}{'...' if len(str(last_msg.content)) > 300 else ''}")

            elif isinstance(last_msg, ToolMessage):
                content = str(last_msg.content)[:200]
                print(f"  {BLUE}[Tool result]{RESET} ({last_msg.name}): {content}{'...' if len(str(last_msg.content)) > 200 else ''}")

    except Exception as e:
        fail(f"Graph execution error: {e}")
        raise

    return final_state


# ─────────────────────────────────────────────
# ASSISTANT GRAPH TESTS
# ─────────────────────────────────────────────
async def test_assistant_graph():
    header("AI Assistant Graph")

    from app.graph.assistant_graph import get_graph
    graph = get_graph()

    def make_state(query: str) -> dict:
        return {
            "messages": [HumanMessage(content=query)],
            "p_agent_position": "",
            "r_agent_position": "",
            "debate_rounds": 0,
            "consensus_reached": False,
            "requires_human_approval": False,
            "decision_type": "direct",
            "pending_handler": "none",
            "final_response": "",
        }

    # ── Test 1: Direct path — read-only query, should NOT trigger debate
    # ** Test with success
    state = await stream_graph(
        graph,
        make_state("What is the current inventory level for salmon?"),
        "Direct path — inventory check (no debate expected)"
    )
    decision_type = state.get("decision_type", "unknown")
    if decision_type == "direct":
        ok(f"Routed as 'direct' — correct")
    else:
        warn(f"Expected 'direct', got '{decision_type}'")

    # ── Test 2: Debate path — promotion keyword must trigger P vs R
    # ** Test with success
    state = await stream_graph(
        graph,
        make_state("I want to run a 20% discount promotion on all noodle dishes this Friday."),
        "Debate path — promotion discount (debate expected)"
    )
    decision_type = state.get("decision_type", "unknown")
    debate_rounds = state.get("debate_rounds", 0)
    if decision_type == "debate":
        ok(f"Routed as 'debate' — correct (rounds: {debate_rounds})")
    else:
        warn(f"Expected 'debate', got '{decision_type}'")

    # # ── Test 3: Debate path — supplier switch
    state = await stream_graph(
        graph,
        make_state("Switch our salmon supplier to OceanKing and place a bulk purchase order."),
        "Debate path — supplier switch + bulk purchase"
    )
    if state.get("decision_type") == "debate":
        ok(f"Supplier switch correctly triggered debate")
    else:
        warn(f"Supplier switch did not trigger debate — check keywords")

    # ── Test 4: High-stakes gate — price change >15% should hit send_human_notification
    # ** Test with success
    state = await stream_graph(
        graph,
        make_state("Increase the price of salmon rice by 25% starting today."),
        "High-stakes gate — price increase >15% (human notification expected)"
    )
    final = state.get("final_response", "")
    if "notification" in final.lower() or "approval" in final.lower():
        ok("High-stakes action correctly routed to human notification")
    else:
        warn("Expected human notification mention in final response — verify executor prompt")

    # ── Test 5: Forced consensus — debate must terminate within 3 rounds
    # ** Test with success
    state = await stream_graph(
        graph,
        make_state("Launch a flash sale with 30% off all menu items immediately."),
        "Forced consensus — debate must end within 3 rounds"
    )
    rounds = state.get("debate_rounds", 0)
    if rounds <= 3:
        ok(f"Debate terminated within limit (rounds: {rounds})")
    else:
        fail(f"Debate exceeded 3 rounds: {rounds} — forced concede may not be working")


# ─────────────────────────────────────────────
# INGESTION GRAPH TESTS
# ─────────────────────────────────────────────
async def test_ingestion_graph():
    header("Ingestion Graph")

    from app.graph.inventory_graph import get_ingestion_graph
    graph = get_ingestion_graph()

    def make_state(signal: str) -> dict:
        return {
            "messages": [HumanMessage(content=signal)],
            "price_spike_detected": False,
            "spike_item_id": "",
            "spike_pct": 0.0,
            "supplier_contacted": False,
            "action_logged": False,
        }

    # ── Test 1: Normal restock — price within range
    state = await stream_graph(
        graph,
        make_state(
            "Invoice from FreshMarine: 10kg salmon at RM87/kg. "
            "Current stored cost is RM85/kg. Delivery date: tomorrow."
        ),
        "Normal restock — price within 20% threshold"
    )
    spike = state.get("price_spike_detected", False)
    logged = state.get("action_logged", False)
    if not spike:
        ok("No spike detected — normal restock path taken")
    else:
        warn(f"Spike incorrectly detected at {state.get('spike_pct', 0)*100:.1f}% — threshold may be too sensitive")
    if logged:
        ok("Action logged to audit trail")
    else:
        warn("Action not logged — check log_decision_node")

    # ── Test 2: Price spike — >20% should trigger supplier evaluation
    state = await stream_graph(
        graph,
        make_state(
            "WhatsApp from supplier: salmon price increased to RM115/kg due to shortage. "
            "Current stored unit cost is RM85/kg. They can deliver 20kg tomorrow."
        ),
        "Price spike — 35% above stored cost (supplier eval + notify expected)"
    )
    spike = state.get("price_spike_detected", False)
    spike_pct = state.get("spike_pct", 0.0)
    contacted = state.get("supplier_contacted", False)
    if spike:
        ok(f"Spike detected: {spike_pct*100:.1f}%")
    else:
        warn(f"Spike not detected — spike_pct={spike_pct:.2f}, expected >0.20")
    if contacted:
        ok("Alternative supplier contacted")
    else:
        warn("Supplier contact not recorded in state")

    # ── Test 3: OCR invoice with blurry/messy format
    state = await stream_graph(
        graph,
        make_state(
            "OCR result from invoice x: 'Chikn brst 15kg @ RM13.50/kg "
            "dlvry 22/04 Supplier: GoodMeat Trading'. Current stored cost: RM12.00/kg."
        ),
        "Messy OCR invoice — chicken breast 12.5% above stored cost"
    )
    spike = state.get("price_spike_detected", False)
    if not spike:
        ok("Correctly identified as within threshold (12.5% < 20%)")
    else:
        warn(f"Spike detected at {state.get('spike_pct', 0)*100:.1f}% — check threshold logic")


# ─────────────────────────────────────────────
# PROACTIVE GRAPH TESTS
# ─────────────────────────────────────────────
async def test_proactive_graph():
    header("Proactive Graph")

    from app.graph.proactive_graph import get_proactive_graph
    graph = get_proactive_graph()

    def make_state(alert: str) -> dict:
        return {
            "messages": [HumanMessage(content=alert)],
            "anomaly_type": "unknown",
            "pending_handler": "none",
            "action_taken": False,
        }

    # ── Test 1: No anomaly — should route to END cleanly
    state = await stream_graph(
        graph,
        make_state("System check: all inventory levels normal. Kitchen load at 45%. No alerts."),
        "No anomaly — should terminate cleanly"
    )
    anomaly = state.get("anomaly_type", "unknown")
    action = state.get("action_taken", False)
    if anomaly == "none":
        ok("Classified as 'none' — no action taken, graph exited cleanly")
    else:
        warn(f"Expected 'none', got '{anomaly}'")
    if not action:
        ok("No unnecessary actions triggered")

    # ── Test 2: Stock critical — salmon < 1 day supply
    state = await stream_graph(
        graph,
        make_state(
            "ALERT: salmon stock at 0.5kg. At current order rate of 3kg/day, "
            "we have less than 4 hours of supply remaining. Expiry risk score: 0.95."
        ),
        "Stock critical — salmon depleted (flash sale + notify expected)"
    )
    anomaly = state.get("anomaly_type", "unknown")
    action = state.get("action_taken", False)
    if anomaly == "stock_critical":
        ok("Correctly classified as 'stock_critical'")
    else:
        warn(f"Expected 'stock_critical', got '{anomaly}'")
    if action:
        ok("Action taken (flash sale / notify / PO)")
    else:
        warn("action_taken is False — check stock_crisis_handler execution")

    # ── Test 3: Kitchen surge — order spike
    state = await stream_graph(
        graph,
        make_state(
            "ALERT: kitchen_load_percent is 92%. Pending orders jumped from 8 to 31 "
            "in the last 15 minutes. Active staff: 3. Rice stock running low."
        ),
        "Kitchen surge — load 92% (rewrite menu + KDS alert expected)"
    )
    anomaly = state.get("anomaly_type", "unknown")
    if anomaly == "kitchen_surge":
        ok("Correctly classified as 'kitchen_surge'")
    else:
        warn(f"Expected 'kitchen_surge', got '{anomaly}'")

    # ── Test 4: Tool loop — verify tool_node routes BACK to handler
    # (If tool_node routes to END, action_taken will be False despite the handler running)
    state = await stream_graph(
        graph,
        make_state(
            "CRITICAL: chicken inventory = 0.2kg. Daily consumption = 8kg. "
            "Kitchen load = 88%. Two large tables just seated."
        ),
        "Combined alert — verifies tool loop-back (both anomaly types present)"
    )
    if state.get("action_taken"):
        ok("Tool loop-back confirmed — handler received tool results and continued")
    else:
        warn("action_taken=False suggests tool_node may have routed to END prematurely")


# ─────────────────────────────────────────────
# FORECAST GRAPH TESTS
# ─────────────────────────────────────────────
async def test_forecast_graph():
    header("Forecast Graph")

    from app.graph.forecast_graph import get_forecast_graph
    graph = get_forecast_graph()

    def make_state(context: str = "") -> dict:
        return {
            "messages": [HumanMessage(content=context)] if context else [],
            "macro_risk_level": "unknown",
            "pending_handler": "none",
            "plan_generated": False,
        }

    # ── Test 1: Scheduled run with no context — standard forecast path
    state = await stream_graph(
        graph,
        make_state("Scheduled weekly forecast run. Today is Friday evening."),
        "Standard forecast — Friday evening scheduled run"
    )
    risk = state.get("macro_risk_level", "unknown")
    plan = state.get("plan_generated", False)
    if risk != "unknown":
        ok(f"Macro risk level resolved: '{risk}'")
    else:
        warn("macro_risk_level still 'unknown' — evaluate_risk_node may have failed to parse")
    if plan:
        ok("Plan generated successfully")
    else:
        warn("plan_generated=False — standard_forecast or crisis_optimizer did not complete")

    # ── Test 2: Crisis signal — macro risk should trigger crisis_optimizer
    state = await stream_graph(
        graph,
        make_state(
            "Scheduled forecast run. "
            "NOTE: query_macro_context returned overall_risk_level='high'. "
            "Oil prices spiked 18% this week. USD/MYR at 4.95."
        ),
        "Crisis forecast — macro risk='high' (crisis_optimizer expected)"
    )
    risk = state.get("macro_risk_level", "unknown")
    if risk in ("high", "elevated"):
        ok(f"Macro risk '{risk}' correctly triggered crisis_optimizer")
    else:
        warn(f"Expected 'high'/'elevated', got '{risk}' — crisis path may not have fired")

    # ── Test 3: Festival context — Hari Raya in 3 days
    state = await stream_graph(
        graph,
        make_state(
            "Scheduled forecast run. Hari Raya Aidilfitri is in 3 days. "
            "Expect -70% lunch covers and +80% pre-Raya dinner this week."
        ),
        "Festival forecast — Hari Raya in 3 days (demand adjustment expected)"
    )
    plan = state.get("plan_generated", False)
    if plan:
        ok("Plan generated with festival context")
    else:
        warn("Plan not generated — check read_signals_node festival handling")

    # ── Test 4: Tool loop verification — standard_forecast must receive tool results
    state = await stream_graph(
        graph,
        make_state("Scheduled forecast. Normal Friday. No macro events."),
        "Tool loop verification — standard_forecast must loop through tool_node"
    )
    if state.get("plan_generated"):
        ok("plan_generated=True confirms tool loop-back working in standard_forecast")
    else:
        warn("plan_generated=False — tool_node may be routing to evaluate_risk instead of standard_forecast")


# ─────────────────────────────────────────────
# Main runner
# ─────────────────────────────────────────────
GRAPH_MAP = {
    "assistant": test_assistant_graph,
    "ingestion":  test_ingestion_graph,
    "proactive":  test_proactive_graph,
    "forecast":   test_forecast_graph,
}

async def main():
    target = sys.argv[1].lower() if len(sys.argv) > 1 else "all"

    if target == "all":
        for name, fn in GRAPH_MAP.items():
            try:
                await fn()
            except Exception as e:
                fail(f"{name} graph tests crashed: {e}")
    elif target in GRAPH_MAP:
        await GRAPH_MAP[target]()
    else:
        print(f"{RED}Unknown target '{target}'. Choose from: all, {', '.join(GRAPH_MAP)}{RESET}")
        sys.exit(1)

    print(f"\n{BOLD}{GREEN}{'═' * 60}{RESET}")
    print(f"{BOLD}{GREEN}  All tests complete{RESET}")
    print(f"{BOLD}{GREEN}{'═' * 60}{RESET}\n")


if __name__ == "__main__":
    asyncio.run(main())