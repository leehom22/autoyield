import sys
from pathlib import Path
from app.graph.forecast_graph import build_forecast_graph
from app.graph.proactive_graph import build_proactive_graph
from app.graph.assistant_graph import get_graph, build_assistant_graph
from app.graph.inventory_graph import build_ingestion_graph

sys.path.insert(0, str(Path(__file__).parent))

forecast_graph = build_forecast_graph()
proactive_graph = build_proactive_graph()
inventory_graph = build_ingestion_graph()
assistant_graph = build_assistant_graph()

if __name__ == "__main__":
    import uvicorn
    import os

    # Create a folder for diagrams if it doesn't exist
    os.makedirs("diagrams", exist_ok=True)

    try:
        print("Generating visualizations for Agent Graphs...")
        # Save Forecast Graph
        with open("diagrams/forecast_graph.png", "wb") as f:
            f.write(forecast_graph.get_graph().draw_mermaid_png())
        
        # Save Proactive Graph
        with open("diagrams/proactive_graph.png", "wb") as f:
            f.write(proactive_graph.get_graph().draw_mermaid_png())
            
        with open("diagrams/assistant_graph.png", "wb") as f:
            f.write(assistant_graph.get_graph().draw_mermaid_png())
            
        with open("diagrams/inventory_graph.png", "wb") as f:
            f.write(inventory_graph.get_graph().draw_mermaid_png())
            
        print("✅ Graph visualizations saved to /diagrams folder.")
    except Exception as e:
        print(f"⚠️ Visualization skipped: {e}")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)