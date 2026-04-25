import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from langchain_core.messages import HumanMessage
from app.core.supabase import supabase
from app.engine.simulator import get_current_simulated_time
from app.graph.forecast_graph import get_forecast_graph

scheduler = AsyncIOScheduler()

graph = get_forecast_graph()

async def weekly_forecast(graph):
    result = await graph.ainvoke({
        "messages": [HumanMessage(content="Weekly procurement report analysis required. Review last 7 days of purchases. Provide summary and recommendations.")]
    })
 
def start_scheduler(graph):
    scheduler.add_job(
        lambda: asyncio.run(weekly_forecast(graph)),
        'interval',
        weeks=1,
        id='weekly_forecast',
        replace_existing=True
    )
    scheduler.start()

def shutdown_scheduler():
    scheduler.shutdown()