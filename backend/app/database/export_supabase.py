import os
import asyncio
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")

async def export_all():
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    tables = [
        "inventory", "menu_items", "suppliers", "staff_roster",
        "market_trends_history", "orders", "decision_logs",
        "notifications", "kds_queue", "festival_calendar",
        "knowledge_base", "procurement_logs", "inventory_pricing_history",
        "supplier_contact_logs", "marketing_campaigns"
    ]
    
    export = {}
    for table in tables:
        print(f"Exporting {table}...")
        try:
            res = supabase.table(table).select("*").execute()
            export[table] = res.data
        except Exception as e:
            print(f"  Error exporting {table}: {e}")
            export[table] = []
    
    with open("db_export.json", "w", encoding="utf-8") as f:
        json.dump(export, f, indent=2, default=str)
    
    print(f"\nExport complete: db_export.json ({len(export)} tables)")

if __name__ == "__main__":
    asyncio.run(export_all())