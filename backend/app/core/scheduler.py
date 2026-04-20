import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from langchain_core.messages import HumanMessage
from app.core.supabase import supabase

scheduler = BackgroundScheduler()

async def weekly_forecast(graph):
    result = await graph.ainvoke({
        "messages": [HumanMessage(content="Weekly procurement report analysis required. Review last 7 days of purchases. Provide summary and recommendations.")]
    })
    final_response = result.get("final_response", "")
    supabase.table("decision_logs").insert({
        "trigger_signal": "WEEKLY_FORECAST",
        "p_agent_argument": result.get("p_agent_position", ""),
        "r_agent_argument": result.get("r_agent_position", ""),
        "resolution": "Report generated",
        "action_taken": final_response[:500],
    }).execute()

def start_scheduler(graph):
    scheduler.add_job(
        lambda: asyncio.run(weekly_forecast(graph)),
        'interval',
        weeks=1,
        id='weekly_forecast',
        replace_existing=True
    )
    scheduler.start()