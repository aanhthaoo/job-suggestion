"""
Standalone runner for backend - no relative imports needed
Run with: python run.py
"""
import sys
import os
from pathlib import Path

# Add parent directory to path so we can import app modules
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

if __name__ == "__main__":
    import uvicorn
    from app.main import app
    
    print("=" * 60)
    print("🚀 Starting JobPortal Backend API")
    print("=" * 60)
    print(f"📍 Server: http://localhost:8000")
    print(f"📚 API Docs: http://localhost:8000/docs")
    print(f"🔧 Debug mode: ON")
    print("=" * 60)
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
