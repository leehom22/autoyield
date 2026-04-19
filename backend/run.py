# backend/run.py
import uvicorn
import sys
from pathlib import Path

# 将父目录（autoyield）添加到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)